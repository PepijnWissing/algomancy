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
from myapp.templates import kpi_templates, algorithm_templates
from myapp.schemas import all_schemas


cfg = ApiConfiguration(
    etl_factory=MyETLFactory,
    kpi_templates=kpi_templates,
    algo_templates=algorithm_templates,
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
fields like `etl_factory`, `kpi_templates`, `algo_templates`, `schemas`,
`data_object_type`, `data_path`, `has_persistent_state`, `autocreate`,
`autorun`, and `title` behave exactly as they do for the GUI.

| Field | Type | Default | Notes |
|---|---|---|---|
| `host` | `str` | `"127.0.0.1"` | Bind address |
| `port` | `int` | `8051` | Bind port |
| `prefix` | `str` | `"/api/v1"` | URL prefix for all routes (must start with `/`) |
| `cors_origins` | `list[str]` | `[]` | Allowed CORS origins; empty disables CORS middleware |

Routes are always scoped by session under `/sessions/{session_id}/...`. The
SessionManager auto-creates a default `"main"` session when none exists yet,
so single-tenant deployments still have a working URL shape.

## Sessions

The API always exposes routes under `/sessions/{session_id}/...`. A
session is a self-contained `ScenarioManager` with its own data and
scenarios — useful for serving multiple users or experiment workspaces from
one process.

**Identity.** Every session has a stable UUID ``id`` and a mutable
``display_name``. The URL path uses the UUID; the ``display_name`` is what
you show in UIs. For convenience, the URL path also accepts a session's
current ``display_name`` as a soft-compat alias — useful for single-tenant
deployments and clients migrating from pre-M14 algomancy. Authoritative
clients should always use the UUID returned by ``GET /sessions``.

| Verb | Path | Description |
|---|---|---|
| `GET` | `/sessions` | List `[{id, display_name}, ...]` and the default id |
| `POST` | `/sessions` | Create — body `{"display_name": "..."}` |
| `POST` | `/sessions/{sid}/copy` | Copy — body `{"new_display_name": "..."}` |
| `PATCH` | `/sessions/{sid}` | Rename — body `{"display_name": "..."}` (id stays) |
| `DELETE` | `/sessions/{sid}` | Delete a session and all its scenarios, runs, KPIs, and data |

Status codes:
- `201` on a successful create/copy.
- `200` on a successful rename or delete; the rename response is the
  updated `{id, display_name}`, the delete response is the refreshed
  session list.
- `404` when the targeted session doesn't exist.
- `409` when the requested `display_name` is already taken by another session.
- `422` when the request body fails Pydantic validation (e.g. empty
  `display_name`).

Deleting the last remaining session never leaves the manager empty: a
fresh ``"main"`` session is auto-created in its place so subsequent
scenario writes still have somewhere to land.

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

```{tip}
The `/status` endpoint is intentionally small: just id, tag, status, and
progress. It is safe to poll at a high frequency without serializing the full
scenario (with KPIs, algorithm config, and result payload) every time.
```

(api-create-scenario-ref)=
### `POST /sessions/{sid}/scenarios` — create a scenario

Binds an input dataset + algorithm + parameter values into a runnable
scenario. The body is JSON.

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `tag` | string | yes | Human-readable scenario name. Must be unique within the session — duplicates return `409`. |
| `dataset_key` | string | yes | Must exist in this session's data manager. Discover via `GET /data`. |
| `algo_name` | string | yes | Must exist in `available_algorithms`. Discover via `GET /algorithms`. |
| `algo_params` | object | no | Parameter values keyed by parameter name. Omit or set to `null` for defaults. Discover the expected keys via `GET /algorithms/{name}/parameters`. |

The `algo_params` keys come from the algorithm's parameter set — the
`/parameters` endpoint described above returns the schema. Values are
validated against that schema by `BaseParameterSet`; bad values raise
`ParameterError` and the route returns `400` with the detail.

**Example**

```{code-block} python
import httpx

scenario = httpx.post(
    "http://127.0.0.1:8051/api/v1/sessions/main/scenarios",
    json={
        "tag": "slow-5s",
        "dataset_key": "Master data",
        "algo_name": "Slow",
        "algo_params": {"duration": 5},
    },
).json()
```

**Response** (`201`)

Returns the full `Scenario.to_dict()` payload (see
{ref}`Scenario response shape <api-scenario-shape-ref>` below). At this point
`status` is `"CREATED"`, `result` is `null`, and each KPI's `value` is `None`.

**Error cases**

| Status | When |
|---|---|
| `404` | `algo_name` is not registered, or `dataset_key` is not present. |
| `409` | `tag` already exists in this session. |
| `400` | A parameter value failed validation (`ParameterError`). |
| `422` | A required field is missing or has the wrong JSON type (Pydantic-level). |

(api-run-scenario-ref)=
### `POST /sessions/{sid}/scenarios/{id}/run` — enqueue for processing

Fire-and-forget. Returns `202 Accepted` immediately and returns the scenario
in its `QUEUED` state — actual computation happens on a worker thread. Clients
must poll `GET /status` to observe progress and completion.

The status state machine, in order:

```
CREATED  →  QUEUED  →  PROCESSING  →  COMPLETE
                                  ↘   FAILED
```

`COMPLETE` and `FAILED` are terminal. A subsequent `/run` on a terminal
scenario re-enqueues it from the current state — the manager allows re-runs.
At any moment, at most one scenario per session is in `PROCESSING`; check
`GET /processing` to see which one.

**Polling**

`GET /status` returns just `{id, tag, status, progress}` and is safe to call
at high frequency. `progress` is a float in `[0.0, 1.0]`. Once `status` is
`COMPLETE` or `FAILED`, fetch the full result with `GET /scenarios/{id}`.

**Error cases**

| Status | When |
|---|---|
| `404` | `scenario_id` does not exist in this session. |
| `500` | The algorithm raised an exception during processing. Note: the HTTP response for `/run` itself does not surface this — the failure is reflected in the scenario's `status=FAILED` field. Inspect the server log for the traceback. |

(api-scenario-shape-ref)=
### Scenario response shape

`GET /scenarios` and `GET /scenarios/{id}` (and the create/run endpoints)
return the dict produced by `Scenario.to_dict()`:

```{code-block} json
{
  "id": "01HZX...",
  "tag": "slow-5s",
  "input_data_id": "Master data",
  "algorithm": {
    "name": "Slow",
    "parameters": [
      {"name": "duration", "type": "integer", "value": 5, "default": 1, "min": 1, "max": 60, "required": true}
    ]
  },
  "kpis": {
    "throughput": {"name": "throughput", "value": 42.0, "unit": "items/s"}
  },
  "status": "complete",
  "result": { "...domain-specific Result.to_dict() payload..." }
}
```

- `result` and each KPI's `value` are `null` until the scenario reaches
  `COMPLETE`.
- `kpis` is keyed by the KPI template name registered in `kpi_templates`.
- `algorithm.parameters` is the same descriptor shape returned by
  `GET /algorithms/{name}/parameters`, plus the `value` chosen for this run.
- `result` is whatever your domain's `BaseResult.to_dict()` returns. The
  framework does not impose a shape — see the
  {ref}`Scenario reference <scenario-package-ref>`.

There is no separate `/kpi-measurements` endpoint; KPI values are part of
this payload.

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

(api-etl-ref)=
### `POST /sessions/{sid}/etl` — run ETL over uploaded files

Stages a bundle of uploaded files into a temp directory, wraps each one in the
appropriate `algomancy_data.File` subclass, and calls
`ScenarioManager.etl_data(file_map, dataset_name)`. The result is a new (or
overwritten) dataset accessible under the chosen `dataset_name`.

This is the only endpoint that uses a **multipart/form-data** body — every
other write accepts JSON. There is no Pydantic model for the request because
FastAPI's `UploadFile` handling is what converts the multipart parts into
file-like objects on the server. The OpenAPI schema at `/openapi.json` does
describe the `dataset_name` form field and the `files` array.

**Form fields**

| Field | Repeated? | Type | Notes |
|---|---|---|---|
| `dataset_name` | once | string | Logical key the resulting dataset is stored under. Required, non-empty. |
| `files` | one or more | file upload | Each upload's filename stem becomes the **logical name** the ETL factory expects. Extension picks the `File` subclass — `csv` → `CSVFile`, `json` → `JSONFile`, `xlsx` → `XLSXFile`. Any other extension fails with `400`. |

The filename stem mapping means the ETL factory does NOT receive uploaded
filenames as opaque blobs — they must match the logical names declared by your
schemas. For example, if your schemas declare a `sku_data` group, the
corresponding upload must be `sku_data.csv` (or `.json`, or `.xlsx`).

**Curl example**

```{code-block} bash
curl -X POST http://127.0.0.1:8051/api/v1/sessions/main/etl \
  -F dataset_name=uploaded \
  -F files=@./sku_data.csv \
  -F files=@./inventory.xlsx
```

Note: each `-F files=@...` repeats the same form field name `files`; that is
how multipart "array" fields are encoded.

**Python example (httpx)**

```{code-block} python
import httpx

with open("sku_data.csv", "rb") as csv, open("inventory.xlsx", "rb") as xlsx:
    r = httpx.post(
        "http://127.0.0.1:8051/api/v1/sessions/main/etl",
        data={"dataset_name": "uploaded"},
        files=[
            ("files", ("sku_data.csv", csv, "text/csv")),
            (
                "files",
                (
                    "inventory.xlsx",
                    xlsx,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
            ),
        ],
    )
r.raise_for_status()
```

**Response**

```{code-block} json
{
  "dataset_name": "uploaded",
  "success": true,
  "keys": ["uploaded", "Master data"]
}
```

`success` reflects `ETLResult.is_success` — a successful HTTP request can
still report `success=false` when extraction or validation produced ERRORs but
the request itself completed cleanly. Inspect the dataset and the manager's
log to diagnose.

**Error cases**

| Status | When |
|---|---|
| `400` | No files uploaded, an upload is missing a filename, or the filename extension is not in `{csv, json, xlsx}`. |
| `404` | `session_id` does not exist. |
| `422` | `dataset_name` form field missing (Pydantic-level validation). |
| `500` | The ETL pipeline itself raised an unhandled exception (logged with traceback). |

(api-from-json-ref)=
### `POST /sessions/{sid}/data/from-json` — ingest a serialized DataSource

Accepts the raw JSON produced by `DataSource.to_json()` as the request body
(not wrapped in any envelope). The framework parses the body with
`DataSource.from_json`, so the bytes are forwarded verbatim and the route does
no re-encoding. Both an object-rooted and array-rooted payload are accepted —
whichever your `DataSource` subclass produces.

Returns `201` with the full key list. Common errors: `400` on an empty body or
malformed JSON, `404` on unknown session.

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
