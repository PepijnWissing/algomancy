# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Package manager:** `uv` (not pip/poetry). All commands run from the repo root.

```bash
# Install all workspace packages
uv sync --frozen

# Run tests
uv run pytest tests -v                                    # root tests
uv run pytest packages/algomancy-data/tests -v            # single package
uv run pytest packages/algomancy-scenario/tests -v

# Lint/format (via pre-commit)
pre-commit run --all-files

# Run example app
uv run python example/main.py                             # opens at http://127.0.0.1:8050

# Build documentation (from docs/)
uv run sphinx-build -b html docs/source docs/build/html

# Version bump (updates version across all packages)
uv run python algomancy-version-bump.py
```

## Architecture

Algomancy is a **uv workspace** of 7 modular packages (`packages/algomancy-*/`) plus a thin root package (`src/algomancy/`). Users build dashboards by subclassing framework base classes and wiring them into `AppConfig`. The same backend (`ScenarioManager` / `SessionManager`) is reachable through two interchangeable frontends — Dash GUI or HTTP API.

### Package responsibilities

| Package | Role |
|---|---|
| `algomancy-data` | ETL pipeline, data containers (`DataSource`), schemas, `DataManager` |
| `algomancy-scenario` | Scenario lifecycle, `BaseAlgorithm`, `BaseParameterSet`, `BaseKPI`, `SessionManager` |
| `algomancy-gui` | Dash app assembly, `AppConfig`, `GuiLauncher`, styling/theming |
| `algomancy-content` | Pre-built page templates, placeholder implementations |
| `algomancy-api` | FastAPI HTTP service exposing scenario/data management for remote frontends |
| `algomancy-utils` | Shared helpers |
| `algomancy-quickstart` | Project scaffolding (`algomancy-quickstart` CLI) |

### Data flow

```
User's custom code (subclasses of BaseAlgorithm, BaseKPI, ETLFactory, Transformer)
    ↓
AppConfig (central config object: data paths, algorithms, KPIs, styling)
    ↓
GuiLauncher.build() → Dash app with pages
    ↓
Data page → DataManager → ETLFactory → Extractor/Transformer/Loader → DataSource
Scenario page → Scenario lifecycle → BaseAlgorithm.run() → BaseKPI.compute()
```

The `algomancy-api` package serves the same backend as JSON over HTTP — useful for remote frontends and headless backend testing. Launch with `ApiLauncher.build(ApiConfiguration(...))` + `ApiLauncher.run(app)` (default port `8051`). Routes under `/api/v1/sessions/{session_id}/...` cover the full scenario lifecycle (CRUD + run + poll), data management, and algorithm/KPI discovery. OpenAPI schema at `/openapi.json`, Swagger UI at `/docs`.

### Extension points

Users implement the framework by subclassing:
- `BaseAlgorithm` + `BaseParameterSet` (scenario logic)
- `BaseKPI` (metrics computation)
- `ETLFactory` / `Transformer` / `Extractor` (data ingestion)
- Dash page classes from `algomancy-gui` (custom pages)

See `example/` for a complete reference implementation.

## Documentation

Source lives in `docs/source/` as Markdown (MyST). Sphinx with the Furo theme. Hosted on Read the Docs at https://algomancy.readthedocs.io.

API reference is auto-generated from Google-style docstrings via `sphinx.ext.autodoc`.

## Versioning

All 7 packages share a single version number (currently `0.7.0`). Use `algomancy-version-bump.py` to update all `pyproject.toml` files at once — do not edit package versions manually.