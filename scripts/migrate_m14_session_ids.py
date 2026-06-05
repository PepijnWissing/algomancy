"""One-shot migration for M14: session identity → UUID + mutable display_name.

Run this once when upgrading from a pre-M14 algomancy deployment.

Filesystem deployments:
    python scripts/migrate_m14_session_ids.py --data-path /path/to/data

    Writes a ``meta.json`` into each session directory containing a fresh UUID
    ``id`` and the directory name as the initial ``display_name``. Idempotent:
    directories that already have a ``meta.json`` are skipped.

Database deployments:
    python scripts/migrate_m14_session_ids.py --database-url sqlite:///./algomancy.db

    Rewrites ``algomancy_sessions`` from ``(name PK, created_at)`` to
    ``(id TEXT PK, display_name TEXT, created_at)``. Each old ``name`` becomes
    the ``display_name``; a fresh UUID becomes the new ``id``. Updates
    ``algomancy_scenarios.session_id`` to point at the new ids.

    SQLite, PostgreSQL, and MySQL are all supported via SQLAlchemy. The
    migration runs in a single transaction; if it fails partway through the
    table is left in its original shape.

Both backends can be migrated in one invocation by passing both flags.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from typing import Iterable


META_FILENAME = "meta.json"


def migrate_filesystem(data_path: str) -> int:
    """Write meta.json into each session directory under data_path."""
    if not os.path.isdir(data_path):
        print(f"[fs] data_path does not exist or is not a directory: {data_path}")
        return 1

    written = 0
    skipped = 0
    for entry in sorted(os.scandir(data_path), key=lambda e: e.name):
        if not entry.is_dir():
            continue
        meta_path = os.path.join(entry.path, META_FILENAME)
        if os.path.isfile(meta_path):
            skipped += 1
            continue
        meta = {"id": str(uuid.uuid4()), "display_name": entry.name}
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        print(f"[fs] wrote {meta_path} (id={meta['id']})")
        written += 1
    print(f"[fs] done: {written} written, {skipped} already migrated")
    return 0


def migrate_database(database_url: str) -> int:
    """Rewrite algomancy_sessions to the (id, display_name) schema."""
    try:
        import sqlalchemy as sa
    except ImportError:
        print("[db] SQLAlchemy is required: pip install algomancy-scenario[database]")
        return 1

    engine = sa.create_engine(database_url)
    metadata = sa.MetaData()
    metadata.reflect(
        bind=engine, only=_only_tables(["algomancy_sessions", "algomancy_scenarios"])
    )

    sessions = metadata.tables.get("algomancy_sessions")
    if sessions is None:
        print("[db] no algomancy_sessions table; nothing to migrate")
        return 0

    cols = {c.name for c in sessions.columns}
    if "id" in cols and "display_name" in cols:
        print("[db] algomancy_sessions already on the new schema; nothing to do")
        return 0

    if "name" not in cols:
        print(
            "[db] algomancy_sessions has neither 'name' nor 'id'/'display_name'; "
            "cannot determine source columns. Aborting."
        )
        return 1

    print(f"[db] migrating algomancy_sessions on {engine.dialect.name}")
    with engine.begin() as conn:
        rows = conn.execute(
            sa.text("SELECT name, created_at FROM algomancy_sessions")
        ).fetchall()
        mapping = {row.name: str(uuid.uuid4()) for row in rows}
        print(f"[db] {len(mapping)} session rows to relabel")

        scenarios = metadata.tables.get("algomancy_scenarios")
        if scenarios is not None:
            for old_name, new_id in mapping.items():
                conn.execute(
                    sa.text(
                        "UPDATE algomancy_scenarios SET session_id = :new "
                        "WHERE session_id = :old"
                    ),
                    {"new": new_id, "old": old_name},
                )

        # Schema rewrite: drop old table, create new, insert relabeled rows.
        conn.execute(
            sa.text("ALTER TABLE algomancy_sessions RENAME TO _algomancy_sessions_old")
        )
        conn.execute(
            sa.text(
                "CREATE TABLE algomancy_sessions ("
                "id VARCHAR NOT NULL PRIMARY KEY, "
                "display_name VARCHAR NOT NULL, "
                "created_at TIMESTAMP NULL)"
            )
        )
        for old_name, new_id in mapping.items():
            created_at = next(r.created_at for r in rows if r.name == old_name)
            conn.execute(
                sa.text(
                    "INSERT INTO algomancy_sessions (id, display_name, created_at) "
                    "VALUES (:id, :name, :ts)"
                ),
                {"id": new_id, "name": old_name, "ts": created_at},
            )
        conn.execute(sa.text("DROP TABLE _algomancy_sessions_old"))

    print("[db] migration complete")
    return 0


def _only_tables(names: Iterable[str]):
    wanted = set(names)
    return lambda table_name, _: table_name in wanted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-path",
        default=None,
        help="Filesystem data folder containing per-session directories.",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="SQLAlchemy URL for the database backend (e.g. sqlite:///./algomancy.db).",
    )
    args = parser.parse_args(argv)
    if not args.data_path and not args.database_url:
        parser.error("Specify at least one of --data-path or --database-url")

    rc = 0
    if args.data_path:
        rc |= migrate_filesystem(args.data_path)
    if args.database_url:
        rc |= migrate_database(args.database_url)
    return rc


if __name__ == "__main__":
    sys.exit(main())
