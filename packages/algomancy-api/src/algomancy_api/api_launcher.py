from __future__ import annotations

from typing import Any, Dict, Union

from fastapi import FastAPI

from algomancy_scenario import SessionManager
from algomancy_scenario.core_configuration import CoreConfig

from .api_configuration import ApiConfiguration
from .errors import install_exception_handlers
from .routers import algorithms as algorithms_router
from .routers import scenarios as scenarios_router
from .routers import sessions as sessions_router


class ApiLauncher:
    """Builds and runs the FastAPI app that exposes the scenario-management surface.

    Mirrors :class:`algomancy_cli.cli_launcher.CliLauncher` and
    :class:`algomancy_gui.gui_launcher.GuiLauncher` in shape: a static ``build``
    method that returns the framework's primitive (here, a FastAPI app), and a
    static ``run`` method that hosts it.
    """

    @staticmethod
    def build(
        cfg: Union[ApiConfiguration, CoreConfig, Dict[str, Any]],
    ) -> FastAPI:
        """Construct a FastAPI app from a config (object or dict)."""
        cfg_obj = ApiLauncher._normalize_config(cfg)

        # Always wrap in a SessionManager so all routes share one resolution
        # shape, regardless of cfg.use_sessions. When use_sessions=False the
        # SessionManager just has the single default "main" session.
        session_manager = SessionManager.from_config(cfg_obj)

        app = FastAPI(
            title=cfg_obj.title,
            description=(
                "HTTP interface for Algomancy scenario management. "
                "See /docs for the interactive OpenAPI schema."
            ),
            docs_url="/docs",
            openapi_url="/openapi.json",
        )

        # Stash config + manager on app.state for handlers and Depends() helpers.
        app.state.config = cfg_obj
        app.state.session_manager = session_manager

        install_exception_handlers(app)
        ApiLauncher._install_middleware(app, cfg_obj)
        ApiLauncher._install_routes(app, cfg_obj)
        return app

    @staticmethod
    def run(app: FastAPI, host: str | None = None, port: int | None = None) -> None:
        """Serve the app with uvicorn. ``host``/``port`` default to the app's config."""
        import uvicorn

        cfg: ApiConfiguration = app.state.config
        uvicorn.run(
            app,
            host=host or cfg.host,
            port=port or cfg.port,
        )

    # ---- internals -------------------------------------------------------

    @staticmethod
    def _normalize_config(
        cfg: Union[ApiConfiguration, CoreConfig, Dict[str, Any]],
    ) -> ApiConfiguration:
        if isinstance(cfg, ApiConfiguration):
            return cfg
        if isinstance(cfg, dict):
            return ApiConfiguration(**cfg)
        if isinstance(cfg, CoreConfig):
            return ApiConfiguration(**cfg.as_dict())
        raise TypeError(
            "ApiLauncher.build expects ApiConfiguration, CoreConfig, or dict; "
            f"got {type(cfg).__name__}"
        )

    @staticmethod
    def _install_middleware(app: FastAPI, cfg: ApiConfiguration) -> None:
        if cfg.cors_origins:
            from fastapi.middleware.cors import CORSMiddleware

            app.add_middleware(
                CORSMiddleware,
                allow_origins=cfg.cors_origins,
                allow_methods=["*"],
                allow_headers=["*"],
                allow_credentials=True,
            )

    @staticmethod
    def _install_routes(app: FastAPI, cfg: ApiConfiguration) -> None:
        @app.get("/health", tags=["meta"])
        def health() -> dict:
            sm: SessionManager = app.state.session_manager
            return {
                "status": "ok",
                "title": cfg.title,
                "sessions": sm.sessions_names,
                "use_sessions": cfg.use_sessions,
            }

        app.include_router(sessions_router.router, prefix=cfg.prefix)
        app.include_router(algorithms_router.router, prefix=cfg.prefix)
        app.include_router(scenarios_router.router, prefix=cfg.prefix)
