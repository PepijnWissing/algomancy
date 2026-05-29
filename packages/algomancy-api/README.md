# algomancy-api

FastAPI HTTP interface that exposes the same scenario/data management surface used
by `algomancy-gui` and `algomancy-cli`, so a remote frontend (browser SPA, native
desktop app, another Python process, ...) can drive an Algomancy backend over the
network instead of importing it in-process.

## Quick start

```bash
# launch with your own config
algomancy-api --config-callback myapp:make_config

# or with the bundled example config
algomancy-api --example
```

The server starts (default `127.0.0.1:8051`) and serves an OpenAPI schema at
`/docs`. All scenario/data endpoints live under `/api/v1/sessions/{session_id}/...`.

## Programmatic use

```python
from algomancy_api import ApiLauncher, ApiConfiguration

cfg = ApiConfiguration(
    etl_factory=...,
    kpi_templates=...,
    algo_templates=...,
    schemas=...,
    data_object_type=...,
    has_persistent_state=False,
    autocreate=False,
    autorun=False,
)
app = ApiLauncher.build(cfg)
ApiLauncher.run(app, host=cfg.host, port=cfg.port)
```
