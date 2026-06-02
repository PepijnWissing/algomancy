"""Session lifecycle endpoints.

These are the routes that operate on the SessionManager itself (list, create,
copy, rename). Routes that operate within a single session live in the other
routers and use ``Depends(get_scenario_manager)`` to resolve the session id
from the URL.

Session ids in the URL are UUIDs; the human-readable label is the mutable
``display_name`` returned in the response body.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from algomancy_scenario import SessionManager

from ..dependencies import get_session_manager, resolve_session_id
from ..schemas import (
    CopySessionRequest,
    CreateSessionRequest,
    RenameSessionRequest,
    SessionInfo,
    SessionsListResponse,
)


router = APIRouter(prefix="/sessions", tags=["sessions"])


def _build_list_response(sm: SessionManager) -> SessionsListResponse:
    return SessionsListResponse(
        sessions=[SessionInfo(**entry) for entry in sm.list_sessions()],
        default=sm.start_session_id,
    )


@router.get(
    "",
    response_model=SessionsListResponse,
    summary="List all sessions",
)
def list_sessions(
    sm: SessionManager = Depends(get_session_manager),
) -> SessionsListResponse:
    return _build_list_response(sm)


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
        sm.create_new_session(body.display_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return _build_list_response(sm)


@router.post(
    "/{session_id}/copy",
    status_code=status.HTTP_201_CREATED,
    response_model=SessionsListResponse,
    summary="Copy an existing session under a new display name",
)
def copy_session(
    session_id: str,
    body: CopySessionRequest,
    sm: SessionManager = Depends(get_session_manager),
) -> SessionsListResponse:
    resolved = resolve_session_id(sm, session_id)
    if resolved is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )
    try:
        sm.copy_session(resolved, body.new_display_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return _build_list_response(sm)


@router.patch(
    "/{session_id}",
    response_model=SessionInfo,
    summary="Rename a session (update its display_name; id is immutable)",
)
def rename_session(
    session_id: str,
    body: RenameSessionRequest,
    sm: SessionManager = Depends(get_session_manager),
) -> SessionInfo:
    resolved = resolve_session_id(sm, session_id)
    if resolved is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )
    try:
        sm.rename_session(resolved, body.display_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return SessionInfo(id=resolved, display_name=sm.get_display_name(resolved))
