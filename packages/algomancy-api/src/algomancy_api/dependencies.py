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


def get_scenario_manager(
    request: Request,
    session_id: str = Path(..., description="Session identifier"),
) -> ScenarioManager:
    """Resolve {session_id} from the URL to a ScenarioManager. 404 on miss."""
    sm = get_session_manager(request)
    try:
        return sm.get_scenario_manager(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
