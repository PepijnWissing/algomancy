(api-ref)=
# HTTP API

The `algomancy-api` package exposes the same scenario- and data-management
surface used by the Dash GUI as an HTTP service. A remote process —
browser SPA, native desktop app, another Python client — can drive an
Algomancy backend over JSON-over-HTTP instead of importing it in-process.

The shape mirrors the GUI:

- An [`ApiConfiguration`](#configuration) carries the same domain wiring
  (ETL factory, algorithm/KPI templates, schemas, data paths) as
  `AppConfig.core`.
- An [`ApiLauncher`](#launching) turns that configuration into a
  [FastAPI](https://fastapi.tiangolo.com/) app and serves it with uvicorn.

```{toctree}
:maxdepth: 1

api/details
api/extending_the_api
```

```{tip}
Once a server is running, point your browser at `/docs` for the interactive
Swagger UI generated from the live OpenAPI schema. Every endpoint listed below
is discoverable there.
```

## Launching

```{code-block} python
:caption: myapp/api.py
from algomancy_api import ApiConfiguration, ApiLauncher
from algomancy_data import DataSource

from myapp.etl import MyETLFactory
from myapp.templates import kpis, algorithms
from myapp.schemas import all_schemas


cfg = ApiConfiguration(
    etl_factory=MyETLFactory,
    kpis=kpis,
    algorithms=algorithms,
    schemas=all_schemas,
    data_object_type=DataSource,
    has_persistent_state=True,
    data_path="data",
    autocreate=False,
    autorun=False,
    host="127.0.0.1",
    port=8051,
)

app = ApiLauncher.build(cfg)
ApiLauncher.run(app)  # blocks; host/port come from cfg
```

`ApiLauncher.build` accepts an `ApiConfiguration`, a bare `CoreConfig`, or a
plain dict with the same keys. It returns a standard `FastAPI` instance — for
production deployments you can hand that to your own uvicorn / gunicorn
process manager instead of using `ApiLauncher.run`.

To try the API quickly against the bundled example wiring (data lives in
`./example/data`):

```{code-block} python
from algomancy_api import ApiLauncher
from algomancy_api.example import build_example_config

ApiLauncher.run(ApiLauncher.build(build_example_config()))
```

(api-configuration-ref)=
## Configuration

`ApiConfiguration` extends `CoreConfig` (see the
{ref}`Scenario reference <scenario-package-ref>`) with HTTP-specific fields. Inherited
fields like `etl_factory`, `kpis`, `algorithms`, `schemas`,
`data_object_type`, `data_path`, `has_persistent_state`, `autocreate`,
`autorun`, and `title` behave exactly as they do for the GUI.

| Field | Type | Default | Notes |
|---|---|---|---|
| `host` | `str` | `"127.0.0.1"` | Bind address |
| `port` | `int` | `8051` | Bind port |
| `prefix` | `str` | `"/api/v1"` | URL prefix for all routes (must start with `/`) |
| `cors_origins` | `list[str]` | `[]` | Allowed CORS origins; empty disables CORS middleware |

Routes are always scoped by session under `/sessions/{session_id}/...`. The
`SessionManager` auto-creates a default `"main"` session when none exists yet,
so single-tenant deployments still have a working URL shape.

## Sessions

The API exposes routes under `/sessions/{session_id}/...`. A session is a
self-contained `ScenarioManager` with its own data and scenarios — useful for
serving multiple users or experiment workspaces from one process.

**Identity.** Every session has a stable UUID `id` and a mutable
`display_name`. The URL path uses the UUID; the `display_name` is what you
show in UIs. For convenience, the URL path also accepts a session's current
`display_name` as a soft-compat alias. Authoritative clients should always use
the UUID returned by `GET /sessions`.

| Verb | Path | Description |
|---|---|---|
| `GET` | `/sessions` | List `[{id, display_name}, ...]` and the default id |
| `POST` | `/sessions` | Create — body `{"display_name": "..."}` |
| `POST` | `/sessions/{sid}/copy` | Copy — body `{"new_display_name": "..."}` |
| `PATCH` | `/sessions/{sid}` | Rename — body `{"display_name": "..."}` (id stays) |
| `DELETE` | `/sessions/{sid}` | Delete a session and all its scenarios, runs, KPIs, and data |

## Algorithm + KPI discovery

These endpoints let a remote frontend render a scenario-creation form for an
algorithm it has never seen before.

| Verb | Path | Description |
|---|---|---|
| `GET` | `/sessions/{sid}/algorithms` | List algorithm template names |
| `GET` | `/sessions/{sid}/algorithms/{name}/parameters` | Per-parameter descriptors |
| `GET` | `/sessions/{sid}/kpis` | List KPI template names |

## Scenarios

CRUD plus the run-and-poll lifecycle. Run is fire-and-forget; clients poll
`/status` for progress.

| Verb | Path | Description |
|---|---|---|
| `GET` | `/sessions/{sid}/scenarios` | List scenarios (full `to_dict()`) |
| `POST` | `/sessions/{sid}/scenarios` | Create scenario — body `{tag, dataset_key, algo_name, algo_params}` |
| `GET` | `/sessions/{sid}/scenarios/{id}` | Full scenario including KPIs + result |
| `DELETE` | `/sessions/{sid}/scenarios/{id}` | Remove scenario |
| `POST` | `/sessions/{sid}/scenarios/{id}/run` | Enqueue for processing (returns `202`) |
| `GET` | `/sessions/{sid}/scenarios/{id}/status` | Lightweight `{id, tag, status, progress}` for polling |
| `GET` | `/sessions/{sid}/processing` | The scenario currently processing, or `null` |

## Data management

| Verb | Path | Description |
|---|---|---|
| `GET` | `/sessions/{sid}/data` | List dataset keys |
| `GET` | `/sessions/{sid}/data/{key}` | Parsed JSON for a dataset |
| `DELETE` | `/sessions/{sid}/data/{key}` | Remove a dataset |
| `POST` | `/sessions/{sid}/data/{key}/derive` | Derive a new dataset — body `{"new_key": "..."}` |
| `POST` | `/sessions/{sid}/data/from-json` | Add a dataset from a `DataSource.to_json()` payload |
| `POST` | `/sessions/{sid}/etl` | Run ETL over an uploaded multipart bundle |

Deleting a dataset that is referenced by a scenario returns `409`. To delete
the underlying data, delete its referencing scenarios first.

## Error mapping

The API translates framework exceptions to HTTP status codes consistently:

| Exception | HTTP | Source |
|---|---|---|
| `ValueError` | `400` | Generic bad input |
| `ParameterError` | `400` | Out-of-range / wrong-type parameter values |
| `AssertionError` | `409` | Framework precondition failure (e.g. deleting a dataset used by a scenario) |
| Manual route raises | `404` / `409` | Explicit `HTTPException` from the route — used for unknown lookups and name conflicts |
| Anything else | `500` | Unexpected; logged with a traceback |

```{note}
The error response shape is consistent: `{"detail": "<message>"}`. Branch on
the HTTP status code, not the message text — messages are written for humans
and may change between versions.
```

## Cross-references

- {ref}`Scenario reference <scenario-package-ref>` — `CoreConfig`, `ScenarioManager`, `SessionManager`.
- {ref}`Data reference <data-ref>` — `DataSource`, `ETLFactory`, `Schema`.
- {ref}`Endpoint reference <api-endpoint-details-ref>` — full per-endpoint documentation.
- [Extending the API](api/extending_the_api) — attaching custom routes to the built app.
