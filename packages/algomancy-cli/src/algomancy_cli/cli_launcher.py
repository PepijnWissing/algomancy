from typing import Dict, Any, Union

from algomancy_scenario.scenariomanager import ScenarioManager
from algomancy_scenario.core_configuration import CoreConfiguration

from .cli_shell import CliShell
from .cli_configuration import CliConfiguration


class CliLauncher:
    @staticmethod
    def build(
        cfg: Union[CliConfiguration, CoreConfiguration, Dict[str, Any]],
    ) -> CliShell:
        """Create a CLI shell from a CliConfiguration/CoreConfiguration or equivalent dict."""
        if isinstance(cfg, dict):
            cfg_obj = CliConfiguration(**cfg)
        elif isinstance(cfg, CliConfiguration):
            cfg_obj = cfg
        elif isinstance(cfg, CoreConfiguration):
            # allow passing a CoreConfiguration; wrap minimally
            cfg_obj = CliConfiguration(**cfg.as_dict())
        else:
            raise TypeError(
                "CliLauncher.build expects CliConfiguration, CoreConfiguration, or dict"
            )

        sm = ScenarioManager.from_config(cfg_obj)
        return CliShell(sm)

    @staticmethod
    def run(shell: CliShell) -> None:
        """Run the interactive shell."""
        shell.run()
