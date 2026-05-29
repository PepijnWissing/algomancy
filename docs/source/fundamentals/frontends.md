(fundamentals-frontends-ref)=
# Frontends

The same Algomancy backend can be driven through three frontend shapes,
chosen at startup time:

```{eval-rst}
.. mermaid::

    flowchart LR
        subgraph Frontends
            GUI[Dash GUI<br>algomancy-gui]
            CLI[Interactive Shell<br>algomancy-cli]
            API[HTTP API<br>algomancy-api]
        end

        subgraph Backend
            SM[SessionManager / ScenarioManager]
            DM[DataManager]
            SP[Scenario Processor]
        end

        GUI --> SM
        CLI --> SM
        API --> SM
        SM --> DM
        SM --> SP
```

All three reuse the same `ScenarioManager` / `SessionManager`, the same
algorithm and KPI templates, and the same configuration object. They differ
only in how a user (or another program) reaches the framework:

| Frontend | Best for | Entry point |
|---|---|---|
| `algomancy-gui` | Interactive analysis with rich, domain-specific visualizations | `GuiLauncher.build(AppConfig)` |
| `algomancy-cli` | Headless backend testing, scripted experiments | `algomancy-cli --config-callback module:fn` |
| `algomancy-api` | Remote frontends (browser SPAs, native apps, scripts) over HTTP | `algomancy-api --config-callback module:fn` |

The configuration objects share a `CoreConfig` base, so the same backend
wiring (`etl_factory`, `kpi_templates`, `algo_templates`, `schemas`,
`data_object_type`) can be passed to any of the launchers.

## Dash GUI
The default frontend — see {ref}`Graphical interface <fundamentals-frontend-ref>`
for a tour of the pages and the customization model.

## CLI shell
A REPL that opens directly on a `ScenarioManager`. Useful when iterating on
ETL or algorithm code without the cost of starting a Dash server, and as a
debugging entry point for headless deployments.

## HTTP API
A FastAPI server exposing scenario and data management as JSON over HTTP.
Suitable when you want to:

- Run a long-lived backend behind a load balancer and connect multiple
  clients (a custom browser SPA, a mobile app, a notebook) to it.
- Decouple the UI from the Python runtime — call the framework from
  TypeScript, Go, Rust, or shell scripts.
- Integrate Algomancy with other internal services that already speak HTTP.

The HTTP layer is intentionally thin: every route maps to a single
`ScenarioManager` / `SessionManager` method, and responses are the same
`to_dict()` payloads the rest of the framework already produces. There is no
parallel domain model; clients work with the same concepts (`Scenario`,
`DataSource`, `KPI`) that the GUI does.

For the complete endpoint inventory, launching instructions, and the
configuration surface, see {ref}`HTTP API reference <api-ref>`.

```{tip}
Frontends are not mutually exclusive — you can run, for example, a Dash GUI
and an HTTP API against the same checked-in data folder by pointing two
configs at the same `data_path`. Each process holds its own in-memory
session state, so prefer one frontend per backend process unless you only
need read-only access from the second.
```
