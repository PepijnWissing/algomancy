from __future__ import annotations

from fastapi import HTTPException, Path, Request

from algomancy_scenario import ScenarioManager, SessionManager


def get_session_manager(request: Request) -> SessionManager:
    """Return the SessionManager attached to the app at build time."""
    sm = getattr(request.app.state, "session_manager", None)
    if sm is None:
        # Shouldn't happen unless the app was constructed outside ApiLauncher.build.
        raise HTTPException(status_code=500, detail="SessionManager not configured")
    return sm


def resolve_session_id(sm: SessionManager, session_id_or_name: str) -> str | None:
    """Return the canonical UUID for a session identifier from a URL.

    Accepts either the UUID directly or the current ``display_name`` as a
    soft-compatibility alias. Returns ``None`` when neither resolves.
    """
    if sm.has_session(session_id_or_name):
        return session_id_or_name
    return sm.resolve_id_by_display_name(session_id_or_name)


def get_scenario_manager(
    request: Request,
    session_id: str = Path(..., description="Session identifier"),
) -> ScenarioManager:
    """Resolve {session_id} from the URL to a ScenarioManager. 404 on miss.

    The canonical form is the session UUID. As a soft-compatibility alias,
    the resolver also accepts a session's current ``display_name`` — useful
    for casual single-tenant deployments and for clients migrating from
    pre-M14 algomancy where session ids and names were the same string.
    Authoritative clients should always use the UUID returned by
    ``GET /sessions``.
    """
    sm = get_session_manager(request)
    resolved_id = resolve_session_id(sm, session_id)
    if resolved_id is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return sm.get_scenario_manager(resolved_id)
