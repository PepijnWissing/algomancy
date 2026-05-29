"""Session lifecycle endpoints.

These are the routes that operate on the SessionManager itself (list, create,
copy). Routes that operate within a single session live in the other routers
and use ``Depends(get_scenario_manager)`` to resolve the session id from the
URL.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from algomancy_scenario import SessionManager

from ..dependencies import get_session_manager
from ..schemas import (
    CopySessionRequest,
    CreateSessionRequest,
    SessionsListResponse,
)


router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get(
    "",
    response_model=SessionsListResponse,
    summary="List all sessions",
)
def list_sessions(
    sm: SessionManager = Depends(get_session_manager),
) -> SessionsListResponse:
    return SessionsListResponse(
        sessions=sm.sessions_names,
        default=sm.start_session_name,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SessionsListResponse,
    summary="Create a new empty session",
)
def create_session(
    body: CreateSessionRequest,
    sm: SessionManager = Depends(get_session_manager),
) -> SessionsListResponse:
    try:
        sm.create_new_session(body.name)
    except ValueError as exc:
        # Includes both name-validation failures and duplicate-name failures.
        # 409 reads as "conflict with current state" — matches duplicate; the
        # invalid-name case also fails a precondition. Either way, the client
        # needs to change the name before retrying.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return SessionsListResponse(
        sessions=sm.sessions_names,
        default=sm.start_session_name,
    )


@router.post(
    "/{session_id}/copy",
    status_code=status.HTTP_201_CREATED,
    response_model=SessionsListResponse,
    summary="Copy an existing session under a new name",
)
def copy_session(
    session_id: str,
    body: CopySessionRequest,
    sm: SessionManager = Depends(get_session_manager),
) -> SessionsListResponse:
    if not sm.has_session(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )
    try:
        sm.copy_session(session_id, body.new_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return SessionsListResponse(
        sessions=sm.sessions_names,
        default=sm.start_session_name,
    )
