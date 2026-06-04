(fundamentals-sessions-ref)=
# Sessions

A **session** is an isolated workspace inside a running Algomancy backend.
It owns its own scenarios, runs, KPI measurements, and uploaded datasets,
and it is the unit of scoping for every persistence operation. Every
deployment — even a single-user workshop — runs with at least one
session active; the `SessionManager` always auto-creates a default
`"main"` session when none exists yet.

```{eval-rst}
.. mermaid::

    flowchart LR
        SM[SessionManager] --> S1[Session A]
        SM --> S2[Session B]
        SM --> S3[Session C]

        S1 --> DM1[DataManager]
        S1 --> SP1[ScenarioProcessor]
        S1 --> Sc1[Scenarios + Runs + KPIs]

        S2 --> DM2[DataManager]
        S2 --> SP2[ScenarioProcessor]
        S2 --> Sc2[Scenarios + Runs + KPIs]
```

## Identity and display name

Each session has two strings:

| Field | Mutability | Used for |
|---|---|---|
| `id` | **immutable** UUID generated at creation time | URL paths, database FKs, GUI store values |
| `display_name` | **mutable**, free-form human label | dropdowns, page headers, any UI surface |

The split matters because the `display_name` is the part users actually
want to change — "alice_experiment_v1" might become "alice_experiment_final"
without affecting any URL bookmark, database row, or scenario reference.
Renames go through `SessionManager.rename_session(id, new_display_name)`
or, over HTTP, ``PATCH /api/v1/sessions/{id}`` with body
``{"display_name": "..."}``.

## Persistence backends

Sessions live in one of two backends; both expose the same SessionManager
API but differ in where the data lands.

### Filesystem (default)

Each session is a subdirectory of `data_path`. The directory contains the
session's datasets (one subdirectory per dataset, plus the saved scenario
state) and a small `meta.json`:

```
data/
├── default_session/
│   ├── meta.json              ← {"id": "<uuid>", "display_name": "default_session"}
│   ├── scenarios.json
│   └── example_data/
│       ├── sku_data.csv
│       └── ...
└── alice_experiment/
    ├── meta.json
    ├── scenarios.json
    └── ...
```

The directory name is decided once, when the session is first created
(it's the slugified `display_name`), and never changes afterwards.
Renaming a session only updates `meta.json`. Pre-M14 session directories
without a `meta.json` are migrated transparently on first scan — the
directory name becomes the initial `display_name` and a fresh UUID is
written.

### Database

Sessions are rows of `algomancy_sessions`:

```
algomancy_sessions
├── id            VARCHAR PK   ← UUID
├── display_name  VARCHAR NOT NULL
└── created_at    TIMESTAMP
```

The session's scenarios, runs, and KPI measurements live in
`algomancy_scenarios`, `algomancy_scenario_runs`, and
`algomancy_kpi_measurements` (all keyed by `session_id`). The session's
datasets are persisted through one of two paths, chosen per-DataSource
by `DatabaseDataManager`:

- **Per-sub-table SQL** (default, used by the bundled `DataSource` and
  any custom subclass that implements the `SqlTableLayout` protocol) —
  each DataFrame becomes its own table named
  `ds__{session_id}__{dataset_name}__{sub_table}`. Data stays externally
  queryable and is loaded lazily on first access.
- **JSON blob** (fallback, used by any other `BaseDataSource` subclass)
  — the DataSource is serialised via `to_json()` into a `payload`
  column on the catalogue.

Either way the row in `algomancy_datasets` carries the dataset's id,
name, classification, and creation time. See
{ref}`Database persistence of custom data sources <fundamentals-data-container-ref>`
for the opt-in protocol.

To choose the database backend pass `persistence_backend="database"`
and `database_url=...` to `CoreConfig` / `ApiConfiguration`.

## Isolation guarantees

Within a single backend process, sessions are mutually isolated at the
SessionManager layer: a ScenarioManager only sees data + scenarios that
belong to its session. A scenario in one session cannot reference a
dataset in another; a KPI computation cannot reach across.

The framework does **not** yet enforce isolation between *processes*. If
you point two backend processes at the same data folder, both will load
the same sessions and writes will race. The
{ref}`Frontends <fundamentals-frontends-ref>` page calls this out: prefer
one frontend per backend process unless the second one is read-only.

## Lifecycle

| Operation | SessionManager | HTTP |
|---|---|---|
| Create | `create_new_session(display_name) -> id` | `POST /sessions` |
| Copy | `copy_session(source_id, new_display_name) -> id` | `POST /sessions/{id}/copy` |
| Rename | `rename_session(id, new_display_name)` | `PATCH /sessions/{id}` |
| Delete | `delete_session(id)` | `DELETE /sessions/{id}` |
| Resolve display name → id | `resolve_id_by_display_name(name)` | (use the list response) |

Deleting a session cascades through all of its scenarios, runs, KPI
measurements, and uploaded data — on the database backend the dynamic
`ds__{id}__*` tables are dropped. Deleting the last remaining session is
never an empty state: a fresh `"main"` session is auto-created in its
place.

## When to create a session

| Shape | Approach |
|---|---|
| Single-user workshop, one analyst | Stay on the auto-created `"main"` (or create one named after the project) |
| Multiple analysts sharing one backend | One session per analyst; switch via the admin page dropdown |
| Same analyst, multiple experiments | One session per experiment; rename freely as the experiment evolves |
| Programmatic clients (API) | Sessions are how you scope HTTP requests; create one per logical workspace |

## How the API and GUI scope by session

The `algomancy-api` HTTP service nests all scenario, data, algorithm,
and KPI routes under `/api/v1/sessions/{session_id}/...`. The session_id
in the URL is a UUID; the URL routing layer also accepts the current
`display_name` as a soft-compat alias so casual single-tenant
deployments can use human-readable URLs while migrating to UUIDs.

The Dash GUI carries the active session id in a `dcc.Store`
(`ACTIVE_SESSION`) so every page renders against the same session. The
session picker on the admin page reads `SessionManager.list_sessions()`
and shows `display_name` in the dropdown while storing the `id` as the
selected value.

When `FeatureConfig.show_session_picker=False` the picker is hidden —
useful for single-tenant deployments where the user shouldn't be
switching contexts. Sessions still exist underneath, the UI just doesn't
expose the controls.

See also: {ref}`Frontends <fundamentals-frontends-ref>` for how the
GUI and API consume the SessionManager, and {ref}`HTTP API
reference <api-ref>` for the full session route shape.
