# Algomancy

Algomancy is a lightweight framework for building interactive dashboards that visualize the performance of algorithms and/or simulations across scenarios. It brings together ETL, scenario orchestration, KPI computation, and three interchangeable frontends: a Dash-based UI, an interactive shell, and an HTTP API.

## Highlights
- Python 3.14+
- Dash UI with modular pages and a production-ready server
- FastAPI HTTP service for remote frontends and headless integrations
- Batteries-included packages: content, data, scenario, GUI, CLI, API


## Features and Capabilities
- **Modular Backend**: Easy to swap algorithms or data models.
- **Three Frontends, One Backend**: The same `ScenarioManager` is reachable through the Dash GUI, a CLI shell, or a FastAPI HTTP service — choose at startup time.
- **Automated ETL**: Structured data intake from various file formats.
- **Parameter Management**: Type-safe, validated parameters with automatic GUI generation.
- **Asynchronous Execution**: Background processing of scenarios with real-time progress tracking.
- **Extensive Logging**: Integrated logger for tracking algorithm execution and debugging.
- **Scalable Results**: Support for complex result models and automated KPI computation.

## Roadmap
- **Visualization Library**: A collection of reusable components for common data types (e.g., Gantt charts, maps).
- **Persistent Storage**: Improved database integration for long-term scenario storage.
- **Multi-user Support**: Collaborative features for shared scenario analysis.

```{toctree}
:maxdepth: 2
:hidden:

getting_started/quickstart
fundamentals/fundamentals
tutorial/tutorial
reference/reference
contributing
migration
changelog
```
 