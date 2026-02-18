"""Tests for the DataSource derive functionality."""

import pandas as pd
import pytest
from algomancy_data.datasource import DataSource, DataClassification


class TestDataSourceDerive:
    """Test suite for DataSource.derive() method."""

    @pytest.fixture
    def sample_datasource(self):
        """Create a sample DataSource with test data."""
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="Original Data")

        # Add a sample table with various data types
        df = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "name": ["Alice", "Bob", "Charlie"],
                "value": [10.5, 20.3, 30.7],
                "timestamp": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            }
        )
        ds.add_table("test_table", df)

        return ds

    def test_derive_creates_new_instance(self, sample_datasource):
        """Test that derive creates a new instance, not the same object."""
        derived = sample_datasource.derive("Derived Data")

        assert derived is not sample_datasource
        assert type(derived) is type(sample_datasource)

    def test_derive_has_distinct_name(self, sample_datasource):
        """Test that derived DataSource has a different name."""
        new_name = "Derived Data"
        derived = sample_datasource.derive(new_name)

        assert derived.name == new_name
        assert derived.name != sample_datasource.name

    def test_derive_has_different_id(self, sample_datasource):
        """Test that derived DataSource has a different ID."""
        derived = sample_datasource.derive("Derived Data")

        assert derived.id != sample_datasource.id

    def test_derived_has_appropriate_classification(self, sample_datasource):
        """Test that derived DataSource has appropriate classification."""
        derived = sample_datasource.derive("Derived Data")

        assert derived._ds_type == DataClassification.DERIVED_DATA

    def test_derive_data_identical_in_value(self, sample_datasource):
        """Test that derived DataSource contains identical data values."""
        derived = sample_datasource.derive("Derived Data")

        # Check table names are the same
        assert derived.list_tables() == sample_datasource.list_tables()

        # Check each table has identical values
        for table_name in sample_datasource.list_tables():
            original_df = sample_datasource.get_table(table_name)
            derived_df = derived.get_table(table_name)

            # Check DataFrames are equal in value
            pd.testing.assert_frame_equal(original_df, derived_df, check_dtype=False)

    def test_derive_data_not_same_reference(self, sample_datasource):
        """Test that derived DataSource data is not the same reference (deep copy)."""
        derived = sample_datasource.derive("Derived Data")

        for table_name in sample_datasource.list_tables():
            original_df = sample_datasource.get_table(table_name)
            derived_df = derived.get_table(table_name)

            # Check that DataFrames are not the same object
            assert original_df is not derived_df

            # Modify derived DataFrame and ensure original is unchanged
            derived_df.loc[0, "value"] = 999.9

            # Original should remain unchanged
            assert original_df.loc[0, "value"] != 999.9

    def test_derive_preserves_data_types(self, sample_datasource):
        """Test that derived DataSource preserves column data types."""
        derived = sample_datasource.derive("Derived Data")

        for table_name in sample_datasource.list_tables():
            original_df = sample_datasource.get_table(table_name)
            derived_df = derived.get_table(table_name)

            # Check dtypes are preserved
            assert original_df.dtypes.to_dict() == derived_df.dtypes.to_dict()

    def test_derive_with_multiple_tables(self):
        """Test deriving a DataSource with multiple tables."""
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="Multi-table Data")

        # Add multiple tables
        df1 = pd.DataFrame({"col1": [1, 2, 3]})
        df2 = pd.DataFrame({"col2": ["a", "b", "c"]})
        df3 = pd.DataFrame({"col3": [1.1, 2.2, 3.3]})

        ds.add_table("table1", df1)
        ds.add_table("table2", df2)
        ds.add_table("table3", df3)

        # Derive
        derived = ds.derive("Derived Multi-table")

        # Check all tables are present
        assert set(derived.list_tables()) == {"table1", "table2", "table3"}

        # Check all tables are value-identical but reference-distinct
        for table_name in ds.list_tables():
            original_df = ds.get_table(table_name)
            derived_df = derived.get_table(table_name)

            pd.testing.assert_frame_equal(original_df, derived_df, check_dtype=False)
            assert original_df is not derived_df

    def test_derive_with_empty_datasource(self):
        """Test deriving an empty DataSource (no tables)."""
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="Empty Data")

        derived = ds.derive("Derived Empty")

        assert derived.list_tables() == []
        assert derived.name == "Derived Empty"
        assert derived.id != ds.id

    def test_derive_preserves_complex_data(self):
        """Test that derive preserves complex data structures correctly."""
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="Complex Data")

        # Create DataFrame with None values and various edge cases
        df = pd.DataFrame(
            {
                "int_col": [1, 2, None],
                "float_col": [1.5, None, 3.5],
                "str_col": ["a", None, "c"],
                "datetime_col": pd.to_datetime(["2024-01-01", None, "2024-01-03"]),
            }
        )
        ds.add_table("complex_table", df)

        derived = ds.derive("Derived Complex")

        # Compare DataFrames (handling NaN/None carefully)
        original_df = ds.get_table("complex_table")
        derived_df = derived.get_table("complex_table")

        pd.testing.assert_frame_equal(original_df, derived_df, check_dtype=False)
        assert original_df is not derived_df

    def test_derive_chain(self, sample_datasource):
        """Test that we can derive from a derived DataSource."""
        first_derived = sample_datasource.derive("First Derived")
        second_derived = first_derived.derive("Second Derived")

        # All three should have different IDs
        assert len({sample_datasource.id, first_derived.id, second_derived.id}) == 3

        # All should have different names
        assert sample_datasource.name == "Original Data"
        assert first_derived.name == "First Derived"
        assert second_derived.name == "Second Derived"

        # Data should still be identical in value
        for table_name in sample_datasource.list_tables():
            original_df = sample_datasource.get_table(table_name)
            second_derived_df = second_derived.get_table(table_name)
            pd.testing.assert_frame_equal(
                original_df, second_derived_df, check_dtype=False
            )

    def test_derive_independence(self, sample_datasource):
        """Test that modifications to tables dict don't affect the original."""
        derived = sample_datasource.derive("Derived Data")

        # Add a new table to derived
        new_df = pd.DataFrame({"new_col": [4, 5, 6]})
        derived.add_table("new_table", new_df)

        # Original should not have the new table
        assert "new_table" in derived.list_tables()
        assert "new_table" not in sample_datasource.list_tables()

    def test_post_derive_hook_is_called(self, sample_datasource):
        """Test that _post_derive() hook method is called during derivation."""

        # Create a custom DataSource subclass to track hook calls
        class TestDataSource(DataSource):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.post_derive_called = False

            def _post_derive(self):
                """Override the hook to track if it's called."""
                super()._post_derive()
                self.post_derive_called = True

        # Create an instance with the custom subclass
        ds = TestDataSource(ds_type=DataClassification.MASTER_DATA, name="Test Data")
        df = pd.DataFrame({"col": [1, 2, 3]})
        ds.add_table("test", df)

        # Derive and check that the hook was called
        derived = ds.derive("Derived Test")

        assert isinstance(derived, TestDataSource)
        assert derived.post_derive_called is True
        assert ds.post_derive_called is False  # Original should not have flag set
