"""Fixed SQLAlchemy table definitions for algomancy-data's database backend.

Only the metadata catalogue lives here. Data rows live in shared per-sub-table
tables (one physical table per DataSource sub-table *name*, across all sessions
and datasets); those tables are created lazily by ``DatabaseDataManager`` on
first write because pandas infers the column types from the DataFrame.
"""

import sqlalchemy as sa

metadata = sa.MetaData()

#: Prefix for the shared data tables (one per DataSource sub-table name).
DATA_TABLE_PREFIX = "algomancy_ds__"

#: Discriminator columns prepended to every shared data table row.
SESSION_COL = "_algomancy_session_id"
DATASET_COL = "_algomancy_dataset_name"

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
    # NULL, the DataSource's rows live in the shared ``algomancy_ds__<sub>``
    # tables and ``sub_tables`` lists which ones to load.
    sa.Column("payload", sa.Text, nullable=True),
    # JSON array of sub-table names this dataset writes to. NULL when the
    # JSON-blob path is used.
    sa.Column("sub_tables", sa.Text, nullable=True),
)
