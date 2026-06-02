# algomancy-api

FastAPI HTTP interface that exposes the same scenario- and data-management
surface used by `algomancy-gui`, so a remote frontend (browser SPA, native
desktop app, another Python process) can drive an Algomancy backend over
the network instead of importing it in-process.

The HTTP layer is deliberately thin: every route maps to a single
`ScenarioManager` / `SessionManager` method and responses use the existing
`to_dict()` payloads. There is no parallel domain model — clients work with
the same `Scenario`, `DataSource`, and `KPI` concepts the Dash GUI does.

## Quick start

```bash
# launch with the bundled example wiring
algomancy-api --example

# or with your own configuration callback
algomancy-api --config-callback myapp.api:make_config

# override host / port from the config
algomancy-api --example --host 0.0.0.0 --port 9000
```

The server starts (default `127.0.0.1:8051`) and serves the OpenAPI schema at
`/openapi.json` plus the interactive Swagger UI at `/docs`. All scenario/data
endpoints live under `/api/v1/sessions/{session_id}/...`.

## Programmatic use

```python
from algomancy_api import ApiConfiguration, ApiLauncher
from algomancy_data import DataSource

cfg = ApiConfiguration(
    etl_factory=MyETLFactory,
    kpi_templates=kpi_templates,
    algo_templates=algorithm_templates,
    schemas=schemas,
    data_object_type=DataSource,
    has_persistent_state=True,
    data_path="data",
    use_sessions=True,
    autocreate=False,
    autorun=False,
)
app = ApiLauncher.build(cfg)  # returns a standard FastAPI app
ApiLauncher.run(app)          # blocks; uses cfg.host / cfg.port
```

`ApiLauncher.build` returns a standard `FastAPI` instance — for production
deploys you can hand it to your own uvicorn / gunicorn process manager
instead of using `ApiLauncher.run`.

## Endpoint inventory

All routes are prefixed with `cfg.prefix` (default `/api/v1`).

### Sessions
- `GET    /sessions` — list sessions and the default
- `POST   /sessions` — create a new session
- `POST   /sessions/{sid}/copy` — copy an existing session

### Algorithm + KPI discovery
- `GET    /sessions/{sid}/algorithms` — list algorithm names
- `GET    /sessions/{sid}/algorithms/{name}/parameters` — per-parameter descriptors
- `GET    /sessions/{sid}/kpis` — list KPI template names

### Scenarios
- `GET    /sessions/{sid}/scenarios` — list scenarios
- `POST   /sessions/{sid}/scenarios` — create a scenario
- `GET    /sessions/{sid}/scenarios/{id}` — full scenario incl. KPIs and result
- `DELETE /sessions/{sid}/scenarios/{id}` — delete a scenario
- `POST   /sessions/{sid}/scenarios/{id}/run` — enqueue for processing
- `GET    /sessions/{sid}/scenarios/{id}/status` — lightweight status/progress (polling)
- `GET    /sessions/{sid}/processing` — currently running scenario, or `null`

### Data
- `GET    /sessions/{sid}/data` — list dataset keys
- `GET    /sessions/{sid}/data/{key}` — parsed JSON of a dataset
- `DELETE /sessions/{sid}/data/{key}` — delete a dataset
- `POST   /sessions/{sid}/data/{key}/derive` — derive a new dataset
- `POST   /sessions/{sid}/data/from-json` — add a dataset from `DataSource.to_json()` payload
- `POST   /sessions/{sid}/etl` — run ETL over a multipart upload

### Meta
- `GET    /health` — liveness probe
- `GET    /openapi.json`, `GET /docs` — OpenAPI schema and Swagger UI

## Polling pattern

```python
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

print(httpx.get(f"{base}/sessions/{session}/scenarios/{scenario['id']}").json())
```

## Error mapping

| Exception | HTTP | When |
|---|---|---|
| `ValueError` | `400` | Generic bad input |
| `ParameterError` | `400` | Algorithm parameter validation failure |
| `AssertionError` | `409` | Framework precondition (e.g. deleting data referenced by a scenario) |
| Route-level `HTTPException` | `404` / `409` | Unknown session/scenario/algorithm/dataset, duplicate tag, name conflict |
| Anything else | `500` | Unexpected; logged with traceback |

Response shape is always `{"detail": "<message>"}` — branch on the status
code, not the message text.

For the full reference (including the parameter-descriptor schema and CORS
configuration) see the
[HTTP API reference](https://algomancy.readthedocs.io/en/latest/reference/api.html)
in the published documentation.
