"""Safe math-equation evaluator for equation-driven blocks (SWD-180).

The authoring language is intentionally small: one assignment per line, with
right-hand sides limited to arithmetic, comparisons, boolean operators, ternary
``a if cond else b`` expressions, and whitelisted helper functions.
"""

from __future__ import annotations

import ast
import math
from collections.abc import Mapping
from typing import Any

from plcassistant.control.pid import anti_windup, zoh_fy
from plcassistant.surface.model import BlockTemplate, PinDirection


class EquationError(ValueError):
    """Raised when an equation document is invalid or unsafe."""


_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod)
_ALLOWED_UNARY = (ast.UAdd, ast.USub, ast.Not)
_ALLOWED_BOOLOPS = (ast.And, ast.Or)
_ALLOWED_CMPOPS = (
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
)


def clamp(value: Any, lo: Any, hi: Any) -> float:
    """Clamp *value* into [lo, hi] and return a float."""
    v = float(value)
    low = float(lo)
    high = float(hi)
    if low > high:
        low, high = high, low
    if v < low:
        return low
    if v > high:
        return high
    return v


def _zoh_coeff(tf_ts: Any, tx: Any, index: int) -> float:
    return zoh_fy(float(tf_ts), float(tx))[index]


_FUNCTIONS: dict[str, Any] = {
    "abs": abs,
    "bool": bool,
    "ceil": math.ceil,
    "clamp": clamp,
    "exp": math.exp,
    "float": float,
    "floor": math.floor,
    "int": int,
    "isfinite": math.isfinite,
    "log": math.log,
    "max": max,
    "min": min,
    "pid_anti_windup": anti_windup,
    "pid_zoh_a11": lambda tf_ts, tx: _zoh_coeff(tf_ts, tx, 0),
    "pid_zoh_a12": lambda tf_ts, tx: _zoh_coeff(tf_ts, tx, 1),
    "pid_zoh_a21": lambda tf_ts, tx: _zoh_coeff(tf_ts, tx, 2),
    "pid_zoh_a22": lambda tf_ts, tx: _zoh_coeff(tf_ts, tx, 3),
    "pid_zoh_b1": lambda tf_ts, tx: _zoh_coeff(tf_ts, tx, 4),
    "pid_zoh_b2": lambda tf_ts, tx: _zoh_coeff(tf_ts, tx, 5),
    "pow": pow,
    "round": round,
    "sqrt": math.sqrt,
}


def _state_reader(state: Mapping[str, Any]):
    def read(name: Any, default: Any = 0.0) -> Any:
        return state.get(str(name), default)

    return read


def _check_expr(node: ast.AST) -> None:
    if isinstance(node, ast.Expression):
        _check_expr(node.body)
        return
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, bool, str)) or node.value is None:
            return
        raise EquationError(f"unsupported constant: {node.value!r}")
    if isinstance(node, ast.Name):
        if node.id.startswith("__"):
            raise EquationError(f"invalid name: {node.id!r}")
        return
    if isinstance(node, ast.BinOp):
        if not isinstance(node.op, _ALLOWED_BINOPS):
            raise EquationError(f"unsupported operator: {type(node.op).__name__}")
        _check_expr(node.left)
        _check_expr(node.right)
        return
    if isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, _ALLOWED_UNARY):
            raise EquationError(f"unsupported unary: {type(node.op).__name__}")
        _check_expr(node.operand)
        return
    if isinstance(node, ast.BoolOp):
        if not isinstance(node.op, _ALLOWED_BOOLOPS):
            raise EquationError(f"unsupported boolean op: {type(node.op).__name__}")
        for value in node.values:
            _check_expr(value)
        return
    if isinstance(node, ast.IfExp):
        _check_expr(node.test)
        _check_expr(node.body)
        _check_expr(node.orelse)
        return
    if isinstance(node, ast.Compare):
        _check_expr(node.left)
        for op in node.ops:
            if not isinstance(op, _ALLOWED_CMPOPS):
                raise EquationError(f"unsupported comparison: {type(op).__name__}")
        for comparator in node.comparators:
            _check_expr(comparator)
        return
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise EquationError("only simple function calls are allowed")
        if node.func.id not in _FUNCTIONS and node.func.id != "state":
            raise EquationError(f"function not allowed: {node.func.id!r}")
        if node.keywords:
            raise EquationError("keyword arguments are not allowed")
        for arg in node.args:
            _check_expr(arg)
        return
    raise EquationError(f"unsupported syntax: {type(node).__name__}")


def _eval_expr(node: ast.AST, values: Mapping[str, Any]) -> Any:
    try:
        return _eval_expr_inner(node, values)
    except EquationError:
        raise
    except (ArithmeticError, TypeError, ValueError, OverflowError) as exc:
        raise EquationError(f"evaluation failed: {exc}") from exc


def _eval_expr_inner(node: ast.AST, values: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Expression):
        return _eval_expr_inner(node.body, values)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in values:
            return values[node.id]
        raise EquationError(f"unknown name: {node.id!r}")
    if isinstance(node, ast.UnaryOp):
        value = _eval_expr_inner(node.operand, values)
        if isinstance(node.op, ast.UAdd):
            return +float(value)
        if isinstance(node.op, ast.USub):
            return -float(value)
        if isinstance(node.op, ast.Not):
            return not bool(value)
    if isinstance(node, ast.BinOp):
        left = _eval_expr_inner(node.left, values)
        right = _eval_expr_inner(node.right, values)
        if isinstance(node.op, ast.Add):
            return float(left) + float(right)
        if isinstance(node.op, ast.Sub):
            return float(left) - float(right)
        if isinstance(node.op, ast.Mult):
            return float(left) * float(right)
        if isinstance(node.op, ast.Div):
            return float(left) / float(right)
        if isinstance(node.op, ast.Pow):
            return float(left) ** float(right)
        if isinstance(node.op, ast.Mod):
            return float(left) % float(right)
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            result: Any = True
            for value in node.values:
                result = _eval_expr_inner(value, values)
                if not bool(result):
                    return result
            return result
        if isinstance(node.op, ast.Or):
            result = False
            for value in node.values:
                result = _eval_expr_inner(value, values)
                if bool(result):
                    return result
            return result
    if isinstance(node, ast.IfExp):
        branch = node.body if bool(_eval_expr_inner(node.test, values)) else node.orelse
        return _eval_expr_inner(branch, values)
    if isinstance(node, ast.Compare):
        left = _eval_expr_inner(node.left, values)
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval_expr_inner(comparator, values)
            if isinstance(op, ast.Eq):
                ok = left == right
            elif isinstance(op, ast.NotEq):
                ok = left != right
            elif isinstance(op, ast.Lt):
                ok = float(left) < float(right)
            elif isinstance(op, ast.LtE):
                ok = float(left) <= float(right)
            elif isinstance(op, ast.Gt):
                ok = float(left) > float(right)
            elif isinstance(op, ast.GtE):
                ok = float(left) >= float(right)
            else:  # pragma: no cover - guarded by _check_expr
                raise EquationError(f"unsupported comparison: {type(op).__name__}")
            if not ok:
                return False
            left = right
        return True
    if isinstance(node, ast.Call):
        assert isinstance(node.func, ast.Name)
        fn = values.get(node.func.id)
        if fn is None:
            raise EquationError(f"function not allowed: {node.func.id!r}")
        args = [_eval_expr_inner(arg, values) for arg in node.args]
        try:
            return fn(*args)
        except (ArithmeticError, TypeError, ValueError, OverflowError) as exc:
            raise EquationError(f"call {node.func.id} failed: {exc}") from exc
    raise EquationError(f"unsupported syntax: {type(node).__name__}")


def evaluate_equation(
    equation: str,
    template: BlockTemplate,
    input_pins: Mapping[str, Any],
    params: Mapping[str, Any],
    state: dict[str, Any],
    dt: float,
) -> dict[str, Any]:
    """Evaluate an equation document and return output pin values.

    Assigned non-output variables are persisted into ``state`` for the next
    scan, which lets equations implement integrators and bumpless state without
    exposing Python object mutation.
    """
    values: dict[str, Any] = {}
    values.update(state)
    values.update(template.params)
    values.update(params)
    values.update(input_pins)
    for pin in template.pins:
        if pin.direction is PinDirection.IN and pin.name not in values:
            values[pin.name] = pin.default
    values.update(_FUNCTIONS)
    values["state"] = _state_reader(state)
    values["dt"] = float(dt)
    values["True"] = True
    values["False"] = False
    values["None"] = None

    assigned: set[str] = set()
    for line_no, raw_line in enumerate(equation.splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            parsed = ast.parse(line, mode="exec")
        except SyntaxError as exc:
            raise EquationError(f"line {line_no}: syntax error: {exc.msg}") from exc
        if len(parsed.body) != 1 or not isinstance(parsed.body[0], ast.Assign):
            raise EquationError(f"line {line_no}: expected assignment")
        stmt = parsed.body[0]
        if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            raise EquationError(f"line {line_no}: assignment target must be a name")
        target = stmt.targets[0].id
        if target.startswith("__") or target in _FUNCTIONS or target == "state":
            raise EquationError(f"line {line_no}: invalid assignment target {target!r}")
        expr = ast.Expression(stmt.value)
        _check_expr(expr)
        values[target] = _eval_expr(expr, values)
        assigned.add(target)

    if not assigned:
        raise EquationError("equation has no assignments")

    output_names = {
        pin.name for pin in template.pins if pin.direction is PinDirection.OUT
    }
    param_names = set(params)
    pin_names = set(input_pins)
    for name in assigned:
        if name not in output_names and name not in param_names and name not in pin_names:
            state[name] = values[name]

    return {
        pin.name: values.get(pin.name, pin.default)
        for pin in template.pins
        if pin.direction is PinDirection.OUT
    }


__all__ = ["EquationError", "clamp", "evaluate_equation"]
