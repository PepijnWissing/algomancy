(api-endpoint-details-ref)=
# Endpoint reference

Every built-in endpoint is documented below in the same order they are registered.
Each section follows a fixed pattern: **Function** → **Request body** (omitted when none) → **Responses** → tips or notes where they add value.

All paths are relative to the configured `prefix` (default `/api/v1`).  The full URL for a single-host deployment running on the defaults would be `http://127.0.0.1:8051/api/v1/<path>`.

---

## Global

### GET /health

**Function:** Liveness probe. Returns the server title and the display names of all active sessions.

**Responses**

| Status | Meaning |
|---|---|
| `200` | Always. Body: `{"status": "ok", "title": "<cfg.title>", "sessions": ["main", ...]}` |

:::{tip}
Use this as a readiness check before sending any domain requests — if the server isn't up yet, this endpoint is the cheapest one to poll.
:::

---

## Sessions

### GET /sessions

**Function:** Lists all sessions with their stable UUIDs and mutable display names, plus the UUID of the default session.

**Responses**

| Status | Meaning |
|---|---|
| `200` | Body: `{"sessions": [{"id": "...", "display_name": "..."}], "default": "<uuid>"}` |

:::{tip}
The `default` key is the UUID of the session that was created first (or the auto-created `"main"` session).  Authoritative clients should cache this UUID rather than the display name, which can be changed with `PATCH /sessions/{sid}`.
:::

---

### POST /sessions

**Function:** Creates a new, empty session with the given display name.

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `display_name` | string | yes | Must be non-empty. Must not collide with an existing session's display name. |

**Responses**

| Status | Meaning |
|---|---|
| `201` | Session created. Body: refreshed session list (same shape as `GET /sessions`). |
| `409` | A session with that display name already exists. |
| `422` | `display_name` is missing or empty (Pydantic validation). |

---

### POST /sessions/{sid}/copy

**Function:** Copies an existing session — all its scenarios, data, and configuration — under a new display name. The original session is unchanged.

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `new_display_name` | string | yes | Must be non-empty and not already taken. |

**Responses**

| Status | Meaning |
|---|---|
| `201` | Copy created. Body: refreshed session list. |
| `404` | `sid` does not match any session. |
| `409` | `new_display_name` already exists. |
| `422` | `new_display_name` is missing or empty. |

---

### PATCH /sessions/{sid}

**Function:** Renames a session. The UUID is immutable; only `display_name` changes.

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `display_name` | string | yes | Must be non-empty and not already taken by another session. |

**Responses**

| Status | Meaning |
|---|---|
| `200` | Renamed. Body: the updated `{"id": "...", "display_name": "..."}` for this session. |
| `404` | `sid` does not match any session. |
| `409` | `display_name` is already taken by a different session. |
| `422` | `display_name` is missing or empty. |

---

### DELETE /sessions/{sid}

**Function:** Permanently deletes the session and everything it contains (scenarios, runs, KPI measurements, datasets).

**Responses**

| Status | Meaning |
|---|---|
| `200` | Deleted. Body: refreshed session list. |
| `404` | `sid` does not match any session. |

:::{note}
Deleting the last remaining session never leaves the manager empty: a fresh `"main"` session is automatically created so subsequent writes still have somewhere to land.
:::

---

## Algorithms & KPIs

### GET /sessions/{sid}/algorithms

**Function:** Lists the names of all algorithm templates registered in this session's configuration.

**Responses**

| Status | Meaning |
|---|---|
| `200` | Body: `{"algorithms": ["AlgoA", "AlgoB", ...]}` |
| `404` | Session not found. |

:::{tip}
Use these names as the `algo_name` value when creating a scenario.
:::

---

### GET /sessions/{sid}/algorithms/{name}/parameters

**Function:** Returns the parameter schema for one algorithm — the complete set of fields, types, constraints, and defaults a client needs to build a scenario-creation form dynamically.

**Responses**

| Status | Meaning |
|---|---|
| `200` | Body: `{"name": "<algo>", "parameters": [...]}` |
| `404` | Session not found, or `name` is not a registered algorithm. |

The `parameters` array contains one object per parameter:

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

Optional fields (`choices`, `min`, `max`, `default`) appear only when they apply to the parameter type — enums get `choices`, numerics get `min`/`max`, and so on.

---

### GET /sessions/{sid}/kpis

**Function:** Lists the names of all KPI templates configured in this session.

**Responses**

| Status | Meaning |
|---|---|
| `200` | Body: `{"kpis": ["throughput", "latency", ...]}` |
| `404` | Session not found. |

:::{tip}
KPI values appear on the scenario object after it reaches `COMPLETE` — there is no separate KPI endpoint.
:::

---

## Scenarios

### GET /sessions/{sid}/scenarios

**Function:** Returns the full `Scenario.to_dict()` payload for every scenario in the session.

**Responses**

| Status | Meaning |
|---|---|
| `200` | Body: array of scenario objects (see [scenario response shape](#scenario-response-shape)). |
| `404` | Session not found. |

---

(api-create-scenario-ref)=
### POST /sessions/{sid}/scenarios

**Function:** Creates a new scenario by binding an input dataset, an algorithm, and parameter values. The scenario is not executed yet — call `POST …/run` to enqueue it.

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `tag` | string | yes | Human-readable name. Must be unique within the session. |
| `dataset_key` | string | yes | Must exist in this session's data manager. Discover keys via `GET /data`. |
| `algo_name` | string | yes | Must be a registered algorithm template. Discover names via `GET /algorithms`. |
| `algo_params` | object | no | Parameter values keyed by parameter name. Omit or set to `null` to use all defaults. Discover the expected keys via `GET /algorithms/{name}/parameters`. |
| `data_params` | object | no | Data-source parameter overrides. Discover the shape via `GET /data/{key}/parameters`. |

**Responses**

| Status | Meaning |
|---|---|
| `201` | Created. Body: full scenario object with `status = "CREATED"`, `result = null`, KPI values `null`. |
| `400` | A parameter value failed validation (`ParameterError`). |
| `404` | `algo_name` is not registered, or `dataset_key` does not exist. |
| `409` | `tag` already exists in this session. |
| `422` | A required field is missing or has the wrong JSON type. |

---

### GET /sessions/{sid}/scenarios/{id}

**Function:** Returns the full `Scenario.to_dict()` payload for one scenario, including KPI values and the algorithm result after execution completes.

**Responses**

| Status | Meaning |
|---|---|
| `200` | Body: scenario object (see [scenario response shape](#scenario-response-shape)). |
| `404` | Session or scenario not found. |

---

### DELETE /sessions/{sid}/scenarios/{id}

**Function:** Permanently removes a scenario from the session.

**Responses**

| Status | Meaning |
|---|---|
| `204` | Deleted. No body. |
| `404` | Session or scenario not found. |

---

(api-run-scenario-ref)=
### POST /sessions/{sid}/scenarios/{id}/run

**Function:** Enqueues the scenario for execution. Returns immediately with `202 Accepted`; actual computation runs on a background worker thread. Clients must poll `GET …/status` to observe progress and completion.

**Responses**

| Status | Meaning |
|---|---|
| `202` | Accepted. Body: scenario object in `QUEUED` state. |
| `404` | Session or scenario not found. |

The status state machine, in order:

```
CREATED  →  QUEUED  →  PROCESSING  →  COMPLETE
                                  ↘   FAILED
```

`COMPLETE` and `FAILED` are terminal. A subsequent `/run` on a terminal scenario re-enqueues it — the manager allows re-runs. At most one scenario per session is in `PROCESSING` at any moment; check `GET /processing` to see which one.

:::{tip}
**Polling pattern** — a complete run-to-completion flow:

```{code-block} python
import time, httpx

base = "http://127.0.0.1:8051/api/v1"
session = httpx.get(f"{base}/sessions").json()["default"]

scenario = httpx.post(
    f"{base}/sessions/{session}/scenarios",
    json={"tag": "my-run", "dataset_key": "Master data",
          "algo_name": "Slow", "algo_params": {"duration": 5}},
).json()

httpx.post(f"{base}/sessions/{session}/scenarios/{scenario['id']}/run")

while True:
    s = httpx.get(f"{base}/sessions/{session}/scenarios/{scenario['id']}/status").json()
    if s["status"] in ("complete", "failed"):
        break
    time.sleep(0.5)

result = httpx.get(f"{base}/sessions/{session}/scenarios/{scenario['id']}").json()
print(result["kpis"])
```
:::

---

### GET /sessions/{sid}/scenarios/{id}/status

**Function:** Lightweight poll endpoint. Returns only `id`, `tag`, `status`, and `progress` — intentionally small so it is safe to call at high frequency without serializing the full scenario payload.

**Responses**

| Status | Meaning |
|---|---|
| `200` | Body: `{"id": "...", "tag": "...", "status": "PROCESSING", "progress": 0.42}` |
| `404` | Session or scenario not found. |

`progress` is a float in `[0.0, 1.0]`. Once `status` is `COMPLETE` or `FAILED`, fetch the full result with `GET /scenarios/{id}`.

---

### GET /sessions/{sid}/processing

**Function:** Returns the scenario currently being processed by the background worker, or `null` if the worker is idle.

**Responses**

| Status | Meaning |
|---|---|
| `200` | Body: full scenario object if one is processing, or `null`. |
| `404` | Session not found. |

---

(api-scenario-shape-ref)=
### Scenario response shape

`GET /scenarios`, `GET /scenarios/{id}`, and the create/run endpoints all return `Scenario.to_dict()`:

```{code-block} json
{
  "id": "01HZX...",
  "tag": "slow-5s",
  "input_data_id": "Master data",
  "algorithm": {
    "name": "Slow",
    "parameters": [
      {"name": "duration", "type": "integer", "value": 5,
       "default": 1, "min": 1, "max": 60, "required": true}
    ]
  },
  "kpis": {
    "throughput": {"name": "throughput", "value": 42.0, "unit": "items/s"}
  },
  "status": "complete",
  "result": {"...domain-specific Result.to_dict() payload..."}
}
```

- `result` and each KPI's `value` are `null` until the scenario reaches `COMPLETE`.
- `kpis` is keyed by the KPI template name registered in `cfg.kpis`.
- `algorithm.parameters` uses the same descriptor shape as `GET /algorithms/{name}/parameters`, plus the `value` chosen for this scenario.
- `result` is whatever your `BaseResult.to_dict()` returns — the framework imposes no shape.

---

## Data

### GET /sessions/{sid}/data

**Function:** Lists the keys of all datasets currently loaded in the session.

**Responses**

| Status | Meaning |
|---|---|
| `200` | Body: `{"keys": ["Master data", "uploaded", ...]}` |
| `404` | Session not found. |

---

### GET /sessions/{sid}/data/{key}

**Function:** Returns a dataset's full JSON representation — the output of `DataSource.to_json()`.

**Responses**

| Status | Meaning |
|---|---|
| `200` | Body: the `DataSource.to_json()` payload for this dataset. Shape depends on your `DataSource` subclass. |
| `404` | Session or dataset not found. |

---

### DELETE /sessions/{sid}/data/{key}

**Function:** Permanently removes a dataset from the session.

**Responses**

| Status | Meaning |
|---|---|
| `204` | Deleted. No body. |
| `404` | Session or dataset not found. |
| `409` | At least one scenario in this session references the dataset. Delete those scenarios first. |

---

### POST /sessions/{sid}/data/{key}/derive

**Function:** Derives a new dataset from an existing one and stores it under a new key. What "derive" does concretely is determined by your `DataSource` implementation.

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `new_key` | string | yes | Identifier for the derived dataset. Must be non-empty. |

**Responses**

| Status | Meaning |
|---|---|
| `201` | Derived dataset created. Body: refreshed key list `{"keys": [...]}`. |
| `404` | Session not found or `key` does not exist. |
| `409` | `new_key` already exists. |
| `422` | `new_key` is missing or empty. |

---

(api-from-json-ref)=
### POST /sessions/{sid}/data/from-json

**Function:** Ingests a serialised `DataSource` directly. The request body is the raw JSON produced by `DataSource.to_json()` — not wrapped in any envelope. The server parses it with `DataSource.from_json` and registers the result under the key embedded in the payload.

**Request body**

Raw JSON — the verbatim output of `DataSource.to_json()`. Both object-rooted and array-rooted payloads are accepted, depending on what your `DataSource` subclass produces.

**Responses**

| Status | Meaning |
|---|---|
| `201` | Ingested. Body: refreshed key list `{"keys": [...]}`. |
| `400` | Empty body or malformed JSON. |
| `404` | Session not found. |

:::{tip}
This endpoint is the counterpart of `GET /data/{key}`: fetch a dataset from one session and `POST` it straight to another without any re-serialisation.
:::

---

(api-etl-ref)=
### POST /sessions/{sid}/etl

**Function:** Accepts one or more file uploads, stages them through the configured `ETLFactory`, and registers the result as a new (or overwritten) dataset under `dataset_name`.

This is the only endpoint that uses **multipart/form-data** — all other write endpoints accept JSON.

**Request body** (multipart/form-data)

| Field | Repeated? | Type | Notes |
|---|---|---|---|
| `dataset_name` | once | string | Logical key the resulting dataset is stored under. Required, non-empty. |
| `files` | one or more | file upload | Filename stem becomes the logical name the ETL factory expects. Extension selects the `File` subclass: `.csv` → `CSVFile`, `.json` → `JSONFile`, `.xlsx` → `XLSXFile`. Any other extension fails with `400`. |

**Responses**

| Status | Meaning |
|---|---|
| `200` | ETL completed. Body: `{"dataset_name": "...", "success": true/false, "keys": [...]}`. |
| `400` | No files supplied, an upload is missing a filename, or an unsupported file extension was used. |
| `404` | Session not found. |
| `422` | `dataset_name` form field is missing. |
| `500` | The ETL pipeline raised an unhandled exception (logged with traceback server-side). |

:::{note}
`success` in the response body reflects `ETLResult.is_success`. A `200` response can carry `"success": false` when extraction or validation produced `ERROR`-level messages but the request itself completed cleanly. Inspect the dataset and the server log to diagnose.

The filename stem mapping means filenames are **not** opaque. If your schema declares a `sku_data` group, the upload must be named `sku_data.csv` (or `.json`, or `.xlsx`).
:::

**curl example**

```{code-block} bash
curl -X POST http://127.0.0.1:8051/api/v1/sessions/main/etl \
  -F dataset_name=uploaded \
  -F files=@./sku_data.csv \
  -F files=@./inventory.xlsx
```

**Python example (httpx)**

```{code-block} python
import httpx

with open("sku_data.csv", "rb") as csv_f, open("inventory.xlsx", "rb") as xlsx_f:
    r = httpx.post(
        "http://127.0.0.1:8051/api/v1/sessions/main/etl",
        data={"dataset_name": "uploaded"},
        files=[
            ("files", ("sku_data.csv", csv_f, "text/csv")),
            ("files", ("inventory.xlsx", xlsx_f,
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
        ],
    )
r.raise_for_status()
```
