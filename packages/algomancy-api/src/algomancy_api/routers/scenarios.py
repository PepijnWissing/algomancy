"""Scenario lifecycle endpoints.

CRUD + run + poll. Each scenario is owned by exactly one session; the session
id comes from the URL path and is resolved into a ``ScenarioManager`` by the
``get_scenario_manager`` dependency.

Error mapping notes:

* Unknown algorithm or dataset is preempted with a 404 in this layer (rather
  than letting the AssertionError bubble through the global handler) so that
  the response semantically distinguishes "you referenced something that
  doesn't exist" from "you referenced something that exists but is in a
  conflicting state" (409).
* Duplicate tag → 409 (ValueError from ``create_scenario``).
* Bad parameter values → 400 (``ParameterError`` from BaseParameterSet, which
  is not a ValueError so it doesn't hit the global handler).
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from algomancy_scenario import ScenarioManager, ScenarioStatus
from algomancy_utils.baseparameterset import ParameterError

from ..dependencies import get_scenario_manager
from ..schemas import CreateScenarioRequest, ScenarioStatusResponse


router = APIRouter(
    prefix="/sessions/{session_id}",
    tags=["scenarios"],
)


def _to_status_response(scenario) -> ScenarioStatusResponse:
    return ScenarioStatusResponse(
        id=scenario.id,
        tag=scenario.tag,
        status=str(scenario.status),
        progress=float(scenario.progress or 0.0),
    )


def _resolve_scenario_or_404(sm: ScenarioManager, scenario_id: str):
    scenario = sm.get_by_id(scenario_id)
    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario_id}' not found",
        )
    return scenario


@router.get("/scenarios", summary="List scenarios in this session")
def list_scenarios(
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> List[dict]:
    return [s.to_dict() for s in sm.list_scenarios()]


@router.post(
    "/scenarios",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new scenario",
)
def create_scenario(
    body: CreateScenarioRequest,
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> dict:
    if body.algo_name not in sm.available_algorithms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Algorithm '{body.algo_name}' not found",
        )
    if body.dataset_key not in sm.get_data_keys():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{body.dataset_key}' not found",
        )

    try:
        scenario = sm.create_scenario(
            tag=body.tag,
            dataset_key=body.dataset_key,
            algo_name=body.algo_name,
            algo_params=body.algo_params or {},
            data_params=body.data_params or {},
        )
    except ValueError as exc:
        # Duplicate tag.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ParameterError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return scenario.to_dict()


@router.get("/scenarios/{scenario_id}", summary="Get one scenario by id")
def get_scenario(
    scenario_id: str,
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> dict:
    return _resolve_scenario_or_404(sm, scenario_id).to_dict()


@router.delete(
    "/scenarios/{scenario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a scenario",
)
def delete_scenario(
    scenario_id: str,
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> None:
    if not sm.delete_scenario(scenario_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario_id}' not found",
        )
    return None


@router.post(
    "/scenarios/{scenario_id}/run",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue a scenario for processing",
)
def run_scenario(
    scenario_id: str,
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> dict:
    scenario = _resolve_scenario_or_404(sm, scenario_id)
    if scenario.status != ScenarioStatus.CREATED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Scenario '{scenario_id}' cannot be run from status "
                f"'{scenario.status}'. Reset it first to re-run."
            ),
        )
    sm.process_scenario_async(scenario)
    return scenario.to_dict()


@router.post(
    "/scenarios/{scenario_id}/reset",
    summary="Reset a scenario's status and clear its result",
)
def reset_scenario(
    scenario_id: str,
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> dict:
    scenario = _resolve_scenario_or_404(sm, scenario_id)
    if scenario.status in (ScenarioStatus.QUEUED, ScenarioStatus.PROCESSING):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Scenario '{scenario_id}' cannot be reset while in status "
                f"'{scenario.status}'."
            ),
        )
    sm.refresh_scenario(scenario_id)
    return scenario.to_dict()


@router.get(
    "/scenarios/{scenario_id}/status",
    response_model=ScenarioStatusResponse,
    summary="Lightweight status + progress for polling",
)
def scenario_status(
    scenario_id: str,
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> ScenarioStatusResponse:
    scenario = _resolve_scenario_or_404(sm, scenario_id)
    return _to_status_response(scenario)


@router.get(
    "/processing",
    summary="The scenario currently being processed (or null if idle)",
)
def currently_processing(
    sm: ScenarioManager = Depends(get_scenario_manager),
):
    s = sm.currently_processing
    if s is None:
        return None
    return s.to_dict()
