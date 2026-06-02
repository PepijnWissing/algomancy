"""Fixed SQLAlchemy table definitions for algomancy-scenario's database backend.

Covers sessions, scenario definitions, per-run execution history, and KPI
measurements. These tables ARE managed by Alembic migrations (unlike the
dynamic per-DataSource data tables in algomancy-data).
"""

import sqlalchemy as sa

metadata = sa.MetaData()

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
