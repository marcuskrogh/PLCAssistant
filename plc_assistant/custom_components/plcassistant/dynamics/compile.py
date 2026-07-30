"""Compile unit-op model documents into ModelSpec + SpecModel (SWD-144/167)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .core import DynamicsModel, InputDict, ModelSpec, ParamDict, StateDict
from .equations import is_simple_name, validate_measurement_expr
from .expr import ExpressionError, compile_expr
from .ops import OP_CATALOG, get_op, limit_flows

SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class Measurement:
    """One Soft-PLC IN tag produced by evaluating an expression."""

    tag: str
    expr: str


@dataclass
class ModelDocument:
    """Validated in-memory model document."""

    name: str
    version: str
    inputs: tuple[str, ...]
    outputs: Mapping[str, str]
    """Nudge map tag → state key (identity subset of measurements)."""
    params: ParamDict
    initial: StateDict
    ops: tuple[dict[str, Any], ...]
    measurements: tuple[Measurement, ...] = ()
    inventory_couple: Mapping[str, str] | None = None


def _as_mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ExpressionError(f"{field} must be a mapping")
    return value


def _parse_measurements(
    data: Mapping[str, Any],
    outputs: Mapping[str, str],
) -> tuple[Measurement, ...]:
    raw = data.get("measurements")
    if raw is None:
        if not outputs:
            raise ExpressionError("outputs or measurements required")
        return tuple(Measurement(tag=str(k), expr=str(v)) for k, v in outputs.items())
    if not isinstance(raw, list) or not raw:
        raise ExpressionError("measurements must be a non-empty list")
    seen: set[str] = set()
    out: list[Measurement] = []
    for item in raw:
        row = _as_mapping(item, field="measurement")
        tag = str(row.get("tag") or "").strip().upper()
        expr = str(row.get("expr") or "").strip()
        if not tag or not expr:
            raise ExpressionError("each measurement requires tag and expr")
        if tag in seen:
            raise ExpressionError(f"duplicate measurement tag: {tag!r}")
        seen.add(tag)
        validate_measurement_expr(expr)
        out.append(Measurement(tag=tag, expr=expr))
    return tuple(out)


def _nudge_outputs_from_measurements(
    measurements: tuple[Measurement, ...],
) -> dict[str, str]:
    """Identity measurements remain Number-nudgeable via output_tags."""
    nudge: dict[str, str] = {}
    for m in measurements:
        if is_simple_name(m.expr):
            nudge[m.tag] = m.expr.strip()
    return nudge


def parse_model_document(raw: Any) -> ModelDocument:
    data = _as_mapping(raw, field="document")
    version = str(data.get("version") or "").strip()
    if version != SCHEMA_VERSION:
        raise ExpressionError(
            f"unsupported model document version: {version!r} (expected {SCHEMA_VERSION!r})"
        )
    name = str(data.get("name") or "").strip()
    if not name:
        raise ExpressionError("model document requires name")
    inputs_raw = data.get("inputs") or []
    if not isinstance(inputs_raw, list) or not all(isinstance(x, str) for x in inputs_raw):
        raise ExpressionError("inputs must be a list of strings")
    outputs = {
        str(k).upper(): str(v)
        for k, v in _as_mapping(data.get("outputs") or {}, field="outputs").items()
    }
    measurements = _parse_measurements(data, outputs)
    # Prefer explicit outputs; fill gaps from identity measurements.
    merged = dict(outputs)
    for tag, state_key in _nudge_outputs_from_measurements(measurements).items():
        merged.setdefault(tag, state_key)
    outputs = merged
    if not measurements:
        raise ExpressionError("outputs or measurements required")
    params = {
        str(k): float(v)
        for k, v in _as_mapping(data.get("params") or {}, field="params").items()
    }
    initial = {
        str(k): float(v)
        for k, v in _as_mapping(data.get("initial") or {}, field="initial").items()
    }
    ops_raw = data.get("ops") or []
    if not isinstance(ops_raw, list) or not ops_raw:
        raise ExpressionError("ops must be a non-empty list")
    ops: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in ops_raw:
        op = _as_mapping(item, field="op")
        op_id = str(op.get("id") or "").strip()
        op_type = str(op.get("type") or "").strip().lower()
        if not op_id or not op_type:
            raise ExpressionError("each op requires id and type")
        if op_id in seen_ids:
            raise ExpressionError(f"duplicate op id: {op_id!r}")
        seen_ids.add(op_id)
        if op_type not in OP_CATALOG:
            raise ExpressionError(f"unknown unit-op type: {op_type!r}")
        bind = {
            str(k): str(v)
            for k, v in _as_mapping(op.get("bind") or {}, field=f"op {op_id} bind").items()
        }
        # Validate declare now (also compiles custom_ode expressions).
        get_op(op_type).declare(bind, op.get("params") or {})
        ops.append(dict(op))
    couple_raw = data.get("inventory_couple")
    couple: Mapping[str, str] | None = None
    if couple_raw is not None:
        couple = {
            str(k): str(v)
            for k, v in _as_mapping(couple_raw, field="inventory_couple").items()
        }
        required = (
            "q_in",
            "q_drain",
            "h_tank",
            "h_res",
            "a_tank",
            "a_res",
            "h_tank_max",
            "h_res_max",
        )
        missing = [k for k in required if k not in couple]
        if missing:
            raise ExpressionError(f"inventory_couple missing keys: {missing}")
    return ModelDocument(
        name=name,
        version=version,
        inputs=tuple(inputs_raw),
        outputs=outputs,
        params=params,
        initial=initial,
        ops=tuple(ops),
        measurements=measurements,
        inventory_couple=couple,
    )


def load_model_document(path: str | Path) -> ModelDocument:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    suffix = file_path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as err:
            raise ExpressionError("PyYAML required to load .yaml model documents") from err
        raw = yaml.safe_load(text)
    else:
        raw = json.loads(text)
    return parse_model_document(raw)


def _param_map(op: Mapping[str, Any], model_params: ParamDict) -> dict[str, Any]:
    """Merge op-local params; string values may reference model params."""
    local = dict(op.get("params") or {})
    # Keep derivatives / algebraic maps intact for custom_ode.
    resolved: dict[str, Any] = {}
    for key, value in local.items():
        if key in {"derivatives", "algebraic"} and isinstance(value, Mapping):
            resolved[key] = dict(value)
            continue
        if isinstance(value, str) and value in model_params:
            resolved[key] = float(model_params[value])
        else:
            resolved[key] = value
    # Also expose full model params for _resolve_param lookups.
    for key, value in model_params.items():
        resolved.setdefault(key, float(value))
    return resolved


def compile_document(doc: ModelDocument) -> ModelSpec:
    """Compile a validated document into a collected ModelSpec."""
    state_keys: list[str] = []
    for op in doc.ops:
        bind = {str(k): str(v) for k, v in (op.get("bind") or {}).items()}
        decl = get_op(str(op["type"])).declare(bind, op.get("params") or {})
        for key in decl.state_keys:
            if key not in state_keys:
                state_keys.append(key)
    for key in doc.initial:
        if key not in state_keys:
            state_keys.append(key)
    # Ensure identity-measurement / output state keys exist.
    for state_key in doc.outputs.values():
        if state_key not in state_keys:
            state_keys.append(state_key)
    for m in doc.measurements:
        if is_simple_name(m.expr) and m.expr.strip() not in state_keys:
            state_keys.append(m.expr.strip())

    op_runtime = []
    for op in doc.ops:
        bind = {str(k): str(v) for k, v in (op.get("bind") or {}).items()}
        op_runtime.append(
            (
                get_op(str(op["type"])),
                bind,
                _param_map(op, doc.params),
            )
        )
    couple = dict(doc.inventory_couple) if doc.inventory_couple else None
    param_defaults = dict(doc.params)
    initial_state = {k: float(doc.initial.get(k, 0.0)) for k in state_keys}
    input_keys = tuple(doc.inputs)
    output_tags = dict(doc.outputs)
    measurement_exprs = {m.tag: m.expr for m in doc.measurements}
    tank_binds = [
        bind
        for op, bind, _ in op_runtime
        if op.name == "tank"
    ]

    def rhs(dt: float, state: StateDict, inputs: InputDict, params: ParamDict) -> StateDict:
        ctx: dict[str, float] = {k: float(v) for k, v in state.items()}
        for key in input_keys:
            value = float(inputs.get(key, 0.0))
            if key == "cmd_speed":
                value = 0.0 if value < 0.0 else 100.0 if value > 100.0 else value
            ctx[key] = value
        # Prefer live params over defaults.
        for key, value in params.items():
            ctx[key] = float(value)
        for op, bind, op_params in op_runtime:
            live_params = dict(op_params)
            for key, value in params.items():
                live_params[key] = float(value)
            op.contribute(dt=dt, ctx=ctx, bind=bind, params=live_params)

        if couple is not None and dt > 0.0:
            q_in_name = couple["q_in"]
            q_drain_name = couple["q_drain"]
            q_in_cmd = float(ctx.get(q_in_name + "__cmd", ctx.get(q_in_name, 0.0)))
            q_drain_cmd = float(
                ctx.get(q_drain_name + "__cmd", ctx.get(q_drain_name, 0.0))
            )
            h_tank = float(ctx[couple["h_tank"]])
            h_res = float(ctx[couple["h_res"]])
            q_in, q_drain = limit_flows(
                q_in=q_in_cmd,
                q_drain=q_drain_cmd,
                h_tank=h_tank,
                h_res=h_res,
                a_tank=float(params.get(couple["a_tank"], ctx.get(couple["a_tank"], 0.05))),
                a_res=float(params.get(couple["a_res"], ctx.get(couple["a_res"], 0.10))),
                h_tank_max=float(
                    params.get(couple["h_tank_max"], ctx.get(couple["h_tank_max"], 0.40))
                ),
                h_res_max=float(
                    params.get(couple["h_res_max"], ctx.get(couple["h_res_max"], 0.30))
                ),
                dt=dt,
            )
            ctx[q_in_name] = q_in
            ctx[q_drain_name] = q_drain
            # Integrate tanks after limiting (matches skid_rhs order).
            for bind in tank_binds:
                h_key = bind["h"]
                q_in_key = bind["q_in"]
                q_out_key = bind["q_out"]
                if h_key == couple["h_tank"]:
                    area = float(
                        params.get(couple["a_tank"], ctx.get(couple["a_tank"], 0.05))
                    )
                elif h_key == couple["h_res"]:
                    area = float(
                        params.get(couple["a_res"], ctx.get(couple["a_res"], 0.10))
                    )
                else:
                    area = float(ctx.get(h_key + "_area", 0.05))
                to_m = 1.0 / (area * 1000.0 * 60.0)
                ctx[h_key] = float(ctx[h_key]) + (
                    float(ctx[q_in_key]) - float(ctx[q_out_key])
                ) * to_m * dt
        elif dt > 0.0:
            for bind in tank_binds:
                h_key = bind["h"]
                area = float(ctx.get(h_key + "_area", params.get("area", 0.05)))
                to_m = 1.0 / (area * 1000.0 * 60.0)
                ctx[h_key] = float(ctx[h_key]) + (
                    float(ctx.get(bind["q_in"], 0.0)) - float(ctx.get(bind["q_out"], 0.0))
                ) * to_m * dt

        out: StateDict = {k: float(ctx.get(k, state.get(k, 0.0))) for k in state_keys}
        if "cmd_speed" in state or "cmd_speed" in inputs:
            out["cmd_speed"] = float(inputs.get("cmd_speed", ctx.get("cmd_speed", 0.0)))
        return out

    def project(state: StateDict, params: ParamDict, dt: float) -> StateDict:
        del dt
        out = dict(state)
        if couple is not None:
            out[couple["h_tank"]] = max(
                0.0,
                min(
                    float(out.get(couple["h_tank"], 0.0)),
                    float(params.get(couple["h_tank_max"], 0.40)),
                ),
            )
            out[couple["h_res"]] = max(
                0.0,
                min(
                    float(out.get(couple["h_res"], 0.0)),
                    float(params.get(couple["h_res_max"], 0.30)),
                ),
            )
            q_in_name = couple["q_in"]
            if q_in_name in out:
                out[q_in_name] = max(0.0, float(out[q_in_name]))
        if "sc_pump" in out:
            out["sc_pump"] = max(0.0, min(100.0, float(out["sc_pump"])))
        if "cmd_speed" in out:
            out["cmd_speed"] = max(0.0, min(100.0, float(out["cmd_speed"])))
        return out

    return ModelSpec(
        name=doc.name,
        state_keys=tuple(state_keys),
        input_keys=input_keys,
        output_tags=output_tags,
        param_defaults=param_defaults,
        initial_state=initial_state,
        rhs=rhs,
        project=project,
        measurement_exprs=measurement_exprs,
    )


class SpecModel:
    """Runnable DynamicsModel backed by a compiled ModelSpec."""

    def __init__(
        self,
        spec: ModelSpec,
        params: Mapping[str, float] | None = None,
    ) -> None:
        self._spec = spec
        self._params: ParamDict = dict(spec.param_defaults)
        if params:
            self._params.update({k: float(v) for k, v in params.items()})
        self._state: StateDict = {
            key: float(spec.initial_state.get(key, 0.0)) for key in spec.state_keys
        }
        self._inputs: InputDict = {key: 0.0 for key in spec.input_keys}
        exprs = dict(spec.measurement_exprs) if spec.measurement_exprs else {
            tag: key for tag, key in spec.output_tags.items()
        }
        self._measurement_fns: dict[str, Callable[[Mapping[str, float]], float]] = {
            tag: compile_expr(expr) for tag, expr in exprs.items()
        }

    @property
    def spec(self) -> ModelSpec:
        return self._spec

    @property
    def state(self) -> Mapping[str, float]:
        return dict(self._state)

    @property
    def params(self) -> Mapping[str, float]:
        return dict(self._params)

    def set_input(self, name: str, value: float) -> None:
        if name not in self._spec.input_keys:
            raise KeyError(name)
        self._inputs[name] = float(value)

    def set_state(self, name: str, value: float) -> None:
        if name not in self._state and name not in self._spec.state_keys:
            raise KeyError(name)
        self._state[name] = float(value)

    def step(self, dt: float) -> Mapping[str, float]:
        tentative = self._spec.rhs(dt, self._state, self._inputs, self._params)
        self._state = self._spec.project(tentative, self._params, dt)
        keep = set(self._spec.state_keys)
        if "cmd_speed" in self._state:
            keep.add("cmd_speed")
        self._state = {k: float(v) for k, v in self._state.items() if k in keep}
        return dict(self._state)

    def outputs(self) -> Mapping[str, float]:
        # Refresh algebraics (orifice q, custom_ode algebraic, …) without
        # advancing time so measurement exprs see a coherent ctx.
        snap = self._spec.rhs(0.0, self._state, self._inputs, self._params)
        ctx: dict[str, float] = {k: float(v) for k, v in snap.items()}
        for key, value in self._params.items():
            ctx[key] = float(value)
        for key, value in self._inputs.items():
            ctx[key] = float(value)
        return {tag: float(fn(ctx)) for tag, fn in self._measurement_fns.items()}

    def nudge(self, **deltas: float) -> None:
        if "h_tank" in deltas or "dh_tank" in deltas:
            delta = float(deltas.get("h_tank", deltas.get("dh_tank", 0.0)))
            if "h_tank" in self._state:
                self._state["h_tank"] = float(self._state["h_tank"]) + delta
        if "h_res" in deltas or "dh_res" in deltas:
            delta = float(deltas.get("h_res", deltas.get("dh_res", 0.0)))
            if "h_res" in self._state:
                self._state["h_res"] = float(self._state["h_res"]) + delta
        for key, value in deltas.items():
            if key in ("h_tank", "h_res", "dh_tank", "dh_res"):
                continue
            if key in self._state:
                self._state[key] = float(value)
        self._state = self._spec.project(self._state, self._params, 0.0)


def document_to_model(
    doc: ModelDocument, params: Mapping[str, float] | None = None
) -> SpecModel:
    return SpecModel(compile_document(doc), params=params)


__all__ = [
    "SCHEMA_VERSION",
    "Measurement",
    "ModelDocument",
    "SpecModel",
    "compile_document",
    "document_to_model",
    "load_model_document",
    "parse_model_document",
]
