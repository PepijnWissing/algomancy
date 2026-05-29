"""Map framework exceptions to HTTP status codes.

Route handlers should call ``ScenarioManager``/``SessionManager`` methods
directly and let domain exceptions bubble. These handlers translate them so
handlers stay terse.

Concrete situations that drive the mapping:

* ``KeyError`` — unknown session, unknown algorithm template, unknown data key.
  These are always "not found" situations → 404.
* ``AssertionError`` — defensive guard in the manager (e.g. deleting data that
  is referenced by a scenario). These are precondition failures → 409.
* ``ValueError`` — bad input. The one ambiguous case is ``create_scenario``
  raising ``ValueError`` when a tag already exists; the scenarios router handles
  that explicitly and raises ``HTTPException(409)``. The fallback here is 400.
"""

from __future__ import annotations

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


_log = logging.getLogger("algomancy_api")


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(KeyError)
    async def _handle_key_error(_: Request, exc: KeyError) -> JSONResponse:
        # KeyError's str() includes quotes around the key; .args[0] is cleaner.
        msg = exc.args[0] if exc.args else "Not found"
        return JSONResponse(status_code=404, content={"detail": str(msg)})

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
