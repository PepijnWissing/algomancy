"""Pydantic models for request bodies and response shapes.

Domain objects (Scenario, BaseAlgorithm, BaseKPI, ...) already expose
``to_dict()`` and the route handlers return those dicts directly. Pydantic is
used here mostly to give incoming request bodies a stable shape and to make
the OpenAPI schema useful for frontend codegen — not to mirror the domain.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---- Sessions --------------------------------------------------------------


class CreateSessionRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        description="Identifier for the new session. Must be a single safe path "
        "segment (no separators, no '..', no drive prefix).",
    )


class CopySessionRequest(BaseModel):
    new_name: str = Field(
        ...,
        min_length=1,
        description="Identifier for the destination session. Same restrictions "
        "as session creation.",
    )


class SessionsListResponse(BaseModel):
    sessions: List[str]
    default: str


# ---- Algorithms / KPIs -----------------------------------------------------


class AlgorithmsListResponse(BaseModel):
    algorithms: List[str]


class KpisListResponse(BaseModel):
    kpis: List[str]


# ---- Scenarios -------------------------------------------------------------


class CreateScenarioRequest(BaseModel):
    tag: str = Field(..., min_length=1, description="Unique scenario tag")
    dataset_key: str = Field(..., min_length=1, description="Input dataset key")
    algo_name: str = Field(..., min_length=1, description="Algorithm template name")
    algo_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameter values keyed by parameter name. "
        "Omit or set to null to use defaults.",
    )


class ScenarioStatusResponse(BaseModel):
    """Lightweight status shape for high-frequency polling.

    Excludes algorithm/KPI/result payloads — use the full scenario endpoint when
    you need those.
    """

    id: str
    tag: str
    status: str
    progress: float
