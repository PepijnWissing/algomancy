"""Tests for ``JSONMultiExtractor`` — schema-driven nested JSON extraction."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from algomancy_data import (
    Column,
    ColumnGroup,
    DataType,
    FileExtension,
    JSONFile,
    JSONMultiExtractor,
    Schema,
)
from algomancy_data.schema import SchemaType


# --------------------------------------------------------------------- #
# Schemas for the tests below — modelled on the warehouse pick example.
# --------------------------------------------------------------------- #


class PickSchema(Schema):
    _FILENAME = "picks"
    _EXTENSION = FileExtension.JSON
    _SCHEMA_TYPE = SchemaType.MULTI

    PICK_LOAD_CARRIERS = ColumnGroup(
        "PickLoadCarriers",
        [
            Column("Identity", dtype=DataType.STRING, primary_key=True),
            Column("PickOrderIdentity", dtype=DataType.STRING),
            Column("NumberOfPickOrderLines", dtype=DataType.INTEGER),
        ],
        source_path=(),
    )

    PICK_ORDER_LINES = ColumnGroup(
        "PickOrderLines",
        [
            Column("Identity", dtype=DataType.STRING, primary_key=True),
            Column(
                "PickLoadCarrierIdentity",
                dtype=DataType.STRING,
                foreign_key=("PickLoadCarriers", "Identity"),
            ),
            Column("PickSequence", dtype=DataType.INTEGER),
            Column("OrderedQuantity", dtype=DataType.INTEGER),
        ],
        source_path=("PickOrderLines",),
    )


SAMPLE_DOC = {
    "PickLoadCarriers": [
        {
            "Identity": "29036570",
            "PickOrderIdentity": "113379427",
            "NumberOfPickOrderLines": 2,
            "PickOrderLines": [
                {"Identity": "L1", "PickSequence": 28258, "OrderedQuantity": 1},
                {"Identity": "L2", "PickSequence": 28182, "OrderedQuantity": 1},
            ],
        },
        {
            "Identity": "29036571",
            "PickOrderIdentity": "113379428",
            "NumberOfPickOrderLines": 1,
            "PickOrderLines": [
                {"Identity": "L3", "PickSequence": 27933, "OrderedQuantity": 3},
            ],
        },
    ]
}


def _write_json(tmp_path, payload):
    p = tmp_path / "picks.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return JSONFile(name="picks", path=str(p))


# --------------------------------------------------------------------- #
# Happy path
# --------------------------------------------------------------------- #


class TestHappyPath:
    def test_splits_parent_and_child(self, tmp_path):
        f = _write_json(tmp_path, SAMPLE_DOC)
        ex = JSONMultiExtractor(f, PickSchema)
        out = ex.extract()

        parent_key = "picks.PickLoadCarriers"
        child_key = "picks.PickOrderLines"
        assert set(out.keys()) == {parent_key, child_key}

        parent = out[parent_key]
        child = out[child_key]
        assert len(parent) == 2
        assert len(child) == 3

    def test_parent_drops_nested_list_column(self, tmp_path):
        f = _write_json(tmp_path, SAMPLE_DOC)
        out = JSONMultiExtractor(f, PickSchema).extract()
        parent = out["picks.PickLoadCarriers"]
        assert "PickOrderLines" not in parent.columns

    def test_fk_injection_links_child_to_parent(self, tmp_path):
        f = _write_json(tmp_path, SAMPLE_DOC)
        out = JSONMultiExtractor(f, PickSchema).extract()
        child = out["picks.PickOrderLines"]

        assert "PickLoadCarrierIdentity" in child.columns
        # Rows L1, L2 belong to carrier 29036570; row L3 to 29036571.
        by_identity = dict(zip(child["Identity"], child["PickLoadCarrierIdentity"]))
        assert by_identity == {
            "L1": "29036570",
            "L2": "29036570",
            "L3": "29036571",
        }

    def test_accepts_top_level_list(self, tmp_path):
        f = _write_json(tmp_path, SAMPLE_DOC["PickLoadCarriers"])
        out = JSONMultiExtractor(f, PickSchema).extract()
        assert len(out["picks.PickLoadCarriers"]) == 2
        assert len(out["picks.PickOrderLines"]) == 3


# --------------------------------------------------------------------- #
# Edge cases
# --------------------------------------------------------------------- #


class TestEdges:
    def test_empty_nested_list_yields_empty_child_df(self, tmp_path):
        doc = {
            "PickLoadCarriers": [
                {
                    "Identity": "X",
                    "PickOrderIdentity": "Y",
                    "NumberOfPickOrderLines": 0,
                    "PickOrderLines": [],
                }
            ]
        }
        f = _write_json(tmp_path, doc)
        out = JSONMultiExtractor(f, PickSchema).extract()
        child = out["picks.PickOrderLines"]
        assert len(child) == 0
        # Empty child still preserves the declared columns so downstream
        # consumers (validators, DB backend) don't choke on missing fields.
        for col in ["Identity", "PickLoadCarrierIdentity", "PickSequence"]:
            assert col in child.columns

    def test_missing_nested_key_is_treated_as_empty(self, tmp_path):
        doc = {
            "PickLoadCarriers": [
                {
                    "Identity": "X",
                    "PickOrderIdentity": "Y",
                    "NumberOfPickOrderLines": 0,
                    # PickOrderLines key intentionally absent
                }
            ]
        }
        f = _write_json(tmp_path, doc)
        out = JSONMultiExtractor(f, PickSchema).extract()
        assert len(out["picks.PickOrderLines"]) == 0


# --------------------------------------------------------------------- #
# Schema misconfig is rejected eagerly at construction time
# --------------------------------------------------------------------- #


class TestSchemaMisconfig:
    def test_requires_exactly_one_root_group(self, tmp_path):
        class TwoRoots(Schema):
            _FILENAME = "picks"
            _EXTENSION = FileExtension.JSON
            _SCHEMA_TYPE = SchemaType.MULTI

            A = ColumnGroup(
                "A", [Column("id", DataType.STRING, primary_key=True)], source_path=()
            )
            B = ColumnGroup(
                "B", [Column("id", DataType.STRING, primary_key=True)], source_path=()
            )

        f = _write_json(tmp_path, SAMPLE_DOC)
        with pytest.raises(AssertionError, match="exactly one"):
            JSONMultiExtractor(f, TwoRoots)

    def test_rejects_fk_to_nonexistent_parent_column(self, tmp_path):
        class BadFK(Schema):
            _FILENAME = "picks"
            _EXTENSION = FileExtension.JSON
            _SCHEMA_TYPE = SchemaType.MULTI

            PARENT = ColumnGroup(
                "PickLoadCarriers",
                [Column("Identity", DataType.STRING, primary_key=True)],
                source_path=(),
            )
            CHILD = ColumnGroup(
                "PickOrderLines",
                [
                    Column("Identity", DataType.STRING, primary_key=True),
                    Column(
                        "PickLoadCarrierIdentity",
                        dtype=DataType.STRING,
                        foreign_key=("PickLoadCarriers", "NotARealColumn"),
                    ),
                ],
                source_path=("PickOrderLines",),
            )

        f = _write_json(tmp_path, SAMPLE_DOC)
        with pytest.raises(AssertionError, match="foreign_key"):
            JSONMultiExtractor(f, BadFK)


# --------------------------------------------------------------------- #
# Registry exposes the new extractor for (JSON, MULTI)
# --------------------------------------------------------------------- #


def test_registered_for_json_multi():
    from algomancy_data import get_extractor_class

    cls = get_extractor_class(FileExtension.JSON, SchemaType.MULTI)
    assert cls is JSONMultiExtractor


# --------------------------------------------------------------------- #
# End-to-end via the extractor's own dtype-conversion path
# --------------------------------------------------------------------- #


def test_dtype_conversion_runs_on_each_subtable(tmp_path):
    f = _write_json(tmp_path, SAMPLE_DOC)
    out = JSONMultiExtractor(f, PickSchema).extract()
    parent = out["picks.PickLoadCarriers"]
    child = out["picks.PickOrderLines"]
    # NumberOfPickOrderLines is declared as INTEGER on the parent group.
    assert pd.api.types.is_integer_dtype(parent["NumberOfPickOrderLines"])
    # PickSequence + OrderedQuantity are INTEGER on the child group.
    assert pd.api.types.is_integer_dtype(child["PickSequence"])
    assert pd.api.types.is_integer_dtype(child["OrderedQuantity"])
