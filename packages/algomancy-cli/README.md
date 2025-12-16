Algomancy CLI

Interactive terminal shell to exercise Algomancy backend functionality without the GUI. Useful for rapid development of ETL, algorithms, and scenarios.

Install / Run

```
uv run algomancy-cli --example
```

Or point to your own configuration factory:

```
uv run algomancy-cli --config-callback myproject.config:make_config
```

Where `make_config` returns an `AppConfiguration` instance.

Commands

- `help` — show help
- `list-data` / `ld` — list datasets
- `load-data <name>` — load example data into dataset `<name>`
- `etl-data <name>` — run ETL to create dataset `<name>`
- `list-scenarios` / `ls` — list scenarios
- `create-scenario <tag> <dataset_key> <algo_name> [json_params]` — create scenario
- `run <scenario_id_or_tag>` — run scenario and wait for completion
- `status` — show processing status
- `quit` / `exit` — exit shell

Parameters for `create-scenario` can be provided as a JSON object, e.g.:

```
create-scenario test1 "Master data" Fast "{\"duration\": 0.5}"
```

How it works

The CLI wraps `ScenarioManager` created via `AppConfiguration` just like the GUI launcher. See `src/algomancy/cli_launcher.py` for details.
