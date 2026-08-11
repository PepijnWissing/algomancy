"""Pydantic models for request bodies and response shapes.

Domain objects (Scenario, BaseAlgorithm, BaseKPI, ...) already expose
``to_dict()`` and the route handlers return those dicts directly. Pydantic is
used here mostly to give incoming request bodies a stable shape and to make
the OpenAPI schema useful for frontend codegen — not to mirror the domain.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---- Sessions --------------------------------------------------------------


class CreateSessionRequest(BaseModel):
    display_name: str = Field(
        ...,
        min_length=1,
        description="Human-readable name for the new session. Display only; "
        "the server generates a UUID id and returns it.",
    )


class CopySessionRequest(BaseModel):
    new_display_name: str = Field(
        ...,
        min_length=1,
        description="Human-readable name for the destination session.",
    )


class RenameSessionRequest(BaseModel):
    display_name: str = Field(
        ...,
        min_length=1,
        description="New human-readable name for the session.",
    )


class SessionInfo(BaseModel):
    id: str = Field(..., description="Stable UUID identifying the session.")
    display_name: str = Field(..., description="Mutable label shown in UIs.")


class SessionsListResponse(BaseModel):
    sessions: List[SessionInfo]
    default: str = Field(..., description="UUID of the session selected by default.")


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
    data_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Values for the data source's declared parameters "
        "(see ``BaseDataSource.initialize_data_parameters``). "
        "Omit or set to null when the dataset declares none.",
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


class KpiSummary(BaseModel):
    """A KPI's serialized value in a scenario summary.

    Mirrors ``BaseKPI.to_dict()``. ``value`` carries the persisted measurement
    (or the framework's uncomputed sentinel when the scenario has not run).
    """

    name: str
    better_when: str
    unit: str
    value: Optional[float] = None
    threshold: Optional[float] = None


class AlgorithmSummary(BaseModel):
    name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ScenarioSummary(BaseModel):
    """Lightweight scenario metadata for the list view.

    Returned by ``GET /sessions/{id}/scenarios`` without hydrating the input
    dataset or the run result. KPI values come from persisted measurements. Use
    ``GET .../scenarios/{id}`` for the fully hydrated payload.
    """

    id: str
    tag: str
    input_data_key: str
    algorithm: AlgorithmSummary
    data_parameters: Dict[str, Any] = Field(default_factory=dict)
    status: str
    progress: float = 0.0
    created_at: Optional[datetime] = None
    run_started_at: Optional[datetime] = None
    run_finished_at: Optional[datetime] = None
    result_available: bool = False
    kpis: Dict[str, KpiSummary] = Field(default_factory=dict)


# ---- Data management -------------------------------------------------------


class DataKeysResponse(BaseModel):
    keys: List[str]


class DeriveDataRequest(BaseModel):
    new_key: str = Field(
        ..., min_length=1, description="Identifier for the derived dataset"
    )


class EtlResponse(BaseModel):
    """Outcome of an ETL run."""

    dataset_name: str
    success: bool
    keys: List[str]
