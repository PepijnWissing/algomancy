"""Quickstart nested-JSON detection + rendering tests.

Exercises the SchemaInferenceEngine path that scans a JSON file for
list-of-objects children, prompts the user, and (on consent) populates
``DataFileInfo`` with parent + child ColumnGroup metadata. Also covers
the generated_schemas template emitting ``source_path`` and
``foreign_key`` correctly so the rendered schema is loadable by
``JSONMultiExtractor`` at runtime.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from jinja2 import Environment, PackageLoader, select_autoescape

from algomancy_data import (
    Column,
    ColumnGroup,
    DataType,
    FileExtension,
    JSONFile,
    JSONMultiExtractor,
    Schema,
    SimpleETLFactory,
)
from algomancy_data.schema import SchemaType
from algomancy_quickstart.data_inference import DataFileInfo, SchemaInferenceEngine
from algomancy_quickstart.quickstart import QuickstartWizard


SAMPLE_NESTED_JSON = {
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


@pytest.fixture
def jinja_env() -> Environment:
    return Environment(
        loader=PackageLoader("algomancy_quickstart", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _write(tmp_path: Path, payload, name: str = "picks") -> DataFileInfo:
    p = tmp_path / f"{name}.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return DataFileInfo(file_path=p, file_name=name, extension=FileExtension.JSON)


# --------------------------------------------------------------------- #
# Detection & DataFileInfo population
# --------------------------------------------------------------------- #


class TestDetection:
    def test_detects_list_of_objects(self, tmp_path):
        engine = SchemaInferenceEngine()
        info = _write(tmp_path, SAMPLE_NESTED_JSON)
        with patch("click.confirm", return_value=True):
            assert engine._infer_schema_with_config(info) is True

        # Parent + one child group; FK populated on the child.
        assert info.is_nested_json
        assert info.is_multi_table
        assert "PickLoadCarriers" in info.inferred_schemas
        assert "PickOrderLines" in info.inferred_schemas
        assert info.nested_source_paths == {
            "PickLoadCarriers": (),
            "PickOrderLines": ("PickOrderLines",),
        }
        assert info.nested_foreign_keys["PickOrderLines"] == {
            "PickLoadCarriersIdentity": ("PickLoadCarriers", "Identity"),
        }

    def test_user_declines_falls_back_to_flat(self, tmp_path):
        engine = SchemaInferenceEngine()
        info = _write(tmp_path, SAMPLE_NESTED_JSON)
        with patch("click.confirm", return_value=False):
            assert engine._infer_schema_with_config(info) is True

        assert not info.is_nested_json
        assert info.inferred_schemas == {"default": info.inferred_schemas["default"]}

    def test_no_parent_pk_skips_split_without_prompting(self, tmp_path):
        # Parent records have no obvious PK column (no Id-like fields).
        payload = {
            "Carriers": [
                {"Name": "A", "Lines": [{"x": 1}, {"x": 2}]},
                {"Name": "B", "Lines": [{"x": 3}]},
            ]
        }
        engine = SchemaInferenceEngine()
        info = _write(tmp_path, payload, name="noPK")
        with patch("click.confirm") as confirm:
            engine._infer_schema_with_config(info)
            confirm.assert_not_called()

        assert not info.is_nested_json
        assert "default" in info.inferred_schemas

    def test_flat_json_unchanged(self, tmp_path):
        engine = SchemaInferenceEngine()
        info = _write(tmp_path, [{"id": "a", "v": 1}, {"id": "b", "v": 2}], name="flat")
        with patch("click.confirm") as confirm:
            engine._infer_schema_with_config(info)
            confirm.assert_not_called()

        assert not info.is_nested_json
        assert set(info.inferred_schemas["default"].keys()) == {"id", "v"}


# --------------------------------------------------------------------- #
# Template rendering
# --------------------------------------------------------------------- #


class TestTemplate:
    def test_renders_source_path_and_foreign_key(self, tmp_path, jinja_env):
        engine = SchemaInferenceEngine()
        info = _write(tmp_path, SAMPLE_NESTED_JSON)
        with patch("click.confirm", return_value=True):
            engine._infer_schema_with_config(info)
        info.total_columns = sum(len(c) for c in info.inferred_schemas.values())

        tmpl = jinja_env.get_template("generated_schemas.py.jinja")
        rendered = tmpl.render(project_name="Demo", files=[info])

        # Parses + uses MULTI + carries the new fields.
        ast.parse(rendered)
        assert "SchemaType.MULTI" in rendered
        assert 'source_path=("PickOrderLines",)' in rendered
        assert 'foreign_key=("PickLoadCarriers", "Identity")' in rendered

    def test_rendered_schema_is_loadable_by_jsonmultiextractor(
        self, tmp_path, jinja_env
    ):
        """End-to-end: render the schema, exec it, hand it to the live
        ``JSONMultiExtractor``, and confirm the parent/child split happens
        on the same sample JSON."""
        engine = SchemaInferenceEngine()
        info = _write(tmp_path, SAMPLE_NESTED_JSON)
        with patch("click.confirm", return_value=True):
            engine._infer_schema_with_config(info)
        info.total_columns = sum(len(c) for c in info.inferred_schemas.values())

        tmpl = jinja_env.get_template("generated_schemas.py.jinja")
        rendered = tmpl.render(project_name="Demo", files=[info])

        ns: dict = {}
        exec(  # noqa: S102 - controlled template output, no user code
            compile(rendered, "<generated_schemas>", "exec"), ns, ns
        )
        SchemaCls = ns["PicksSchema"]
        assert SchemaCls.is_multi()
        assert "Identity" in SchemaCls.column_groups()["PickLoadCarriers"]
        assert "PickLoadCarriersIdentity" in SchemaCls.column_groups()["PickOrderLines"]

        # Run it through the live extractor and check the split.
        f = JSONFile(name="picks", path=str(info.file_path))
        out = JSONMultiExtractor(f, SchemaCls).extract()
        assert len(out["picks.PickLoadCarriers"]) == 2
        assert len(out["picks.PickOrderLines"]) == 3
        # FK populated from parent's Identity.
        child = out["picks.PickOrderLines"]
        by_id = dict(zip(child["Identity"], child["PickLoadCarriersIdentity"]))
        assert by_id == {"L1": "29036570", "L2": "29036570", "L3": "29036571"}

    def test_rendered_schema_survives_full_etl_pipeline(self, tmp_path, jinja_env):
        """Regression for issue #172: the rendered MULTI schema must also
        survive ``SimpleETLFactory.build_pipeline().run()`` end-to-end, not
        just direct extraction. The previous validator gate at
        ``etl.py:339`` invoked ``primary_key()`` on the MULTI schema and
        crashed via the SINGLE-only ``columns()`` path.
        """
        engine = SchemaInferenceEngine()
        info = _write(tmp_path, SAMPLE_NESTED_JSON)
        with patch("click.confirm", return_value=True):
            engine._infer_schema_with_config(info)
        info.total_columns = sum(len(c) for c in info.inferred_schemas.values())

        tmpl = jinja_env.get_template("generated_schemas.py.jinja")
        rendered = tmpl.render(project_name="Demo", files=[info])

        ns: dict = {}
        exec(  # noqa: S102 - controlled template output, no user code
            compile(rendered, "<generated_schemas>", "exec"), ns, ns
        )
        SchemaCls = ns["PicksSchema"]

        files = {"picks": JSONFile(name="picks", path=str(info.file_path))}
        result = (
            SimpleETLFactory(schemas=[SchemaCls]).build_pipeline("picks", files).run()
        )

        assert result.is_success, [m.message for m in result.messages]
        parent = result.datasource.get_table("picks.PickLoadCarriers")
        child = result.datasource.get_table("picks.PickOrderLines")
        assert len(parent) == 2
        assert len(child) == 3


# --------------------------------------------------------------------- #
# Summary rendering (issue #171)
# --------------------------------------------------------------------- #


class TestSummaryDisplay:
    def _build_wizard_with_nested(self, tmp_path: Path) -> QuickstartWizard:
        engine = SchemaInferenceEngine()
        info = _write(tmp_path, SAMPLE_NESTED_JSON)
        with patch("click.confirm", return_value=True):
            engine._infer_schema_with_config(info)
        info.total_columns = sum(len(c) for c in info.inferred_schemas.values())

        wizard = QuickstartWizard(skip_confirmation=True)
        wizard.current_dir = tmp_path
        wizard.detected_files = [info]
        return wizard

    def test_multi_groups_render_with_source_path_and_fk(self, tmp_path):
        wizard = self._build_wizard_with_nested(tmp_path)
        captured: list[str] = []

        def _capture(msg="", *a, **kw):  # match click.echo signature
            captured.append(str(msg))

        with patch("click.echo", side_effect=_capture):
            wizard._display_inferred_schemas_summary()

        text = "\n".join(captured)
        assert "(MULTI)" in text
        assert "Group: PickLoadCarriers" in text
        assert "source_path: root" in text
        assert "Group: PickOrderLines" in text
        assert "source_path: PickOrderLines" in text
        # Primary keys annotated.
        assert "primary key" in text
        # Foreign key annotation references the parent table + col.
        assert "foreign key → PickLoadCarriers.Identity" in text

    def test_flat_json_renders_as_single(self, tmp_path):
        engine = SchemaInferenceEngine()
        info = _write(tmp_path, [{"id": "a", "v": 1}], name="flat")
        with patch("click.confirm") as confirm:
            engine._infer_schema_with_config(info)
            confirm.assert_not_called()
        info.total_columns = len(info.inferred_schemas["default"])

        wizard = QuickstartWizard(skip_confirmation=True)
        wizard.current_dir = tmp_path
        wizard.detected_files = [info]

        captured: list[str] = []
        with patch(
            "click.echo", side_effect=lambda msg="", *a, **kw: captured.append(str(msg))
        ):
            wizard._display_inferred_schemas_summary()

        text = "\n".join(captured)
        assert "(SINGLE)" in text
        assert "Group:" not in text
        assert "source_path" not in text


# --------------------------------------------------------------------- #
# Unwrap helper
# --------------------------------------------------------------------- #


class TestUnwrap:
    def test_top_level_list(self):
        records, wrapper = SchemaInferenceEngine._unwrap_json_records([{"a": 1}])
        assert records == [{"a": 1}]
        assert wrapper is None

    def test_single_key_dict_with_list(self):
        records, wrapper = SchemaInferenceEngine._unwrap_json_records(
            {"Items": [{"a": 1}]}
        )
        assert records == [{"a": 1}]
        assert wrapper == "Items"

    def test_multi_key_dict_is_not_unwrapped(self):
        records, wrapper = SchemaInferenceEngine._unwrap_json_records(
            {"Items": [{"a": 1}], "Other": [{"b": 2}]}
        )
        assert records is None
        assert wrapper is None


# Suppress unused-symbol warnings for the doc-only imports above.
_ = (Column, ColumnGroup, DataType, FileExtension, Schema, SchemaType)
