"""Relation declarations between tables for cascade-cleanup and FK validation.

A :class:`Relation` captures a foreign-key reference from one table's column(s)
to another table's column(s). Relations are typically derived from
:class:`Column.foreign_key` declarations on user schemas via
:func:`resolve_relations_from_schemas`, but can also be constructed explicitly
to override or extend the schema-derived set.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple, Type

from .schema import Schema


@dataclass(frozen=True)
class Relation:
    """A foreign-key relation between a child table and a parent table.

    Used by :class:`CascadeDropTransformer` (cascade cleanup) and
    :class:`ForeignKeyValidator.from_schemas` (FK violation reporting).
    Typically built from ``Column.foreign_key`` declarations via
    :func:`resolve_relations_from_schemas`, but can be constructed
    explicitly to override or extend the schema-derived set.
    """

    #: Logical name of the child table (matches ``Schema.file_name()``).
    child_table: str
    #: Tuple of column names on the child table that form the FK.
    child_cols: Tuple[str, ...]
    #: Logical name of the parent (referenced) table.
    parent_table: str
    #: Tuple of column names on the parent table forming the referenced key.
    parent_cols: Tuple[str, ...]
    #: If True, parents with zero referencing children are dropped.
    parent_requires_child: bool = False
    #: If True, enables partial-loss cascade when paired with a snapshot.
    track_partial_loss: bool = False

    @property
    def key(self) -> Tuple[str, Tuple[str, ...]]:
        """Identity used when merging relations: ``(child_table, child_cols)``."""
        return (self.child_table, self.child_cols)


def resolve_relations_from_schemas(
    schemas: Sequence[Type[Schema]],
) -> List[Relation]:
    """Build a list of :class:`Relation` objects from FK declarations on schemas.

    Walks the ``Column.foreign_key`` declarations on each schema and groups
    columns sharing the same parent table into composite FKs. Within a
    single schema, all columns with ``foreign_key`` pointing at the same
    parent table are collapsed into one composite relation; the referenced
    parent columns are taken from each column's ``foreign_key`` tuple in
    declaration order.

    Args:
        schemas: Iterable of ``Schema`` subclasses to walk.

    Returns:
        List of relations, deduplicated by ``(child_table, child_cols)``.
    """
    # Group columns per (child_table, parent_table) into composite FKs.
    grouped: Dict[Tuple[str, str], Dict[str, object]] = {}

    for schema in schemas:
        # Foreign keys are declared on flat (SINGLE) schemas via Column.
        # MULTI schemas group columns per sheet and don't participate in
        # cascade relations — skip them so callers can pass a mixed list.
        if not schema.is_single():
            continue
        child_table = schema.file_name()
        for col_name, col in schema.columns().items():
            if col.foreign_key is None:
                continue
            parent_table, parent_col = col.foreign_key
            key = (child_table, parent_table)
            entry = grouped.setdefault(
                key,
                {
                    "child_cols": [],
                    "parent_cols": [],
                    "parent_requires_child": False,
                    "track_partial_loss": False,
                },
            )
            entry["child_cols"].append(col_name)
            entry["parent_cols"].append(parent_col)
            if col.parent_requires_child:
                entry["parent_requires_child"] = True
            if col.track_partial_loss:
                entry["track_partial_loss"] = True

    relations: List[Relation] = []
    for (child_table, parent_table), entry in grouped.items():
        relations.append(
            Relation(
                child_table=child_table,
                child_cols=tuple(entry["child_cols"]),
                parent_table=parent_table,
                parent_cols=tuple(entry["parent_cols"]),
                parent_requires_child=bool(entry["parent_requires_child"]),
                track_partial_loss=bool(entry["track_partial_loss"]),
            )
        )
    return relations


def merge_relations(
    base: Sequence[Relation], override: Sequence[Relation]
) -> List[Relation]:
    """Merge two relation lists; ``override`` wins on matching ``(child_table, child_cols)``.

    Args:
        base: Base relations (typically schema-derived).
        override: Override relations (typically user-supplied extras).

    Returns:
        Combined list. Entries from ``override`` replace entries from ``base``
        with the same ``key``; remaining entries from ``override`` are appended.
    """
    by_key: Dict[Tuple[str, Tuple[str, ...]], Relation] = {r.key: r for r in base}
    for r in override:
        by_key[r.key] = r
    return list(by_key.values())
