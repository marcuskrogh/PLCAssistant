"""Safe math-expression sandbox for plant dynamics (SWD-144).

AST whitelist only — no imports, attribute access, or arbitrary calls.
"""

from __future__ import annotations

import ast
import math
from typing import Callable, Mapping

_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod)
_ALLOWED_UNARY = (ast.UAdd, ast.USub)
_ALLOWED_FUNCS: dict[str, Callable[..., float]] = {
    "sqrt": math.sqrt,
    "exp": math.exp,
    "min": min,
    "max": max,
    "abs": abs,
    "clamp": lambda value, lo, hi: lo if value < lo else hi if value > hi else float(value),
}


class ExpressionError(ValueError):
    """Raised when an expression is invalid or unsafe."""


def _check_node(node: ast.AST) -> None:
    if isinstance(node, ast.Expression):
        _check_node(node.body)
        return
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return
        raise ExpressionError(f"unsupported constant: {node.value!r}")
    if isinstance(node, ast.Name):
        if not node.id.isidentifier():
            raise ExpressionError(f"invalid name: {node.id!r}")
        return
    if isinstance(node, ast.BinOp):
        if not isinstance(node.op, _ALLOWED_BINOPS):
            raise ExpressionError(f"unsupported operator: {type(node.op).__name__}")
        _check_node(node.left)
        _check_node(node.right)
        return
    if isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, _ALLOWED_UNARY):
            raise ExpressionError(f"unsupported unary: {type(node.op).__name__}")
        _check_node(node.operand)
        return
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ExpressionError("only simple function calls are allowed")
        if node.func.id not in _ALLOWED_FUNCS:
            raise ExpressionError(f"function not allowed: {node.func.id!r}")
        if node.keywords:
            raise ExpressionError("keyword arguments are not allowed")
        for arg in node.args:
            _check_node(arg)
        return
    if isinstance(node, ast.Compare):
        # Disallow comparisons in RHS expressions for v1 clarity.
        raise ExpressionError("comparisons are not allowed")
    raise ExpressionError(f"unsupported syntax: {type(node).__name__}")


def compile_expr(source: str) -> Callable[[Mapping[str, float]], float]:
    """Compile a math expression into ``f(ctx) -> float``.

    Names are resolved from ``ctx`` (state / inputs / params). Missing names
    raise ``ExpressionError`` at evaluation time.
    """
    text = str(source or "").strip()
    if not text:
        raise ExpressionError("empty expression")
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as err:
        raise ExpressionError(f"syntax error: {err}") from err
    _check_node(tree)

    def _eval(node: ast.AST, ctx: Mapping[str, float]) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body, ctx)
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id not in ctx:
                raise ExpressionError(f"unknown name: {node.id!r}")
            return float(ctx[node.id])
        if isinstance(node, ast.UnaryOp):
            value = _eval(node.operand, ctx)
            if isinstance(node.op, ast.UAdd):
                return +value
            return -value
        if isinstance(node, ast.BinOp):
            left = _eval(node.left, ctx)
            right = _eval(node.right, ctx)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Pow):
                return left**right
            if isinstance(node.op, ast.Mod):
                return left % right
        if isinstance(node, ast.Call):
            assert isinstance(node.func, ast.Name)
            fn = _ALLOWED_FUNCS[node.func.id]
            args = [_eval(arg, ctx) for arg in node.args]
            return float(fn(*args))
        raise ExpressionError(f"unsupported syntax: {type(node).__name__}")

    def evaluate(ctx: Mapping[str, float]) -> float:
        return float(_eval(tree, ctx))

    return evaluate


def eval_expr(source: str, ctx: Mapping[str, float]) -> float:
    return compile_expr(source)(ctx)


__all__ = ["ExpressionError", "compile_expr", "eval_expr"]
