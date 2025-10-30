# Algomancy

A lightweight framework for building interactive dashboards to visualize the performance of algorithms and/or simulations across scenarios. It provides data ingestion (ETL), scenario orchestration, KPI computation, and a Dash-based UI with modular pages.

### Overview
- Language/stack: Python 3.11+, Dash (frontend/server), Waitress (production WSGI), PyTest (tests), Ruff (lint). Optional: uv as package manager (uv.lock present).
- Package layout: Installable Python package (setuptools/pyproject). Library entry points are in algomancy/, with an example executable script main-example.py.
- Use cases: Rapid prototyping of algorithm scenario experiments and visual inspection of results.

### Requirements
- Python: 3.11+
- OS: Windows, macOS, or Linux
- Dependencies (core): dash, dash-bootstrap-components, dash-auth (optional), dash-extensions, dash-iconify, pandas, fastparquet, openpyxl, diskcache, strenum, tabulate, waitress, python-dotenv
- Dev/test tools: pytest, ruff, wheel
- Optional tools: uv (if you prefer uv over pip)

## Installation
You can install the published package from the private Azure Artifacts feed (keep this section) or install locally in editable/development mode.

### From Azure Artifacts (requires artifacts-keyring):
- Ensure artifacts-keyring is installed and your credentials are configured for the feed.
- Install Algomancy:
  `pip install --index-url=https://pkgs.dev.azure.com/cqmbv/WARP/_packaging/WarpPython/pypi/simple/ algomancy`

### Local development (from this repository):
- Using pip:
```
  python -m venv .venv
  .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # macOS/Linux
  pip install -U pip setuptools wheel
  pip install -e .
```
- Using uv (optional):
```
  uv venv
  # On Windows PowerShell: . .venv\Scripts\Activate.ps1
  # On macOS/Linux: source .venv/bin/activate
  uv pip install -e .
```
### Running the Example App
This repo includes an example application that exercises the framework components.
- CLI
  python main-example.py --host 127.0.0.1 --port 8050 --threads 8 --connections 100 --debug False
- Defaults
  If flags are omitted, sensible defaults are applied inside main() (e.g., host differs by OS, port=8050).
- After starting, open http://127.0.0.1:8050 (or the host/port you chose) in your browser.

### Programmatic Usage (library)
You can embed Algomancy into your own app using the DashLauncher helper.
- Minimal sketch:
```python
from algomancy.dataengine import DataSource
from algomancy.launcher import DashLauncher

configuration = {
  "assets_path": "assets",
  "data_path": "tests/data",
  "has_persistent_state": True,
  "save_type": "json",
  "data_object_type": DataSource,
  "etl_factory": YourETLFactory,
  "kpi_templates": your_kpi_templates,
  "algo_templates": your_algorithm_templates,
  "input_configs": your_input_configs,
  "autorun": False,
  "home_content": "placeholder",
  "data_content": "placeholder",
  "scenario_content": "placeholder",
  "performance_content": "placeholder",
  "performance_compare": "placeholder",
  "performance_details": "placeholder",
  "overview_content": "placeholder",
  "home_callbacks": None,
  "data_callbacks": None,
  "scenario_callbacks": None,
  "performance_callbacks": None,
  "overview_callbacks": None,
  "styling_config": None,  # see StylingConfigurator for options
  "title": "My Algomancy Dashboard",
  "use_authentication": False,
}

app = DashLauncher.build(configuration)
DashLauncher.run(app, host="127.0.0.1", port=8050, threads=8, connection_limit=100, debug=False)
```
### Environment Variables
- Authentication (optional): If configuration["use_authentication"] is True, set these before launching:
  APP_USERNAME=<username>
  APP_PASSWORD=<password>
  If either is missing, DashLauncher.build will raise a ValueError.
- Other env vars: Not required by default. You may use a .env file with python-dotenv if you extend the app. TODO: Document any project-specific environment variables if/when they are introduced.

### Scripts and Common Commands
- Run example app:
  python main-example.py
- Run tests:
  pytest -q
- Run tests with verbose output:
  pytest -vv
- Lint with Ruff:
  ruff check .
- Format with Ruff (if you choose to enable it):
  ruff format .

### Testing
- Framework uses pytest; tests are under tests/.
- Example dataset is in tests/data and tests/data/example_data.
- Some tests are marked xfail intentionally (e.g., missing setters) to capture current behavior. You can run them as-is to verify baseline expectations.

### Project Structure
High-level layout (non-exhaustive):
- algomancy/                Core package
  - launcher.py             Build and run Dash app (DashLauncher)
  - dataengine/             Data loading, ETL, schema, validation
  - scenarioengine/         Scenario orchestration, algorithms, KPIs
  - components/             Dash UI components and pages
  - contentcreatorlibrary/  Ready-made content creators (examples/standard/placeholder)
  - dashboardlogger/        Logging utilities
  - settingsmanager.py      Shared runtime settings access
  - stylingconfigurator.py  Theme, colors, layout selection
- example_implementation/   Example ETL, pages, and templates
- assets/                   Static assets (images/styles)
- tests/                    PyTest suites and data files
- main-example.py           Example app entry point
- pyproject.toml            Build configuration (setuptools)
- uv.lock                   Lock file for uv (optional)

### Entry Points
- Example executable: main-example.py (CLI and default run)
- Library: DashLauncher in algomancy/launcher.py
- There are no console_scripts defined in pyproject.toml.

### Configuration Notes
- Styling: See algomancy/stylingconfigurator.py for layout and color options.
- Content registration: algomancy/contentcreatorlibrary and algomancy/contentregistry.py provide standard/example/placeholder content.
- Server: DashLauncher.run uses Waitress in non-debug mode; Dash’s built-in server is used for debug.

### Package Management
- The project is defined via pyproject.toml with setuptools. Use pip for installs by default.
- A uv.lock file is present; you may use uv if preferred. This repository does not mandate uv.

### CI/CD
- Pipelines configuration files are present under Pipelines/ (Azure DevOps YAML). TODO: Document pipeline triggers, variables, and publishing steps if relevant.

### License
- License: Restricted (as declared in pyproject.toml). Distribution and usage may be limited. Consult the project owners for permissions.

### Changelog
- See changelog.md for notable changes.

### Contributing
- Open issues and pull requests as needed. Run ruff and pytest locally before pushing.
- TODO: Add contributor guidelines and code style policy if required.

### Support
- Maintainers: See pyproject.toml authors/maintainers fields.
- For private package feed access or deployment, contact project maintainers.
