import json
import shlex
from typing import Any, Callable

from algomancy_scenario import ScenarioManager
from algomancy_utils.logger import MessageStatus


class CliShell:
    """
    Minimal interactive shell to exercise backend functionality via ScenarioManager.

    This is intended for backend development and manual testing without the GUI.
    """

    def __init__(self, scenario_manager: ScenarioManager):
        self.sm = scenario_manager
        self._commands: dict[str, Callable[[list[str]], None]] = {
            "help": self._cmd_help,
            "h": self._cmd_help,
            "?": self._cmd_help,
            "quit": self._cmd_quit,
            "exit": self._cmd_quit,
            "list-scenarios": self._cmd_list_scenarios,
            "ls": self._cmd_list_scenarios,
            "list-data": self._cmd_list_data,
            "ld": self._cmd_list_data,
            "load-data": self._cmd_load_data,
            "etl-data": self._cmd_etl_data,
            "create-scenario": self._cmd_create_scenario,
            "run": self._cmd_run,
            "status": self._cmd_status,
        }
        self._running = False

    # ---------- Public API ----------
    def run(self) -> None:
        self._running = True
        self.sm.log(
            "Algomancy CLI Shell. Type 'help' for available commands.",
            MessageStatus.SUCCESS,
        )
        while self._running:
            try:
                raw = input("algomancy> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not raw:
                continue
            parts = shlex.split(raw)
            cmd, args = parts[0], parts[1:]
            handler = self._commands.get(cmd)
            if handler is None:
                self.sm.log(
                    f"Unknown command: {cmd}. Type 'help' for a list of commands.",
                    MessageStatus.ERROR,
                )
                continue
            try:
                handler(args)
            except Exception as ex:  # keep shell alive during development
                self.sm.log(f"Error: {ex}", MessageStatus.ERROR)

    # ---------- Command handlers ----------
    def _cmd_help(self, _: list[str]) -> None:
        print(
            "\nAvailable commands:\n"
            "  help | h | ?                 Show this help.\n"
            "  quit | exit                  Exit the shell.\n"
            "  list-data | ld               List available datasets.\n"
            "  load-data <name>             Load example data into dataset <name>.\n"
            "  etl-data <name>              Run ETL to create dataset <name>.\n"
            "  list-scenarios | ls          List scenarios.\n"
            "  create-scenario <tag> <dataset_key> <algo> [json_params]\n"
            "                               Create a scenario. Params as JSON object.\n"
            "  run <scenario_id_or_tag>     Run a scenario (waits until complete).\n"
            "  status                        Show processing status.\n"
        )

    def _cmd_quit(self, _: list[str]) -> None:
        self._running = False

    def _cmd_list_data(self, _: list[str]) -> None:
        keys = self.sm.get_data_keys()
        if not keys:
            print("No datasets available.")
            return
        print("Datasets:")
        for k in keys:
            print(f"  - {k}")

    def _cmd_load_data(self, args: list[str]) -> None:
        if len(args) < 1:
            self.sm.log("Usage: load-data <dataset_name>", MessageStatus.WARNING)
            return
        name = args[0]
        self.sm.debug_load_data(name)
        self.sm.log(
            f"Loaded example data into dataset '{name}'.", MessageStatus.SUCCESS
        )

    def _cmd_etl_data(self, args: list[str]) -> None:
        if len(args) < 1:
            self.sm.log("Usage: etl-data <dataset_name>", MessageStatus.WARNING)
            return
        name = args[0]
        self.sm.debug_etl_data(name)
        self.sm.log(
            f"ETL completed, dataset '{name}' available.", MessageStatus.SUCCESS
        )

    def _cmd_list_scenarios(self, _: list[str]) -> None:
        scenarios = self.sm.list_scenarios()
        if not scenarios:
            print("No scenarios defined.")
            return
        print("Scenarios:")
        for s in scenarios:
            print(
                f"  - id={s.id} tag={s.tag} algo={s.algo_name} dataset={s.dataset_key} status={getattr(s, 'status', 'n/a')}"
            )

    def _cmd_create_scenario(self, args: list[str]) -> None:
        if len(args) < 3:
            self.sm.log(
                "Usage: create-scenario <tag> <dataset_key> <algo_name> [json_params]",
                MessageStatus.WARNING,
            )
            return
        tag, dataset_key, algo_name = args[0], args[1], args[2]
        params: dict[str, Any] | None = None
        if len(args) >= 4:
            try:
                params = json.loads(args[3])
            except json.JSONDecodeError:
                self.sm.log("Invalid JSON for parameters.", MessageStatus.ERROR)
                return
        s = self.sm.create_scenario(
            tag=tag, dataset_key=dataset_key, algo_name=algo_name, algo_params=params
        )
        self.sm.log(f"Created scenario id={s.id} tag={s.tag}", MessageStatus.SUCCESS)

    def _resolve_scenario(self, key: str):
        s = self.sm.get_by_id(key)
        if s is None:
            s = self.sm.get_by_tag(key)
        return s

    def _cmd_run(self, args: list[str]) -> None:
        if len(args) < 1:
            self.sm.log("Usage: run <scenario_id_or_tag>", MessageStatus.WARNING)
            return
        identifier = args[0]
        s = self._resolve_scenario(identifier)
        if s is None:
            self.sm.log(f"Scenario '{identifier}' not found.", MessageStatus.ERROR)
            return
        self.sm.process_scenario_async(s)
        self.sm.wait_for_processing()
        self.sm.log(f"Scenario '{s.tag}' completed.", MessageStatus.SUCCESS)

    def _cmd_status(self, _: list[str]) -> None:
        processing = self.sm.currently_processing()
        if processing:
            print("Processing queue:")
            for s in processing:
                print(
                    f"  - id={s.id} tag={s.tag} status={getattr(s, 'status', 'processing')}"
                )
        else:
            print("No scenarios processing.")
