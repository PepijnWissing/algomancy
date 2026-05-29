"""Back-compat re-export.

SessionManager has moved to ``algomancy_scenario`` so it can be reused by
headless frontends (CLI, API) without pulling in Dash. Import it from there in
new code; this module re-exports it to preserve existing import paths.
"""

from algomancy_scenario import SessionManager

__all__ = ["SessionManager"]
