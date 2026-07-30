"""Structured equation forms for unit-ops (SWD-167).

Exposes the underlying state / algebraic dynamics of catalog ops and custom
blocks so the Dynamics editor can show one equation per row.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from .expr import ExpressionError, compile_expr

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class EquationForm:
    """One human-readable dynamical relation."""

    kind: str  # "state" | "algebraic"
    left: str
    right: str
    note: str | None = None

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "kind": self.kind,
            "left": self.left,
            "right": self.right,
        }
        if self.note:
            out["note"] = self.note
        return out


def is_simple_name(expr: str) -> bool:
    return bool(_IDENT.match(str(expr or "").strip()))


def _p(params: Mapping[str, Any], *keys: str, default: str = "?") -> str:
    for key in keys:
        if key in params and params[key] not in (None, ""):
            return str(params[key])
    return default


def _b(bind: Mapping[str, str], key: str, default: str | None = None) -> str:
    if key in bind and bind[key]:
        return str(bind[key])
    return default if default is not None else key


def describe_op_equations(
    op_type: str,
    bind: Mapping[str, str] | None = None,
    params: Mapping[str, Any] | None = None,
) -> tuple[EquationForm, ...]:
    """Return substituted equation forms for an op instance."""
    bind = {str(k): str(v) for k, v in (bind or {}).items()}
    params = dict(params or {})
    kind = str(op_type or "").strip().lower()

    if kind == "tank":
        h = _b(bind, "h")
        q_in = _b(bind, "q_in")
        q_out = _b(bind, "q_out")
        area = _p(params, "area", default="area")
        return (
            EquationForm(
                kind="state",
                left=f"d({h})/dt",
                right=f"({q_in} - {q_out}) / ({area} * 1000 * 60)",
                note="Volumetric balance; area in m², flows in L/min → level in m.",
            ),
        )

    if kind == "pump":
        q = _b(bind, "q")
        cmd = _b(bind, "cmd")
        h_source = _b(bind, "h_source")
        q_max = _p(params, "q_max", "q_pump_max", default="q_max")
        tau = _p(params, "tau", "pump_tau", default="tau")
        lim_ll = _p(params, "lim_ll", "lim_res_ll", default="lim_ll")
        return (
            EquationForm(
                kind="algebraic",
                left=f"{q}__cmd",
                right=(
                    f"{q_max} * ({cmd}/100) * derate({h_source}, {lim_ll})"
                ),
                note="Target flow; derate→0 when source level is low.",
            ),
            EquationForm(
                kind="state",
                left=f"d({q})/dt",
                right=f"({q}__cmd - {q}) / {tau}",
                note="First-order lag toward target (Euler / α = 1−e^(−dt/τ)).",
            ),
        )

    if kind == "orifice":
        h = _b(bind, "h")
        q = _b(bind, "q")
        k = _p(params, "k", "k_drain", default="k")
        return (
            EquationForm(
                kind="algebraic",
                left=q,
                right=f"{k} * sqrt(max({h}, 0))",
                note="Gravity drain orifice (not integrated state).",
            ),
        )

    if kind == "lag":
        u = _b(bind, "u")
        y = _b(bind, "y")
        tau = _p(params, "tau", default="tau")
        return (
            EquationForm(
                kind="state",
                left=f"d({y})/dt",
                right=f"({u} - {y}) / {tau}",
                note="First-order lag (Euler / α = 1−e^(−dt/τ)).",
            ),
        )

    if kind == "custom_ode":
        forms: list[EquationForm] = []
        derivatives = params.get("derivatives") or {}
        if isinstance(derivatives, Mapping):
            for state, expr in derivatives.items():
                forms.append(
                    EquationForm(
                        kind="state",
                        left=f"d({state})/dt",
                        right=str(expr),
                    )
                )
        algebraic = params.get("algebraic") or {}
        if isinstance(algebraic, Mapping):
            for name, expr in algebraic.items():
                forms.append(
                    EquationForm(
                        kind="algebraic",
                        left=str(name),
                        right=str(expr),
                        note="Evaluated each step; not integrated.",
                    )
                )
        return tuple(forms)

    raise ExpressionError(f"unknown unit-op type: {op_type!r}")


def equation_templates() -> dict[str, list[dict[str, str]]]:
    """Catalog templates with `{port}` / `{param}` placeholders for the UI."""
    return {
        "tank": [
            {
                "kind": "state",
                "left": "d({h})/dt",
                "right": "({q_in} - {q_out}) / ({area} * 1000 * 60)",
                "note": "Volumetric balance; area in m², flows in L/min → level in m.",
            }
        ],
        "pump": [
            {
                "kind": "algebraic",
                "left": "{q}__cmd",
                "right": "{q_max} * ({cmd}/100) * derate({h_source}, {lim_ll})",
                "note": "Target flow; derate→0 when source level is low.",
            },
            {
                "kind": "state",
                "left": "d({q})/dt",
                "right": "({q}__cmd - {q}) / {tau}",
                "note": "First-order lag toward target.",
            },
        ],
        "orifice": [
            {
                "kind": "algebraic",
                "left": "{q}",
                "right": "{k} * sqrt(max({h}, 0))",
                "note": "Gravity drain orifice (not integrated state).",
            }
        ],
        "lag": [
            {
                "kind": "state",
                "left": "d({y})/dt",
                "right": "({u} - {y}) / {tau}",
                "note": "First-order lag.",
            }
        ],
        "custom_ode": [],
    }


def validate_measurement_expr(expr: str) -> None:
    compile_expr(str(expr))


__all__ = [
    "EquationForm",
    "describe_op_equations",
    "equation_templates",
    "is_simple_name",
    "validate_measurement_expr",
]
