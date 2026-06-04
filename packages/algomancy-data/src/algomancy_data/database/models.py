"""Fixed SQLAlchemy table definitions for algomancy-data's database backend.

Only the metadata catalogue lives here. Per-DataSource data tables are created
dynamically by DatabaseDataManager using names derived from the session / dataset /
sub-table triple, so they are intentionally NOT declared here and not managed by
Alembic migrations.
"""

import sqlalchemy as sa

metadata = sa.MetaData()

datasets_table = sa.Table(
    "algomancy_datasets",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("name", sa.String, nullable=False),
    sa.Column("session_id", sa.String, nullable=False),
    sa.Column("ds_type", sa.String, nullable=False),
    sa.Column("creation_datetime", sa.DateTime, nullable=True),
    # Populated only when the row was persisted via the JSON-blob fallback path,
    # i.e. when the DataSource subclass does NOT implement SqlTableLayout. When
    # NULL, the DataSource's tables live in per-sub-table ds__... SQL tables.
    sa.Column("payload", sa.Text, nullable=True),
)
