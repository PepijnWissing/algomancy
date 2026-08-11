"""Lightweight scenario metadata records.

A :class:`ScenarioRecord` is the metadata-only view of a scenario: enough to
render a scenario list, poll status, and show persisted KPI values without
loading the input dataset or the run result. The SQL backend builds these at
startup (one query per table, no bulk data reads) and keeps them in sync on
every mutation; the in-memory registry derives them from its fully hydrated
``Scenario`` objects via :meth:`ScenarioRecord.from_scenario`.

Full ``Scenario`` objects are materialised lazily, only when a detail / run /
reset path needs them — see ``SqlScenarioRepository.get_by_id``.

This module lives at the package top level (not under ``persistence``) so it
carries no SQL/optional-dependency imports: it is safe to import from the
in-memory registry regardless of whether the ``[database]`` extra is installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, Optional

from .scenario import Scenario, ScenarioStatus


def build_kpi_dicts(
    kpi_factory,
    kpi_names: Iterable[str],
    values_by_name: Optional[Dict[str, Optional[float]]] = None,
) -> Dict[str, dict]:
    """Build the registry-keyed KPI serialization dict without a result.

    Instantiates fresh KPI objects via ``kpi_factory`` — which carry their
    ``name`` / ``better_when`` / ``unit`` / ``threshold`` from their templates —
    overlays any persisted ``values_by_name`` onto them, and serialises each via
    :meth:`BaseKPI.to_dict`. The output matches the ``"kpis"`` shape produced by
    :meth:`Scenario.to_dict` (``{registry_key: {name, better_when, unit, value,
    threshold}}``) so list summaries and full detail agree.
    """
    values_by_name = values_by_name or {}
    kpis = kpi_factory.create(list(kpi_names))
    out: Dict[str, dict] = {}
    for key, kpi in kpis.items():
        value = values_by_name.get(key)
        if value is not None:
            kpi.value = value
        out[key] = kpi.to_dict()
    return out


@dataclass
class ScenarioRecord:
    """Metadata-only snapshot of a scenario (no dataset, no result payload).

    ``algorithm_parameters`` and ``data_parameters`` are plain value dicts (the
    parsed parameter values). ``kpis`` is keyed by registry name, each value the
    :meth:`BaseKPI.to_dict` shape with persisted values already overlaid.
    """

    id: str
    tag: str
    input_data_key: str
    algorithm_name: str
    algorithm_parameters: Dict[str, Any] = field(default_factory=dict)
    data_parameters: Dict[str, Any] = field(default_factory=dict)
    status: ScenarioStatus = ScenarioStatus.CREATED
    progress: float = 0.0
    created_at: Optional[datetime] = None
    run_started_at: Optional[datetime] = None
    run_finished_at: Optional[datetime] = None
    result_available: bool = False
    kpis: Dict[str, dict] = field(default_factory=dict)

    @classmethod
    def from_scenario(cls, scenario: Scenario) -> "ScenarioRecord":
        """Derive a record from a fully hydrated ``Scenario``.

        Used by the in-memory registry (which only ever holds full scenarios)
        and as the eager fallback in ``ScenarioManager.list_summaries``.
        """
        algo = scenario._algorithm
        algo_params: Dict[str, Any] = {}
        params = getattr(algo, "params", None)
        if params is not None:
            try:
                algo_params = params.get_values()
            except Exception:
                algo_params = {}
        data_params: Dict[str, Any] = {}
        if scenario.data_params is not None and scenario.data_params.has_inputs():
            data_params = scenario.data_params.get_values()
        result_available = (
            scenario.status == ScenarioStatus.COMPLETE and scenario.result is not None
        )
        return cls(
            id=scenario.id,
            tag=scenario.tag,
            input_data_key=scenario.input_data_key,
            algorithm_name=getattr(algo, "name", ""),
            algorithm_parameters=algo_params,
            data_parameters=data_params,
            status=scenario.status,
            progress=float(scenario.progress or 0.0),
            result_available=result_available,
            kpis={
                k: v.to_dict() if hasattr(v, "to_dict") else v
                for k, v in scenario.kpis.items()
            },
        )

    def to_summary_dict(self) -> dict:
        """The API scenario-list wire shape."""
        return {
            "id": self.id,
            "tag": self.tag,
            "input_data_key": self.input_data_key,
            "algorithm": {
                "name": self.algorithm_name,
                "parameters": self.algorithm_parameters,
            },
            "data_parameters": self.data_parameters,
            "status": str(self.status),
            "progress": self.progress,
            "created_at": self.created_at,
            "run_started_at": self.run_started_at,
            "run_finished_at": self.run_finished_at,
            "result_available": self.result_available,
            "kpis": self.kpis,
        }
