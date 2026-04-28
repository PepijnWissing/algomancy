import platform
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ServerConfig:
    """
    Server and deployment settings.

    Args:
        host: Server host (str), defaults to "127.0.0.1"
        port: Server port (int) defaults to 8050

    """

    host: str | None = None
    port: int = 8050

    def __post_init__(self):
        self._set_default_host()
        self._validate()

    def _set_default_host(self):
        if self.host is None:
            self.host = "127.0.0.1" if platform.system() == "Windows" else "0.0.0.1"

    def _validate(self) -> None:
        """Validate server configuration."""
        if self.port is not None:
            if not isinstance(self.port, int) or not (1 <= self.port <= 65535):
                raise ValueError("port must be an integer between 1 and 65535")

    def as_dict(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
        }
