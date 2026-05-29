(api-ref)=
# HTTP API

The `algomancy-api` package exposes the same scenario- and data-management
surface used by the Dash GUI and the CLI shell as an HTTP service. A remote
process — browser SPA, native desktop app, another Python client — can drive
an Algomancy backend over JSON-over-HTTP instead of importing it in-process.

The shape mirrors the other frontends:

- An [`ApiConfiguration`](#configuration) carries the same domain wiring
  (ETL factory, algorithm/KPI templates, schemas, data paths) as
  `CliConfiguration` and `AppConfig.core`.
- An [`ApiLauncher`](#launching) turns that configuration into a
  [FastAPI](https://fastapi.tiangolo.com/) app and serves it with uvicorn.
- A console script `algomancy-api` accepts a `--config-callback module:fn`
  that returns an `ApiConfiguration`, identical to how `algomancy-cli` is
  bootstrapped.

```{tip}
Once a server is running, point your browser at `/docs` for the interactive
Swagger UI generated from the live OpenAPI schema. Every endpoint listed below
is discoverable there.
```

## Launching

### As a console script
```bash
# the bundled example wiring (uses ./example/data)
algomancy-api --example

# your own application
algomancy-api --config-callback myapp.api:make_config

# override host / port from the config
algomancy-api --example --host 0.0.0.0 --port 9000
```

The callback must be a zero-argument function returning an `ApiConfiguration`:
```{code-block} python
:caption: myapp/api.py
from algomancy_api import ApiConfiguration
from algomancy_data import DataSource

from myapp.etl import MyETLFactory
from myapp.templates import kpi_templates, algorithm_templates
from myapp.schemas import all_schemas


def make_config() -> ApiConfiguration:
    return ApiConfiguration(
        etl_factory=MyETLFactory,
        kpi_templates=kpi_templates,
        algo_templates=algorithm_templates,
        schemas=all_schemas,
        data_object_type=DataSource,
        has_persistent_state=True,
        data_path="data",
        use_sessions=True,
        autocreate=False,
        autorun=False,
        host="127.0.0.1",
        port=8051,
    )
```

### Programmatically
```{code-block} python
from algomancy_api import ApiConfiguration, ApiLauncher

cfg = ApiConfiguration(...)
app = ApiLauncher.build(cfg)
ApiLauncher.run(app)  # blocks; host/port come from cfg
```

`ApiLauncher.build` accepts an `ApiConfiguration`, a bare `CoreConfig`, or a
plain dict with the same keys. It returns a standard `FastAPI` instance — for
production deployments you can hand that to your own uvicorn / gunicorn
process manager instead of using `ApiLauncher.run`.

(api-configuration-ref)=
## Configuration

`ApiConfiguration` extends `CoreConfig` (see the
{ref}`Scenario reference <scenario-package-ref>`) with HTTP-specific fields. Inherited
fields like `etl_factory`, `kpi_templates`, `algo_templates`, `schemas`,
`data_object_type`, `data_path`, `has_persistent_state`, `use_sessions`,
`autocreate`, `autorun`, and `title` behave exactly as they do for the GUI
and CLI.

| Field | Type | Default | Notes |
|---|---|---|---|
| `host` | `str` | `"127.0.0.1"` | Bind address |
| `port` | `int` | `8051` | Bind port |
| `prefix` | `str` | `"/api/v1"` | URL prefix for all routes (must start with `/`) |
| `cors_origins` | `list[str]` | `[]` | Allowed CORS origins; empty disables CORS middleware |

When `use_sessions=False` the API still wraps the underlying manager in a
`SessionManager`, but only the default `"main"` session is registered.
This keeps the URL shape (`/sessions/{session_id}/...`) consistent across
configurations.

## Sessions

`algomancy-api` always exposes routes under `/sessions/{session_id}/...`. A
session is a self-contained `ScenarioManager` with its own data and
scenarios — useful for serving multiple users or experiment workspaces from
one process.

| Verb | Path | Description |
|---|---|---|
| `GET` | `/sessions` | List session names and the default |
| `POST` | `/sessions` | Create a new session — body `{"name": "..."}` |
| `POST` | `/sessions/{sid}/copy` | Copy a session — body `{"new_name": "..."}` |

Status codes:
- `201` on a successful create/copy.
- `404` when the source session of a copy doesn't exist.
- `409` for duplicate names **or** unsafe names (path separators, `..`,
  drive prefixes, empty strings). Session names are validated at the
  framework layer; the API doesn't add a second guard.

## Algorithm + KPI discovery

These endpoints let a remote frontend render a scenario-creation form for an
algorithm it has never seen before.

| Verb | Path | Description |
|---|---|---|
| `GET` | `/sessions/{sid}/algorithms` | List algorithm template names |
| `GET` | `/sessions/{sid}/algorithms/{name}/parameters` | Per-parameter descriptors |
| `GET` | `/sessions/{sid}/kpis` | List KPI template names |

The `/parameters` response is a list of descriptors, one per parameter:
```{code-block} json
{
  "name": "Slow",
  "parameters": [
    {
      "name": "duration",
      "type": "integer",
      "required": true,
      "value": 1,
      "default": 1,
      "min": 1,
      "max": 60
    }
  ]
}
```

Optional fields (`choices`, `min`/`max`, `default`) appear only when they
apply to the parameter's type — enums get `choices`, numerics get `min`/`max`,
and so on.

## Scenarios

CRUD plus the run-and-poll lifecycle. Run is fire-and-forget on the API; clients
should poll `/status` for progress.

| Verb | Path | Description |
|---|---|---|
| `GET` | `/sessions/{sid}/scenarios` | List scenarios (full `to_dict()`) |
| `POST` | `/sessions/{sid}/scenarios` | Create scenario — body `{tag, dataset_key, algo_name, algo_params}` |
| `GET` | `/sessions/{sid}/scenarios/{id}` | Full scenario including KPIs + result |
| `DELETE` | `/sessions/{sid}/scenarios/{id}` | Remove scenario |
| `POST` | `/sessions/{sid}/scenarios/{id}/run` | Enqueue for processing (returns `202`) |
| `GET` | `/sessions/{sid}/scenarios/{id}/status` | Lightweight `{id, tag, status, progress}` for polling |
| `GET` | `/sessions/{sid}/processing` | The scenario currently processing, or `null` |

Status codes for `POST /scenarios`:
- `201` on success.
- `404` if `algo_name` or `dataset_key` does not exist in this session.
- `409` if `tag` is already used.
- `400` for parameter validation failures (out-of-range values, wrong types).
- `422` if a required body field is missing (Pydantic-level validation).

```{tip}
The `/status` endpoint is intentionally small: just id, tag, status, and
progress. It is safe to poll at a high frequency without serializing the full
scenario (with KPIs, algorithm config, and result payload) every time.
```

## Data management

| Verb | Path | Description |
|---|---|---|
| `GET` | `/sessions/{sid}/data` | List dataset keys |
| `GET` | `/sessions/{sid}/data/{key}` | Parsed JSON for a dataset |
| `DELETE` | `/sessions/{sid}/data/{key}` | Remove a dataset |
| `POST` | `/sessions/{sid}/data/{key}/derive` | Derive a new dataset — body `{"new_key": "..."}` |
| `POST` | `/sessions/{sid}/data/from-json` | Add a dataset from a `DataSource.to_json()` payload |
| `POST` | `/sessions/{sid}/etl` | Run ETL over an uploaded multipart bundle |

`POST /etl` accepts a multipart form with `dataset_name` (form field) and one
or more `files` parts. The filename stem becomes the logical name the ETL
factory expects (`sku_data.csv` ⇒ `sku_data`); the extension picks the
`File` subclass (`.csv`, `.json`, `.xlsx`).

Deleting a dataset that is referenced by a scenario returns `409`. To delete
the underlying data, delete its referencing scenarios first.

## Polling pattern

A complete run-to-completion flow from a client:

```{code-block} python
:caption: client.py
import time
import httpx

base = "http://127.0.0.1:8051/api/v1"
session = httpx.get(f"{base}/sessions").json()["default"]

scenario = httpx.post(
    f"{base}/sessions/{session}/scenarios",
    json={
        "tag": "my-run",
        "dataset_key": "Master data",
        "algo_name": "Slow",
        "algo_params": {"duration": 5},
    },
).json()

httpx.post(f"{base}/sessions/{session}/scenarios/{scenario['id']}/run")

while True:
    status = httpx.get(
        f"{base}/sessions/{session}/scenarios/{scenario['id']}/status"
    ).json()
    if status["status"] in ("complete", "failed"):
        break
    time.sleep(0.5)

result = httpx.get(
    f"{base}/sessions/{session}/scenarios/{scenario['id']}"
).json()
print(result["kpis"])
```

## Error mapping

The API translates framework exceptions to HTTP status codes consistently:

| Exception | HTTP | Source |
|---|---|---|
| `ValueError` | `400` | Generic bad input — also used for duplicate-tag scenarios (handled explicitly in the route) |
| `ParameterError` | `400` | Out-of-range / wrong-type parameter values |
| `AssertionError` | `409` | Framework precondition failure (e.g. deleting a dataset that is used by a scenario) |
| Manual route raises | `404` / `409` | Explicit `HTTPException` from the route — used for unknown algorithm/dataset/session/scenario lookups, duplicate session/dataset names, and tag conflicts |
| Anything else | `500` | Unexpected; logged with a traceback |

```{note}
The error response shape is consistent: `{"detail": "<message>"}`. Use the
HTTP status code to branch, not the message text — messages are written for
humans and may change between versions.
```

## Cross-references

- {ref}`Scenario reference <scenario-package-ref>` — `CoreConfig`, `ScenarioManager`, `SessionManager`.
- {ref}`Data reference <data-ref>` — `DataSource`, `ETLFactory`, `Schema`.
- {ref}`CLI reference <cli-ref>` — the sibling headless frontend.
