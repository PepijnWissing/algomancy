"""Convert a ``BaseParameterSet`` into a frontend-friendly JSON descriptor.

``BaseParameterSet.serialize()`` only returns the current values (as a JSON
string), which is not enough for a remote GUI that needs to render a form for
an algorithm it has never seen before. This module produces a richer schema
that exposes types, defaults, choices, and numeric bounds for every parameter.

The shape is intentionally narrow — only fields the existing GUI already
renders are surfaced. We do not invent constraints that the framework doesn't
already enforce.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from algomancy_utils.baseparameterset import (
    BaseParameterSet,
    BooleanParameter,
    EnumParameter,
    FloatParameter,
    IntegerParameter,
    IntervalParameter,
    MultiEnumParameter,
    NumericParameter,
    StringParameter,
    TimeParameter,
    TypedParameter,
)


def _safe_jsonable(value: Any) -> Any:
    """Convert framework-typed values (datetimes, tuples) to JSON primitives."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_safe_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_safe_jsonable(v) for v in value]
    return value


def describe_parameter(param: TypedParameter) -> Dict[str, Any]:
    """Return a JSON-able dict describing a single parameter."""
    out: Dict[str, Any] = {
        "name": param.name,
        "type": str(param.parameter_type),
        "required": bool(param.required),
        "value": _safe_jsonable(param.value),
    }

    if isinstance(param, (IntegerParameter, FloatParameter, NumericParameter)):
        out["default"] = _safe_jsonable(param.default)
        out["min"] = param.min
        out["max"] = param.max
    elif isinstance(param, (EnumParameter, MultiEnumParameter)):
        out["choices"] = list(param.choices)
    elif isinstance(param, (StringParameter, BooleanParameter)):
        out["default"] = _safe_jsonable(param.default)
    elif isinstance(param, TimeParameter):
        out["default"] = _safe_jsonable(param.default)
    elif isinstance(param, IntervalParameter):
        out["default"] = [
            _safe_jsonable(param.default_start),
            _safe_jsonable(param.default_end),
        ]

    return out


def describe_parameter_set(params: BaseParameterSet) -> Dict[str, Any]:
    """Return a JSON-able dict describing every parameter in a set."""
    described: List[Dict[str, Any]] = [
        describe_parameter(p) for p in params.get_parameters().values()
    ]
    return {"name": params.name, "parameters": described}
