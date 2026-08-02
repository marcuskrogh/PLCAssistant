"""Composable skid: mock process + cascade control + safety (one scan/step).

Pure ``step(dt)`` API with injectable clock/dt — no Home Assistant imports.
Tag names align with docs/wedge/02-io-hmi-contract.md.

Scan phase order (SWD-85): IN → SAFETY → CONTROL → OUT via ``ScanShell``.

Quality lives on each PV as ``TagQuality`` (docs/io/01-image-quality.md). There
are no separate ``*_BAD`` tags; LOS / safety use ``not is_good(quality)``.

Clear / restart policy
----------------------
After a trip, clearing the condition alone does **not** restart. Operator must
HMI_RESET (to clear the latch, MODE→STOP) then HMI_START. Reset never
auto-starts. Stop always forces CMD_SPEED = 0 / idle.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Optional

from plcassistant.control.scan import (
    PHASE_ORDER,
    ScanConfig,
    ScanDiagnostics,
    ScanPhase,
    ScanShell,
)
from plcassistant.io.quality import QualityStatus, ReasonCode, TagQuality, is_good
from plcassistant.surface.apply import ProjectLoader
from plcassistant.surface.builtin import register_builtins, wedge_softplc_project
from plcassistant.surface.io_wires import (
    SHELL_TAG_FLOW_SP_OVERRIDE,
    SHELL_TAG_LEVEL_SP,
    SHELL_TAG_RUNNING,
    TagPinWire,
    apply_io_wires_in,
    apply_io_wires_out,
    validate_tag_pin_wires,
    wedge_cascade_io_wires,
)
from plcassistant.surface.model import TemplateLibrary
from plcassistant.surface.runtime import BlockRuntime, DictContext
from plcassistant.surface.schema import project_from_dict
from plcassistant.wedge.control import CascadeConfig, CascadeController, CascadeOutputs
from plcassistant.wedge.process import MockProcess, ProcessConfig, ProcessPort, ProcessState
from plcassistant.wedge.quality import resolve_tag_quality
from plcassistant.wedge.safety import (
    Mode,
    SafetyConfig,
    SafetyLayer,
    SafetyState,
    TripCode,
)

_PV_TAGS = frozenset({"LT_TANK", "LT_RES", "FT_INLET"})


class OperatorCommand(str, Enum):
    """Maps to HMI_START / HMI_STOP / HMI_RESET."""

    NONE = "none"
    START = "start"  # HMI_START
    STOP = "stop"  # HMI_STOP
    RESET = "reset"  # HMI_RESET


class _UnsetType:
    __slots__ = ()

    def __repr__(self) -> str:
        return "<UNSET>"


_UNSET = _UnsetType()


@dataclass
class LimitConfig:
    """Single owner for HH / LL thresholds (process derate + safety trip)."""

    lim_level_hh: float = 0.36
    """LIM_LEVEL_HH (m) — tank high trip."""

    lim_res_ll: float = 0.05
    """LIM_RES_LL (m) — reservoir low trip and soft pump derate."""


@dataclass
class SkidConfig:
    process: ProcessConfig = field(default_factory=ProcessConfig)
    cascade: CascadeConfig = field(default_factory=CascadeConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    limits: LimitConfig = field(default_factory=LimitConfig)
    """Canonical lim_level_hh / lim_res_ll — synced into process + safety."""

    scan: ScanConfig = field(default_factory=ScanConfig)
    """Scan period / overrun threshold (default 0.1 s)."""

    sp_level: float = 0.20
    """SP_LEVEL default (m)."""


@dataclass(frozen=True)
class MeasurementView:
    """One-scan resolved PVs + per-tag quality (overrides / injectors applied)."""

    lt_tank: Optional[float]
    lt_res: Optional[float]
    ft_inlet: Optional[float]
    lt_tank_quality: TagQuality
    lt_res_quality: TagQuality
    ft_inlet_quality: TagQuality


@dataclass
class SkidSnapshot:
    """Full observable state after one scan — for HMI / tests / historian."""

    process: ProcessState
    safety: SafetyState
    cascade: CascadeOutputs
    measurement: MeasurementView
    sp_level: float
    """SP_LEVEL (m)."""

    sp_flow: float
    """SP_FLOW from level loop (L/min); held when not running."""

    cmd_speed: float
    """CMD_SPEED applied to the process this scan (%)."""

    lt_tank: Optional[float]
    """Safety-view LT_TANK (None when quality is not GOOD)."""

    lt_res: Optional[float]
    """Safety-view LT_RES (None when quality is not GOOD)."""

    ft_inlet: Optional[float]
    """Safety-view FT_INLET (None when quality is not GOOD)."""

    lt_tank_quality: TagQuality
    lt_res_quality: TagQuality
    ft_inlet_quality: TagQuality

    sc_pump: float
    mode: Mode
    perm_ok: bool
    trip_active: bool
    trip_codes: frozenset

    scan_phases: tuple[ScanPhase, ...] = PHASE_ORDER
    """Phases executed this scan (must be IN→SAFETY→CONTROL→OUT)."""

    scan_diagnostics: ScanDiagnostics | None = None
    """Shell diagnostics after this scan (overrun counters, last dt)."""

    # Convenience aliases
    @property
    def level_sp(self) -> float:
        return self.sp_level

    @property
    def flow_sp(self) -> float:
        return self.sp_flow


class Skid:
    """One-tank + reservoir skid scan engine.

    Typical use::

        skid = Skid()
        skid.sp_level = 0.22
        snap = skid.step(0.1, command=OperatorCommand.START)
        snap = skid.step(0.1)

    After a trip: clear condition → Reset → Start (reset does not auto-start).
    """

    def __init__(
        self,
        config: SkidConfig | None = None,
        *,
        process: ProcessPort | None = None,
        control: CascadeController | None = None,
        safety: SafetyLayer | None = None,
    ) -> None:
        self.config = config or SkidConfig()
        self._apply_limits()
        self.process: ProcessPort = process or MockProcess(self.config.process)
        self.safety = safety or SafetyLayer(self.config.safety)
        self.scan_shell = ScanShell(self.config.scan)
        # Re-sync in case injected process/safety carried stale thresholds
        self._apply_limits()
        self.sp_level = self.config.sp_level
        # When set, Flow Man/Rem SP overrides the cascade wire into flow_pi.sp
        # for that CONTROL tick (SWD-223). None → Automatic cascade wire.
        self.sp_flow_override: float | None = None
        # Process tag ↔ pin map (SWD-224). Default = wedge cascade demo.
        self._io_wires: list[TagPinWire] = list(wedge_cascade_io_wires())
        validate_tag_pin_wires(self._io_wires)
        self._last: SkidSnapshot | None = None
        self._was_running = False
        self._force_quality: dict[str, TagQuality] = {}
        self._override_lt_tank: object = _UNSET
        self._override_lt_res: object = _UNSET
        self._override_ft_inlet: object = _UNSET

        if control is None:
            # Default path: block runtime executes wedge_cascade_program in CONTROL.
            _lib = TemplateLibrary()
            self._block_runtime = BlockRuntime(_lib)
            register_builtins(_lib, self._block_runtime)
            self._loader = ProjectLoader(_lib, self._block_runtime)
            # Create context before initial load so the on-apply hook can clear it.
            self._block_context = DictContext()
            self._loader.add_on_apply_hook(self._on_program_apply)
            cfg = self.config.cascade
            scan_s = self.config.scan.scan_period_s
            self._loader.load(
                project_from_dict(
                    wedge_softplc_project(
                        level_kp=cfg.level_kp,
                        level_ki=cfg.level_ki,
                        flow_kp=cfg.flow_kp,
                        flow_ki=cfg.flow_ki,
                        sp_flow_min=cfg.sp_flow_min,
                        sp_flow_max=cfg.sp_flow_max,
                        cmd_speed_min=cfg.cmd_speed_min,
                        cmd_speed_max=cfg.cmd_speed_max,
                        scan_period_s=scan_s,
                    )
                )
            )
            self._use_block_runtime = True
            # Keep CascadeController for API compatibility; synced each scan.
            self.control = CascadeController(self.config.cascade)
        else:
            # Fallback path: explicit CascadeController injection.
            self.control = control
            self._use_block_runtime = False

    def _apply_limits(self) -> None:
        """Push LimitConfig into process derate + safety trip thresholds."""
        lim = self.config.limits
        self.config.process.lim_res_ll = lim.lim_res_ll
        self.config.safety.lim_level_hh = lim.lim_level_hh
        self.config.safety.lim_res_ll = lim.lim_res_ll
        process = getattr(self, "process", None)
        if process is not None and hasattr(process, "config"):
            process.config.lim_res_ll = lim.lim_res_ll  # type: ignore[attr-defined]
        safety = getattr(self, "safety", None)
        if safety is not None:
            safety.config.lim_level_hh = lim.lim_level_hh
            safety.config.lim_res_ll = lim.lim_res_ll

    @property
    def level_sp(self) -> float:
        """Alias for SP_LEVEL."""
        return self.sp_level

    @level_sp.setter
    def level_sp(self, value: float) -> None:
        self.sp_level = value

    @property
    def last(self) -> SkidSnapshot | None:
        return self._last

    def clear_faults(self) -> None:
        """Clear all quality injectors and PV overrides."""
        self._force_quality.clear()
        self._override_lt_tank = _UNSET
        self._override_lt_res = _UNSET
        self._override_ft_inlet = _UNSET

    def force_quality(
        self,
        tag: str,
        status: QualityStatus,
        reason: ReasonCode | None = None,
    ) -> None:
        """Force per-tag quality on a process PV (``LT_TANK``, ``LT_RES``, ``FT_INLET``).

        ``GOOD`` clears any injector for that tag. Non-GOOD requires a reason
        (defaults to ``FAULT`` when omitted).
        """
        key = tag.upper()
        if key not in _PV_TAGS:
            raise ValueError(f"force_quality tag must be one of {sorted(_PV_TAGS)}, got {tag!r}")
        if status is QualityStatus.GOOD:
            self._force_quality.pop(key, None)
            return
        self._force_quality[key] = TagQuality(status, reason if reason is not None else ReasonCode.FAULT)

    def force_lt_tank_bad(self, bad: bool = True) -> None:
        """Thin wrapper: force LT_TANK quality BAD/fault (or clear)."""
        if bad:
            self.force_quality("LT_TANK", QualityStatus.BAD, ReasonCode.FAULT)
        else:
            self.force_quality("LT_TANK", QualityStatus.GOOD)

    def force_lt_res_bad(self, bad: bool = True) -> None:
        """Thin wrapper: force LT_RES quality BAD/fault (or clear)."""
        if bad:
            self.force_quality("LT_RES", QualityStatus.BAD, ReasonCode.FAULT)
        else:
            self.force_quality("LT_RES", QualityStatus.GOOD)

    def force_ft_inlet_bad(self, bad: bool = True) -> None:
        """Thin wrapper: force FT_INLET quality BAD/fault (or clear)."""
        if bad:
            self.force_quality("FT_INLET", QualityStatus.BAD, ReasonCode.FAULT)
        else:
            self.force_quality("FT_INLET", QualityStatus.GOOD)

    def set_signal_override(
        self,
        *,
        lt_tank: object = _UNSET,
        lt_res: object = _UNSET,
        ft_inlet: object = _UNSET,
    ) -> None:
        """Override process measurements (``None`` = unavailable / LOS)."""
        if lt_tank is not _UNSET:
            self._override_lt_tank = lt_tank
        if lt_res is not _UNSET:
            self._override_lt_res = lt_res
        if ft_inlet is not _UNSET:
            self._override_ft_inlet = ft_inlet

    def clear_signal_overrides(self) -> None:
        self._override_lt_tank = _UNSET
        self._override_lt_res = _UNSET
        self._override_ft_inlet = _UNSET

    def _measurement_view(self, live: ProcessState) -> MeasurementView:
        """Resolve one measurement view for this scan (shared by safety + control).

        Quality from injectors or synthesized via ``resolve_tag_quality`` /
        ``pv_ok``: non-GOOD publishes the PV as ``None`` for safety/control.
        """
        lt_tank = self._read(self._override_lt_tank, live.lt_tank)
        lt_res = self._read(self._override_lt_res, live.lt_res)
        ft_inlet = self._read(self._override_ft_inlet, live.ft_inlet)

        tank_q = resolve_tag_quality(lt_tank, self._force_quality.get("LT_TANK"))
        res_q = resolve_tag_quality(lt_res, self._force_quality.get("LT_RES"))
        flow_q = resolve_tag_quality(ft_inlet, self._force_quality.get("FT_INLET"))

        return MeasurementView(
            lt_tank=lt_tank if is_good(tank_q) else None,
            lt_res=lt_res if is_good(res_q) else None,
            ft_inlet=ft_inlet if is_good(flow_q) else None,
            lt_tank_quality=tank_q,
            lt_res_quality=res_q,
            ft_inlet_quality=flow_q,
        )

    def step(
        self,
        dt: float,
        command: OperatorCommand = OperatorCommand.NONE,
        *,
        duration_s: float | None = None,
    ) -> SkidSnapshot:
        """Advance one scan by ``dt`` seconds under optional HMI command.

        Phase order is locked via ``ScanShell``: IN → SAFETY → CONTROL → OUT.
        ``duration_s`` is optional wall/logical duration for overrun diagnostics.
        """
        if dt < 0:
            raise ValueError("dt must be non-negative")

        # Mutable slots filled by phase callbacks (single-scan locals).
        box: dict[str, object] = {}

        def on_in() -> None:
            live = self.process.state
            box["mv"] = self._measurement_view(live)

        def on_safety() -> None:
            mv = box["mv"]
            assert isinstance(mv, MeasurementView)
            box["safety"] = self.safety.evaluate(
                lt_tank=mv.lt_tank,
                lt_res=mv.lt_res,
                ft_inlet=mv.ft_inlet,
                lt_tank_quality=mv.lt_tank_quality,
                lt_res_quality=mv.lt_res_quality,
                ft_inlet_quality=mv.ft_inlet_quality,
                start=command is OperatorCommand.START,
                stop=command is OperatorCommand.STOP,
                reset=command is OperatorCommand.RESET,
            )

        def on_control() -> None:
            mv = box["mv"]
            safety = box["safety"]
            assert isinstance(mv, MeasurementView)
            assert isinstance(safety, SafetyState)
            running = safety.pump_permit

            if self._use_block_runtime:
                # Block runtime path (default).
                if running and not self._was_running:
                    if mv.lt_tank is not None and mv.ft_inlet is not None:
                        self._prepare_bumpless_blocks(
                            lt_tank=mv.lt_tank,
                            ft_inlet=mv.ft_inlet,
                        )

                # Faceplate KP/KI live on CascadeConfig; sync into executing
                # PID instance params so Start actually drives with tuned gains
                # (SWD-224) — CascadeConfig alone is not read by BlockRuntime.
                self._sync_cascade_gains_into_instances()

                ctx = self._block_context
                tag_values = {
                    "LT_TANK": mv.lt_tank if mv.lt_tank is not None else 0.0,
                    "FT_INLET": mv.ft_inlet if mv.ft_inlet is not None else 0.0,
                    SHELL_TAG_LEVEL_SP: self.sp_level,
                    SHELL_TAG_RUNNING: running,
                }
                prefer_context: set[tuple[str, str]] = set()
                override = self.sp_flow_override
                active_wires = list(self._io_wires)
                if override is not None:
                    tag_values[SHELL_TAG_FLOW_SP_OVERRIDE] = float(override)
                    prefer_context.add(("flow_pi", "sp"))
                else:
                    active_wires = [
                        w
                        for w in active_wires
                        if w.tag != SHELL_TAG_FLOW_SP_OVERRIDE
                    ]

                apply_io_wires_in(
                    active_wires,
                    get_tag=tag_values.__getitem__,
                    set_pin=ctx.__setitem__,
                )

                self._loader.tick(
                    ctx, dt, prefer_context=prefer_context or None
                )

                out_tags: dict[str, float] = {}

                def _get_pin(key: str) -> object:
                    return ctx.get(key)

                def _set_tag(name: str, value: object) -> None:
                    out_tags[name] = float(value or 0.0)

                apply_io_wires_out(
                    active_wires, get_pin=_get_pin, set_tag=_set_tag
                )

                sp_flow = float(out_tags.get("SP_FLOW_AUTO", ctx.get("level_pi.cv") or 0.0))
                cmd_speed_raw = float(
                    out_tags.get("CMD_SPEED", ctx.get("flow_pi.cv") or 0.0)
                )
                # Shell precedence: when permit is false, force CMD_SPEED safe in
                # cascade / control.last as well as the OUT-phase process write.
                # Defense in depth if a graph somehow overrides ``running``.
                if not running:
                    cmd_speed_raw = 0.0
                    ctx["flow_pi.cv"] = 0.0
                lt_val = mv.lt_tank if mv.lt_tank is not None else 0.0
                ft_val = mv.ft_inlet if mv.ft_inlet is not None else 0.0
                flow_sp_active = (
                    float(override) if override is not None else sp_flow
                )
                cascade = CascadeOutputs(
                    sp_flow=sp_flow,
                    cmd_speed=cmd_speed_raw,
                    level_error=self.sp_level - lt_val,
                    flow_error=flow_sp_active - ft_val,
                )
                box["cascade"] = cascade
                # Sync control.last for callers that use the CascadeController API.
                self.control._last = cascade  # type: ignore[attr-defined]
            else:
                # CascadeController fallback path (explicit injection).
                if running and not self._was_running:
                    if mv.lt_tank is not None and mv.ft_inlet is not None:
                        self.control.prepare_bumpless(
                            lt_tank=mv.lt_tank,
                            ft_inlet=mv.ft_inlet,
                            sp_level=self.sp_level,
                            target_sp_flow=self.control.last.sp_flow,
                            target_cmd_speed=0.0,
                        )
                box["cascade"] = self.control.step(
                    dt,
                    lt_tank=mv.lt_tank,
                    ft_inlet=mv.ft_inlet,
                    sp_level=self.sp_level,
                    running=running,
                )
            self._was_running = running

        def on_out() -> None:
            safety = box["safety"]
            cascade = box["cascade"]
            assert isinstance(safety, SafetyState)
            assert isinstance(cascade, CascadeOutputs)
            running = safety.pump_permit
            # Safety precedence: CV forced 0 whenever permit is false.
            cmd_speed = cascade.cmd_speed if running else 0.0
            box["cmd_speed"] = cmd_speed
            box["process_state"] = self.process.step(dt, cmd_speed)

        diag = self.scan_shell.run(
            dt,
            on_in=on_in,
            on_safety=on_safety,
            on_control=on_control,
            on_out=on_out,
            duration_s=duration_s,
        )

        mv = box["mv"]
        safety = box["safety"]
        cascade = box["cascade"]
        process_state = box["process_state"]
        cmd_speed = box["cmd_speed"]
        assert isinstance(mv, MeasurementView)
        assert isinstance(safety, SafetyState)
        assert isinstance(cascade, CascadeOutputs)
        assert isinstance(process_state, ProcessState)
        assert isinstance(cmd_speed, float)

        snap = SkidSnapshot(
            process=process_state,
            safety=safety,
            cascade=cascade,
            measurement=mv,
            sp_level=self.sp_level,
            sp_flow=cascade.sp_flow,
            cmd_speed=cmd_speed,
            lt_tank=mv.lt_tank,
            lt_res=mv.lt_res,
            ft_inlet=mv.ft_inlet,
            lt_tank_quality=mv.lt_tank_quality,
            lt_res_quality=mv.lt_res_quality,
            ft_inlet_quality=mv.ft_inlet_quality,
            sc_pump=process_state.sc_pump,
            mode=safety.mode,
            perm_ok=safety.perm_ok,
            trip_active=safety.trip_active,
            trip_codes=frozenset(safety.trip_codes),
            scan_phases=diag.last_phases,
            scan_diagnostics=replace(diag),
        )
        self._last = snap
        return snap

    # ------------------------------------------------------------------
    # On-apply hook (registered with ProgramLoader on default path)
    # ------------------------------------------------------------------

    def apply_scan_period_s(self, scan_period_s: float) -> None:
        """Propagate project scan rate into shell config and overrun threshold."""
        if scan_period_s <= 0:
            raise ValueError("scan_period_s must be positive")
        self.config.scan.scan_period_s = scan_period_s
        self.scan_shell.config.scan_period_s = scan_period_s

    def _on_program_apply(self, is_restart: bool) -> None:
        """Called by ProjectLoader after each apply.

        Clears the scan context so stale CV / pin values from the previous
        program cannot bleed into the new program's first tick.  On restart
        also resets ``_was_running`` so bumpless prep fires correctly on the
        first RUNNING scan of the new program.  Always syncs ``scan_period_s``
        from the active project.
        """
        self._block_context = DictContext()
        if is_restart:
            self._was_running = False
        proj = self._loader.project
        if proj is not None:
            self.apply_scan_period_s(proj.scan_period_s)

    # ------------------------------------------------------------------
    # Block-runtime accessors (public, only set on default path)
    # ------------------------------------------------------------------

    @property
    def block_runtime(self) -> BlockRuntime | None:
        """Block runtime when using the default block path; ``None`` if fallback."""
        return getattr(self, "_block_runtime", None)

    @property
    def program_loader(self) -> ProjectLoader | None:
        """``ProjectLoader`` when using the default block path; ``None`` if fallback."""
        return getattr(self, "_loader", None)

    @property
    def block_context(self) -> DictContext | None:
        """``DictContext`` shared between scans; ``None`` if fallback."""
        return getattr(self, "_block_context", None)

    @property
    def io_wires(self) -> list[TagPinWire]:
        """Process tag ↔ pin wirings used each CONTROL tick (SWD-224)."""
        return list(self._io_wires)

    def set_io_wires(self, wires: list[TagPinWire]) -> None:
        """Replace the external I/O map (validated)."""
        validate_tag_pin_wires(wires)
        self._io_wires = list(wires)

    def _sync_cascade_gains_into_instances(self) -> None:
        """Copy CascadeConfig KP/KI into live PID instance params (SWD-224).

        Faceplate / image tags update ``Skid.config.cascade``; BlockRuntime
        only reads ``inst.params``. Without this sync, Start appears to leave
        CVs unchanged after retune (and docs claiming tunings apply were false).
        """
        prog = self._loader.program if self._loader is not None else None
        if prog is None:
            return
        cfg = self.config.cascade
        mapping = (
            ("level_pi", (("kp", cfg.level_kp), ("ki", cfg.level_ki))),
            ("flow_pi", (("kp", cfg.flow_kp), ("ki", cfg.flow_ki))),
        )
        for inst_id, pairs in mapping:
            inst = prog.instances.get(inst_id)
            if inst is None:
                continue
            for key, value in pairs:
                inst.params[key] = float(value)

    # ------------------------------------------------------------------
    # Bumpless-start helper for block runtime
    # ------------------------------------------------------------------

    def _prepare_bumpless_blocks(self, *, lt_tank: float, ft_inlet: float) -> None:
        """Pre-seed block runtime integrators for a bumpless Start.

        Mirrors ``CascadeController.prepare_bumpless``:
        - target_sp_flow = last held level_pi output (0.0 on first start).
        - target_cmd_speed = 0.0 (always start from rest).

        Gains are read from the active program's instance params first so that
        per-instance overrides (different from ``SkidConfig.cascade``) are
        respected; falls back to ``SkidConfig.cascade`` if the instance or
        param is absent.

        Sets ``bumpless_pending=True`` on both PI instances so that the first
        RUNNING scan skips the I-advance and matches the target outputs.
        """
        cfg = self.config.cascade

        # Prefer instance params over SkidConfig for bumpless seeding.
        prog = self._loader.program
        level_inst = prog.instances.get("level_pi") if prog else None
        flow_inst = prog.instances.get("flow_pi") if prog else None

        def _p(inst: object, key: str, fallback: float) -> float:
            if inst is not None and hasattr(inst, "params"):
                v = inst.params.get(key)  # type: ignore[attr-defined]
                if v is not None:
                    return float(v)
            return fallback

        level_kp = _p(level_inst, "kp", cfg.level_kp)
        level_ki = _p(level_inst, "ki", cfg.level_ki)
        sp_flow_min = _p(level_inst, "cv_min", cfg.sp_flow_min)
        sp_flow_max = _p(level_inst, "cv_max", cfg.sp_flow_max)
        flow_kp = _p(flow_inst, "kp", cfg.flow_kp)
        flow_ki = _p(flow_inst, "ki", cfg.flow_ki)

        last_cv = self._block_context.get("level_pi.cv")
        target_sp_flow = float(last_cv) if last_cv is not None else 0.0
        target_sp_flow = max(sp_flow_min, min(sp_flow_max, target_sp_flow))
        target_cmd_speed = 0.0

        level_error = self.sp_level - lt_tank
        flow_error = target_sp_flow - ft_inlet

        level_integral = (
            (target_sp_flow - level_kp * level_error) / level_ki
            if level_ki != 0.0
            else 0.0
        )
        self._block_runtime.set_instance_state(
            "level_pi",
            {
                "integral": level_integral,
                "bumpless_pending": True,
                "last_cv": target_sp_flow,
            },
        )

        flow_integral = (
            (target_cmd_speed - flow_kp * flow_error) / flow_ki
            if flow_ki != 0.0
            else 0.0
        )
        self._block_runtime.set_instance_state(
            "flow_pi",
            {
                "integral": flow_integral,
                "bumpless_pending": True,
                "last_cv": target_cmd_speed,
            },
        )

    # ------------------------------------------------------------------

    @staticmethod
    def _read(override: object, live: float) -> Optional[float]:
        if override is _UNSET:
            return live
        return override  # type: ignore[return-value]


__all__ = [
    "OperatorCommand",
    "LimitConfig",
    "MeasurementView",
    "Skid",
    "SkidConfig",
    "SkidSnapshot",
    "Mode",
    "TripCode",
]
