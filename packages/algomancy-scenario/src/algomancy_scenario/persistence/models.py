"""Fixed SQLAlchemy table definitions for algomancy-scenario's database backend.

Covers sessions, scenario definitions, per-run execution history, and KPI
measurements. Per-result data rows live in shared per-sub-table tables (one
physical table per ScenarioResult sub-table *name*, across all sessions and
scenarios); those tables are created lazily by ``SqlScenarioRepository`` on
first write because pandas infers their column types from the DataFrame.
"""

import sqlalchemy as sa

metadata = sa.MetaData()

#: Prefix for the shared result tables (one per ScenarioResult sub-table name).
RESULT_TABLE_PREFIX = "algomancy_result__"

#: Discriminator columns prepended to every shared result table row.
SESSION_COL = "_algomancy_session_id"
SCENARIO_COL = "_algomancy_scenario_id"

sessions_table = sa.Table(
    "algomancy_sessions",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("display_name", sa.String, nullable=False),
    sa.Column("created_at", sa.DateTime, nullable=True),
)

scenarios_table = sa.Table(
    "algomancy_scenarios",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("tag", sa.String, nullable=False),
    sa.Column("session_id", sa.String, nullable=False),
    sa.Column("input_data_key", sa.String, nullable=False),
    sa.Column("algorithm_name", sa.String, nullable=False),
    sa.Column("parameter_values", sa.Text, nullable=True),  # JSON
    sa.Column(
        "data_parameter_values", sa.Text, nullable=True
    ),  # JSON, nullable for back-compat
    sa.Column("kpi_names", sa.Text, nullable=True),  # JSON array
    sa.Column("status", sa.String, nullable=False),
    sa.Column("created_at", sa.DateTime, nullable=True),
)

scenario_runs_table = sa.Table(
    "algomancy_scenario_runs",
    metadata,
    sa.Column("run_id", sa.String, primary_key=True),
    sa.Column(
        "scenario_id",
        sa.String,
        sa.ForeignKey("algomancy_scenarios.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("started_at", sa.DateTime, nullable=True),
    sa.Column("finished_at", sa.DateTime, nullable=True),
    sa.Column("status", sa.String, nullable=False),
    sa.Column("result_blob", sa.Text, nullable=True),  # JSON from result.to_dict()
    sa.Column("error", sa.Text, nullable=True),
    # JSON array of sub-table names this run wrote rows to in the shared
    # ``algomancy_result__<sub>`` tables. NULL when the JSON-blob path is used.
    sa.Column("result_sub_tables", sa.Text, nullable=True),
)

kpi_measurements_table = sa.Table(
    "algomancy_kpi_measurements",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column(
        "run_id",
        sa.String,
        sa.ForeignKey("algomancy_scenario_runs.run_id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("kpi_name", sa.String, nullable=False),
    sa.Column("value", sa.Float, nullable=True),
    sa.Column("threshold", sa.Float, nullable=True),
    sa.Column("direction", sa.String, nullable=True),
    sa.Column("computed_at", sa.DateTime, nullable=True),
)
