from typing import Generic, Dict, Type, List

from .keyperformanceindicator import BASE_KPI


class KpiFactory(Generic[BASE_KPI]):
    """
    Factory class for creating KPI instances.

    This class provides a mechanism to register multiple KPI templates and create
    instances of those templates dynamically. It enables flexibility and reuse
    of KPI-related components in a structured and modular way.

    Attributes:
        _templates (Dict[str, Type[BASE_KPI]]): Dictionary mapping template names
            to their corresponding KPI classes.
    """

    def __init__(self, templates: Dict[str, Type[BASE_KPI]]):
        self._templates = templates

    def create_all(self):
        """
        Creates a dictionary of KPIs using predefined templates.

        Returns:
            dict: A dictionary where the keys are the original keys from the
            `templates` dictionary, and the values are the results of calling
            the template functions.
        """
        return {name: template() for name, template in self._templates.items()}

    def create(self, subset: List[str]):
        """
        Creates a dictionary of template instances filtered by the specified subset.

        Args:
            subset (List[str]): A list of template names to include in the resulting
                dictionary.

        Returns:
            dict: A dictionary where the keys are the names of the templates from the
                subset and the values are their corresponding instantiated templates.
        """
        return {
            name: template()
            for name, template in self._templates.items()
            if name in subset
        }
