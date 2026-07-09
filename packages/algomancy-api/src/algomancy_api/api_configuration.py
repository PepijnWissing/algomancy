from __future__ import annotations

from typing import Any, Dict, List, Union

from algomancy_scenario.core_configuration import CoreConfig


class ApiConfiguration(CoreConfig):
    """Configuration for the HTTP API server.

    Extends :class:`CoreConfig` with HTTP-specific options: bind host/port,
    URL prefix, CORS origins, and session-creation policy.
    """

    def __init__(
        self,
        # core parameters (see CoreConfig)
        data_path: str = "data",
        has_persistent_state: bool = False,
        save_type: str | None = "json",
        data_object_type: type | None = None,
        etl_factory: Any | None = None,
        kpis: Dict[str, Any] | None = None,
        algorithms: Dict[str, Any] | None = None,
        schemas: list | None = None,
        autocreate: bool | None = None,
        default_algo: str | None = None,
        default_algo_params_values: Dict[str, Any] | None = None,
        autorun: bool | None = None,
        title: str = "Algomancy API",
        # API specific
        host: str = "127.0.0.1",
        port: int = 8051,
        prefix: str = "/api/v1",
        cors_origins: List[str] | None = None,
        allow_session_create: bool = True,
        forwarded_allow_ips: Union[str, List[str], None] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data_path=data_path,
            has_persistent_state=has_persistent_state,
            save_type=save_type,
            data_object_type=data_object_type,
            etl_factory=etl_factory,
            kpis=kpis,
            algorithms=algorithms,
            schemas=schemas,
            autocreate=autocreate,
            default_algo=default_algo,
            default_algo_params_values=default_algo_params_values,
            autorun=autorun,
            title=title,
            **kwargs,
        )
        self.host = host
        self.port = port
        self.prefix = prefix
        self.cors_origins = list(cors_origins) if cors_origins else []
        self.allow_session_create = allow_session_create
        self.forwarded_allow_ips = self._normalize_forwarded_allow_ips(
            forwarded_allow_ips
        )
        self._validate_api()

    def as_dict(self) -> Dict[str, Any]:
        base = super().as_dict()
        base.update(
            {
                "host": self.host,
                "port": self.port,
                "prefix": self.prefix,
                "cors_origins": list(self.cors_origins),
                "allow_session_create": self.allow_session_create,
                "forwarded_allow_ips": self.forwarded_allow_ips,
            }
        )
        return base

    @staticmethod
    def _normalize_forwarded_allow_ips(
        value: Union[str, List[str], None],
    ) -> Union[str, List[str], None]:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return list(value)
        raise ValueError(
            "forwarded_allow_ips must be None, a string, or a list of strings"
        )

    def _validate_api(self) -> None:
        if not isinstance(self.host, str) or not self.host:
            raise ValueError("host must be a non-empty string")
        if not isinstance(self.port, int) or not (0 < self.port < 65536):
            raise ValueError("port must be an integer in (0, 65536)")
        if not isinstance(self.prefix, str) or not self.prefix.startswith("/"):
            raise ValueError("prefix must be a string starting with '/'")
        if any(not isinstance(o, str) or not o for o in self.cors_origins):
            raise ValueError("cors_origins entries must be non-empty strings")
        if not isinstance(self.allow_session_create, bool):
            raise ValueError("allow_session_create must be a bool")
        if self.forwarded_allow_ips is not None:
            if isinstance(self.forwarded_allow_ips, str):
                if not self.forwarded_allow_ips.strip():
                    raise ValueError(
                        "forwarded_allow_ips must be a non-empty string when provided"
                    )
            elif isinstance(self.forwarded_allow_ips, list):
                if not self.forwarded_allow_ips or any(
                    not isinstance(o, str) or not o.strip()
                    for o in self.forwarded_allow_ips
                ):
                    raise ValueError(
                        "forwarded_allow_ips list entries must be non-empty strings"
                    )
            else:
                raise ValueError(
                    "forwarded_allow_ips must be None, a string, or a list of strings"
                )
