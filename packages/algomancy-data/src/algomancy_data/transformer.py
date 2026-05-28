"""Transformation primitives for ETL pipelines.

Defines the abstract ``Transformer`` contract and a few simple concrete
transformers, as well as a ``TransformationSequence`` to compose multiple
transformers into a single pipeline step.
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, List, Optional, Sequence, Tuple, Type
from algomancy_utils import Logger
from copy import deepcopy

from .relations import Relation, merge_relations, resolve_relations_from_schemas
from .schema import Schema
from .validator import ValidationMessage, ValidationSeverity


class Transformer(ABC):
    """Base class for a transformation step operating on tabular data.

    Subclasses implement ``transform`` and can mutate the provided mapping of
    DataFrames in-place or return a new mapping where applicable.

    Attributes:
        messages: ValidationMessages produced by this transformer during its
            most recent ``transform`` invocation. The ETL pipeline collects
            these from each transformer in the sequence and folds them into
            the run's ``ValidationResult`` so they surface via
            ``ETLResult.messages``.
    """

    def __init__(self, name: str = "Abstract Transformer", logger=None) -> None:
        self.name = name
        self._logger = logger
        self.messages: List[ValidationMessage] = []

    @abstractmethod
    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        """Apply the transformation to the provided data.

        Args:
            data: Mapping from table name to pandas DataFrame. Implementations
                may mutate this mapping in place or create/replace entries.
        """
        pass


def fill_empty(data: pd.DataFrame) -> pd.DataFrame:
    """Forward-fill missing values across columns in a single row.

    Args:
        data: DataFrame to fill.

    Returns:
        DataFrame with values forward-filled along axis=1.
    """
    return data.ffill(axis=1)


def drop_empty(data: pd.DataFrame) -> pd.DataFrame:
    """Drop rows containing any NA values.

    Args:
        data: Input DataFrame.

    Returns:
        DataFrame without rows containing NA values.
    """
    return data.dropna()


class NoopTransformer(Transformer):
    """Transformer that returns the input data unchanged."""

    def __init__(self, logger=None) -> None:
        super().__init__(name="No Operation Transformer", logger=logger)

    def transform(self, data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        if self._logger:
            self._logger.log("No operation transformer called")
        return data


class CleanTransformer(Transformer):
    """Basic cleanup: drop NA rows and normalize column names to lowercase."""

    def __init__(self, logger=None) -> None:
        super().__init__(name="Standard Transformer", logger=logger)

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        if self._logger:
            self._logger.log("Cleaning dataframes (dropna, lowercase columns)")
        for name, df in data.items():
            df = df.dropna()
            df.columns = [c.lower().strip() for c in df.columns]


class JoinTransformer(Transformer):
    """Join two input tables and write the result to a new table key.

    Attributes:
        left: Name of the left table to join.
        right: Name of the right table to join.
        on: Column name to join on.
        output: Key under which the merged table is stored.
    """

    def __init__(
        self, left: str, right: str, on: str, output: str, logger=None
    ) -> None:
        super().__init__(name="Join transformer", logger=logger)
        self.left = left
        self.right = right
        self.on = on
        self.output = output

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        if self._logger:
            self._logger.log(
                f"Joining '{self.left}' and '{self.right}' on '{self.on}' into '{self.output}'"
            )
        merged = data[self.left].merge(data[self.right], on=self.on)
        data[self.output] = merged


class CascadeDropTransformer(Transformer):
    """Drop rows whose declared foreign-key relations are unsatisfied.

    Reads relations from supplied schemas (default source of truth) and
    optionally merges ``extra_relations`` on top. Iterates to fixpoint, on
    each pass applying:

    1. **Orphan-child drop** (always on) — drop child rows whose FK tuple is
       not in the parent's referenced column set.
    2. **Required-child parent drop** — for relations with
       ``parent_requires_child=True``: drop parent rows whose PK doesn't
       appear in any child's FK column.

    Aggregated ``ValidationMessage``s are emitted with
    :class:`ValidationSeverity.ERROR` — one per ``(table, rule, relation)``
    with the dropped row count.

    Args:
        schemas: Schemas whose ``Column.foreign_key`` declarations supply the
            default relation set.
        extra_relations: Additional or override relations; override wins on
            matching ``(child_table, child_cols)``.
        snapshot: Optional :class:`CascadeSnapshot` paired transformer. Used
            for partial-loss detection (see :class:`CascadeSnapshot`).
        name: Override the transformer's display name.
        logger: Optional logger.
    """

    def __init__(
        self,
        schemas: Optional[Sequence[Type[Schema]]] = None,
        extra_relations: Optional[Sequence[Relation]] = None,
        snapshot: Optional["CascadeSnapshot"] = None,
        name: str = "Cascade drop transformer",
        logger=None,
    ) -> None:
        super().__init__(name=name, logger=logger)
        base: List[Relation] = (
            list(resolve_relations_from_schemas(schemas)) if schemas else []
        )
        self.relations: List[Relation] = merge_relations(
            base, list(extra_relations or [])
        )
        self.snapshot = snapshot

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        self.messages = []
        # Accumulators: {(table, code, fk_label): dropped_count}
        drops: Dict[Tuple[str, str, str], int] = {}

        while True:
            any_drop = False
            for relation in self.relations:
                if (
                    relation.child_table not in data
                    or relation.parent_table not in data
                ):
                    continue

                # --- Orphan-child drop ---
                child_df = data[relation.child_table]
                parent_df = data[relation.parent_table]
                if (
                    not child_df.empty
                    and all(c in child_df.columns for c in relation.child_cols)
                    and all(p in parent_df.columns for p in relation.parent_cols)
                ):
                    parent_keys = set(_row_tuples(parent_df, relation.parent_cols))
                    child_keys = _row_tuples(child_df, relation.child_cols)
                    # Treat any row with NA in FK as "no reference" → keep it.
                    mask_has_value = (
                        child_df[list(relation.child_cols)].notna().all(axis=1)
                    )
                    mask_match = pd.Series(
                        [k in parent_keys for k in child_keys],
                        index=child_df.index,
                    )
                    mask_keep = (~mask_has_value) | mask_match
                    dropped = int((~mask_keep).sum())
                    if dropped > 0:
                        data[relation.child_table] = child_df[mask_keep].reset_index(
                            drop=True
                        )
                        key = (
                            relation.child_table,
                            "CASCADE_ORPHAN_DROP",
                            _relation_label(relation),
                        )
                        drops[key] = drops.get(key, 0) + dropped
                        any_drop = True

                # --- Required-child parent drop ---
                if relation.parent_requires_child:
                    child_df = data[relation.child_table]
                    parent_df = data[relation.parent_table]
                    if not parent_df.empty and all(
                        p in parent_df.columns for p in relation.parent_cols
                    ):
                        referenced_keys: set = set()
                        if not child_df.empty and all(
                            c in child_df.columns for c in relation.child_cols
                        ):
                            child_mask = (
                                child_df[list(relation.child_cols)].notna().all(axis=1)
                            )
                            referenced_keys = set(
                                _row_tuples(child_df[child_mask], relation.child_cols)
                            )
                        parent_keys = _row_tuples(parent_df, relation.parent_cols)
                        mask_keep = pd.Series(
                            [k in referenced_keys for k in parent_keys],
                            index=parent_df.index,
                        )
                        dropped = int((~mask_keep).sum())
                        if dropped > 0:
                            data[relation.parent_table] = parent_df[
                                mask_keep
                            ].reset_index(drop=True)
                            key = (
                                relation.parent_table,
                                "CASCADE_REQUIRED_CHILD_DROP",
                                _relation_label(relation),
                            )
                            drops[key] = drops.get(key, 0) + dropped
                            any_drop = True

            # --- Partial-loss parent drop (only when paired with snapshot) ---
            if self.snapshot is not None:
                partial_drops = self._apply_partial_loss(data)
                if partial_drops:
                    any_drop = True
                    for key, n in partial_drops.items():
                        drops[key] = drops.get(key, 0) + n

            if not any_drop:
                break

        # Emit aggregated messages
        for (table, code, fk_label), dropped_count in drops.items():
            self.messages.append(
                ValidationMessage(
                    ValidationSeverity.ERROR,
                    f"{dropped_count} row(s) dropped from '{table}' "
                    f"by {code} on relation {fk_label}",
                    table=table,
                    code=code,
                )
            )
            if self._logger:
                self._logger.log(
                    f"[CascadeDrop] {dropped_count} row(s) dropped from "
                    f"'{table}' by {code} on {fk_label}"
                )

    def _apply_partial_loss(
        self, data: dict[str, pd.DataFrame]
    ) -> Dict[Tuple[str, str, str], int]:
        """Drop parents whose child-count fell below the snapshot baseline.

        Only relations with ``track_partial_loss=True`` are considered. A
        parent is dropped when its current referenced-child count is lower
        than the count captured in the snapshot but still > 0 (the 0 case is
        already covered by required-child drop or by orphan downstream).
        """
        assert self.snapshot is not None
        partial: Dict[Tuple[str, str, str], int] = {}
        for relation in self.relations:
            if not relation.track_partial_loss:
                continue
            baseline = self.snapshot.counts_for(relation)
            if baseline is None:
                continue
            if relation.parent_table not in data:
                continue
            parent_df = data[relation.parent_table]
            if parent_df.empty or not all(
                p in parent_df.columns for p in relation.parent_cols
            ):
                continue
            child_df = data.get(relation.child_table)
            if child_df is None or child_df.empty:
                current_counts: Dict[Tuple, int] = {}
            elif not all(c in child_df.columns for c in relation.child_cols):
                current_counts = {}
            else:
                mask = child_df[list(relation.child_cols)].notna().all(axis=1)
                current_counts = (
                    child_df[mask].groupby(list(relation.child_cols)).size().to_dict()
                )
                # Normalize single-col dict keys to tuples
                if relation.child_cols and len(relation.child_cols) == 1:
                    current_counts = {(k,): v for k, v in current_counts.items()}

            parent_keys = _row_tuples(parent_df, relation.parent_cols)
            mask_keep = []
            for key in parent_keys:
                base_n = baseline.get(key, 0)
                cur_n = current_counts.get(key, 0)
                if base_n > 0 and 0 < cur_n < base_n:
                    mask_keep.append(False)
                else:
                    mask_keep.append(True)
            mask_keep_s = pd.Series(mask_keep, index=parent_df.index)
            dropped = int((~mask_keep_s).sum())
            if dropped > 0:
                data[relation.parent_table] = parent_df[mask_keep_s].reset_index(
                    drop=True
                )
                key = (
                    relation.parent_table,
                    "CASCADE_PARTIAL_LOSS_DROP",
                    _relation_label(relation),
                )
                partial[key] = partial.get(key, 0) + dropped
        return partial


class CascadeSnapshot(Transformer):
    """Captures referenced-child counts for partial-loss cascade detection.

    A read-only transformer that, for every relation flagged
    ``track_partial_loss=True``, records the number of referencing children
    per parent row. Paired with :class:`CascadeDropTransformer` (passed via
    its ``snapshot=`` argument) to enable the partial-loss drop rule.

    Place this transformer **before** any drop-capable transformer so it
    captures the pre-cleanup baseline.

    Args:
        schemas: Schemas whose foreign-key declarations supply the relation
            set. Only relations with ``track_partial_loss=True`` are tracked.
        extra_relations: Additional or override relations.
        logger: Optional logger.
    """

    def __init__(
        self,
        schemas: Optional[Sequence[Type[Schema]]] = None,
        extra_relations: Optional[Sequence[Relation]] = None,
        logger=None,
    ) -> None:
        super().__init__(name="Cascade snapshot transformer", logger=logger)
        base: List[Relation] = (
            list(resolve_relations_from_schemas(schemas)) if schemas else []
        )
        self.relations: List[Relation] = [
            r
            for r in merge_relations(base, list(extra_relations or []))
            if r.track_partial_loss
        ]
        self._counts: Dict[Tuple[str, Tuple[str, ...]], Dict[Tuple, int]] = {}

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        self.messages = []
        self._counts = {}
        for relation in self.relations:
            if relation.child_table not in data or relation.parent_table not in data:
                continue
            child_df = data[relation.child_table]
            parent_df = data[relation.parent_table]
            if child_df.empty or not all(
                c in child_df.columns for c in relation.child_cols
            ):
                continue
            mask = child_df[list(relation.child_cols)].notna().all(axis=1)
            counts = child_df[mask].groupby(list(relation.child_cols)).size().to_dict()
            if relation.child_cols and len(relation.child_cols) == 1:
                counts = {(k,): v for k, v in counts.items()}
            # Initialise parents not present in child to 0
            parent_keys = (
                _row_tuples(parent_df, relation.parent_cols)
                if all(p in parent_df.columns for p in relation.parent_cols)
                else []
            )
            full = {k: 0 for k in parent_keys}
            full.update(counts)
            self._counts[relation.key] = full

    def counts_for(self, relation: Relation) -> Optional[Dict[Tuple, int]]:
        """Return captured ``{parent_key_tuple: count}`` for the relation, or None."""
        return self._counts.get(relation.key)


def _row_tuples(df: pd.DataFrame, cols: Tuple[str, ...]) -> List[Tuple]:
    """Return a list of column-value tuples (one per row) for the given columns."""
    if not cols:
        return []
    if len(cols) == 1:
        return [(v,) for v in df[cols[0]].tolist()]
    return [tuple(row) for row in df[list(cols)].itertuples(index=False, name=None)]


def _relation_label(relation: Relation) -> str:
    """Compact human-readable label for a relation, used in message text."""
    child = f"{relation.child_table}.{','.join(relation.child_cols)}"
    parent = f"{relation.parent_table}.{','.join(relation.parent_cols)}"
    return f"{child}->{parent}"


class OptionalColumnGuard(Transformer):
    """Materialise missing optional columns using each ``Column.default``.

    Injects missing optional columns into the corresponding DataFrame in-place,
    using ``Column.default`` and coercing to the declared dtype. Downstream
    code can then assume the full schema is present.

    Attributes:
        _schemas: Schemas whose optional columns may be injected.
    """

    def __init__(self, schemas: List, logger=None) -> None:
        super().__init__(name="OptionalColumnGuard", logger=logger)
        self._schemas = schemas

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        from .validator import _schema_table_map

        table_map = _schema_table_map(self._schemas)
        for table_name, schema in table_map.items():
            if table_name not in data:
                continue
            df = data[table_name]
            cols = schema.columns()
            for col_name, col in cols.items():
                if not col.optional or col_name in df.columns:
                    continue
                df[col_name] = col.default
                try:
                    df[col_name] = df[col_name].astype(col.dtype)
                except (ValueError, TypeError):
                    # Default may not be coercible (e.g. None for non-nullable
                    # numerics); leave dtype as-is and let SchemaValidator flag.
                    pass
                if self._logger:
                    self._logger.log(
                        f"Injected optional column '{col_name}' with default into {table_name}."
                    )


class TransformationSequence:
    """A sequence of transformers executed in order."""

    def __init__(
        self, transformers: List[Transformer] = None, logger: Logger = None
    ) -> None:
        self._logger = logger
        self._transformers = transformers or []
        self._completed = False

    def add_transformer(self, transformer: Transformer) -> None:
        """Append a single transformer to the sequence."""
        self._transformers.append(transformer)

    def add_transformers(self, transformers: List[Transformer]) -> None:
        """Append multiple transformers to the sequence."""
        for transformer in transformers:
            self.add_transformer(transformer)

    def run_transformation(
        self, data: dict[str, pd.DataFrame]
    ) -> dict[str, pd.DataFrame]:
        """Run all transformers sequentially on a deepcopy of ``data``.

        Args:
            data: Mapping of tables to DataFrames.

        Returns:
            dict[str, pd.DataFrame]: Transformed copy of the input mapping.
        """
        transformed_data = deepcopy(data)
        for transformer in self._transformers:
            transformer.transform(transformed_data)

        return transformed_data

    def collect_messages(self) -> List[ValidationMessage]:
        """Aggregate ``ValidationMessage``s produced by all transformers.

        Returns messages produced during the most recent
        :meth:`run_transformation` invocation, in transformer order.
        """
        out: List[ValidationMessage] = []
        for t in self._transformers:
            out.extend(getattr(t, "messages", []) or [])
        return out
