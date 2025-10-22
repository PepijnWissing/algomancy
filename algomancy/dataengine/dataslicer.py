from typing import Dict

from algomancy.dataengine.datamanager import DataSource

"""
Takes the properties and returns the part of the master_data that matches
"""
def slice_data(
        master_data: DataSource,
        properties_in_slice: Dict,
        logger = None
) -> DataSource:
    if logger:
        logger._log(f"Slicing with properties: {properties_in_slice}")
    return master_data
