"""Map framework exceptions to HTTP status codes.

Route handlers should call ``ScenarioManager``/``SessionManager`` methods
directly and let domain exceptions bubble. These handlers translate them so
handlers stay terse.

Concrete situations that drive the mapping:

* ``AssertionError`` — defensive guard in the manager (e.g. deleting data that
  is referenced by a scenario). These are precondition failures → 409.
* ``ValueError`` — bad input. The one ambiguous case is ``create_scenario``
  raising ``ValueError`` when a tag already exists; the scenarios router handles
  that explicitly and raises ``HTTPException(409)``. The fallback here is 400.

Lookup misses (unknown session, unknown algorithm template, unknown data key)
are NOT translated globally — every framework lookup that raises ``KeyError``
is wrapped in the route or dependency that called it, so we don't accidentally
turn an unrelated KeyError deep in user code into a misleading 404.
"""

from __future__ import annotations

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


_log = logging.getLogger("algomancy_api")


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AssertionError)
    async def _handle_assertion_error(_: Request, exc: AssertionError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc) or "Conflict"})

    @app.exception_handler(ValueError)
    async def _handle_value_error(_: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def _handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        _log.error("Unhandled exception: %s\n%s", exc, traceback.format_exc())
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
