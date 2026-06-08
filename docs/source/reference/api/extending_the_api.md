# Extending the API with custom endpoints

`algomancy-api` exposes Algomancy's scenario-management surface as a FastAPI
application. After `ApiLauncher.build()` returns that application, it is a
plain `FastAPI` instance — you can attach any additional routers, middleware,
or routes to it using standard FastAPI patterns.

This page explains how to do that cleanly.

---

## How the built-in API is assembled

`ApiLauncher.build()` performs three steps that are worth understanding before
you extend the result:

1. It creates a `SessionManager` from your `ApiConfiguration` and stores it on
   `app.state.session_manager`.
2. It installs global exception handlers (`install_exception_handlers`) and,
   when `cors_origins` is non-empty, CORS middleware.
3. It registers four built-in routers — `sessions`, `algorithms`, `scenarios`,
   and `data` — all scoped under the configured `prefix` (default
   `/api/v1`).

Your code runs **after** `build()` returns, so the `app.state` object is
already populated and the built-in routes are already in place. You add your
own routes on top.

---

## The recommended pattern

The cleanest approach is to define your custom routes in a dedicated
`APIRouter`, then include it in the app returned by `build()`.

```python
# my_project/api/routers/results.py

from fastapi import APIRouter, Depends, HTTPException, status
from algomancy_scenario import ScenarioManager
from algomancy_api.dependencies import get_scenario_manager

router = APIRouter(
    prefix="/sessions/{session_id}",
    tags=["results"],
)


@router.get(
    "/scenarios/{scenario_id}/export",
    summary="Export scenario results as a flat CSV-compatible dict",
)
def export_results(
    scenario_id: str,
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> dict:
    scenario = sm.get_by_id(scenario_id)
    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario_id}' not found",
        )
    # Your domain logic here.
    return {"scenario_id": scenario_id, "rows": []}
```

Then in your entry point, include the router after calling `build()`:

```python
# my_project/main.py

from algomancy_api import ApiConfiguration, ApiLauncher
from my_project.api.routers import results

cfg = ApiConfiguration(
    # ... your CoreConfig arguments ...
    host="127.0.0.1",
    port=8051,
    prefix="/api/v1",
)

app = ApiLauncher.build(cfg)

# Attach your router under the same prefix as the built-in routes.
app.include_router(results.router, prefix=cfg.prefix)

if __name__ == "__main__":
    ApiLauncher.run(app, host=cfg.host, port=cfg.port)
```

The custom endpoints now appear in the same OpenAPI schema at `/docs`.

---

## Using the built-in dependencies

`algomancy_api.dependencies` exports two `Depends`-compatible callables that
resolve the session and scenario layers from the URL. You should reuse them
rather than accessing `app.state` directly.

```{list-table}
:header-rows: 1
:widths: 30 70

* - Callable
  - What it provides
* - `get_session_manager(request)`
  - The `SessionManager` attached to the app. Raises HTTP 500 if the app was
    not built through `ApiLauncher.build()`.
* - `get_scenario_manager(request, session_id)`
  - The `ScenarioManager` for the `{session_id}` path parameter. Raises HTTP
    404 when the session does not exist. Accepts either the UUID or the
    session's `display_name` as the identifier.
```

Both are used in the example above via `Depends(get_scenario_manager)`. If
your endpoint operates at the session level rather than on a specific scenario,
use `get_session_manager` instead:

```python
from algomancy_scenario import SessionManager
from algomancy_api.dependencies import get_session_manager

@router.get("/summary")
def session_summary(
    sm: SessionManager = Depends(get_session_manager),
) -> dict:
    return {"session_count": len(sm.list_sessions())}
```

---

## Adding session-independent routes

Not every endpoint needs a session prefix. For top-level or meta routes, omit
the prefix on the router and include it without the `prefix` argument:

```python
# my_project/api/routers/meta.py

from fastapi import APIRouter

router = APIRouter(tags=["meta"])


@router.get("/version")
def version() -> dict:
    return {"app": "my-project", "version": "1.0.0"}
```

```python
# main.py (continued)

from my_project.api.routers import meta

app.include_router(meta.router)  # No prefix — mounts at /version
```

---

## Accessing app state in non-route code

If you need the `SessionManager` outside a route handler (for example, in a
startup hook or a background task), read it from `app.state`:

```python
from algomancy_scenario import SessionManager

@app.on_event("startup")
async def on_startup() -> None:
    sm: SessionManager = app.state.session_manager
    # e.g. pre-load a default dataset
```

:::{note}
`app.state.config` holds the `ApiConfiguration` object, and
`app.state.session_manager` holds the `SessionManager`. Both are set by
`ApiLauncher.build()` before control returns to your code.
:::

---

## Defining request and response schemas

Algomancy's built-in request/response shapes live in `algomancy_api.schemas`
and are all plain Pydantic models. Define your own the same way:

```python
from pydantic import BaseModel, Field
from typing import Any, Dict, List


class ExportRequest(BaseModel):
    include_kpis: bool = Field(default=True)
    columns: List[str] = Field(default_factory=list)


class ExportResponse(BaseModel):
    scenario_id: str
    rows: List[Dict[str, Any]]
```

Use them as the body type and `response_model` on your route:

```python
@router.post(
    "/scenarios/{scenario_id}/export",
    response_model=ExportResponse,
)
def export(
    scenario_id: str,
    body: ExportRequest,
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> ExportResponse:
    ...
```

---

## Error handling

The global exception handlers installed by `install_exception_handlers` map
`AssertionError` to HTTP 409 and `ValueError` to HTTP 400. Any exception your
route raises that falls into those types will be caught automatically.

For lookup failures, raise `HTTPException` explicitly — as the built-in routers
do — so the status code is semantically correct:

```python
from fastapi import HTTPException, status

scenario = sm.get_by_id(scenario_id)
if scenario is None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Scenario '{scenario_id}' not found",
    )
```

Do not rely on domain `KeyError` propagating to a 404: the global handler does
not map `KeyError` to avoid turning unrelated errors in user code into
misleading 404 responses.

---

## Summary

| Step | What to do |
|---|---|
| Define routes | Create an `APIRouter` in your project |
| Access session context | `Depends(get_scenario_manager)` or `Depends(get_session_manager)` from `algomancy_api.dependencies` |
| Register routes | `app.include_router(router, prefix=cfg.prefix)` after `ApiLauncher.build()` |
| Define schemas | Plain Pydantic `BaseModel` subclasses |
| Signal errors | `raise HTTPException(...)` for lookup failures; let `ValueError`/`AssertionError` bubble for the global handler |
