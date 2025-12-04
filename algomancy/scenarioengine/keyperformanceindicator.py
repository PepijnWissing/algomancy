from dataclasses import dataclass
from typing import Callable, Dict, List

from algomancy.scenarioengine.enumtypes import ImprovementDirection
from algomancy.scenarioengine.result import BASE_RESULT_BOUND
from algomancy.scenarioengine.unit import BaseMeasurement, Measurement

KPICalculationFunction = Callable[[BASE_RESULT_BOUND], float]

# todo KpiType: at least value / at most value


@dataclass
class KpiTemplate:
    name: str
    better_when: ImprovementDirection
    callback: KPICalculationFunction
    measurement_base: BaseMeasurement

    def __post_init__(self):
        if self.name == "":
            raise TypeError("KPI name cannot be empty.")
        if self.better_when not in ImprovementDirection:
            raise TypeError("Invalid KPI direction.")
        if not callable(self.callback):
            raise TypeError("Callback function is not callable.")


class KPI:
    def __init__(
        self,
        name: str,
        better_when: ImprovementDirection,
        callback: KPICalculationFunction,
        bm: BaseMeasurement,
    ) -> None:
        self._name = name
        # self._type = type
        self._better_when = better_when
        self._callback = callback
        self._measurement = Measurement(bm)

    @property
    def measurement(self) -> Measurement:
        return self._measurement

    @property
    def name(self) -> str:
        return self._name

    @property
    def better_when(self) -> ImprovementDirection:
        return self._better_when

    @property
    def value(self) -> float | None:
        return self._measurement.value

    @value.setter
    def value(self, value: float):
        self._measurement.value = value

    def __str__(self):
        self._measurement.pretty()

    def compute(self, result: BASE_RESULT_BOUND) -> None:
        """
        Computes a key performance indicator (KPI) value using the provided result data
        and a callback function.

        This method attempts to compute the KPI by invoking a specified callback with
        the result data. If an exception occurs during computation, it logs an error
        message indicating the KPI name and raises a ValueError to indicate failure.

        :param result: The result data of the type required for KPI computation.
        :type result: Derived from BaseScenarioResult
        :raises ValueError: If an error occurs during the KPI computation.
        """
        try:
            value = self._callback(result)
            if not isinstance(value, (int, float)):
                raise TypeError("KPI callback must return a numeric value.")
            self.value = value
        except TypeError:
            raise TypeError("KPI callback must return a numeric value.")
        except Exception as e:
            print(f"Error computing KPI {self.name}: {e}")
            raise ValueError(f"Error computing KPI {self.name}")

    def to_dict(self):
        return {
            "name": self.name,
            "better_when": self.better_when.name,
            "callback": self._callback.__name__,
            "basis": self._measurement.base_measurement,
            "value": self.value,
        }


def build_kpis(kpi_templates: List[KpiTemplate]) -> Dict[str, KPI]:
    """
    Creates a dictionary of KPIs using the provided list of KPI templates.

    The function takes a list of KPI templates and creates a dictionary where
    each template's name serves as the key. If duplicate names are found
    across the templates, a ValueError is raised. For each unique template,
    a corresponding KPI object is created and added to the dictionary.

    :param kpi_templates: List of KPI templates to generate the KPI dictionary
        from.
    :type kpi_templates: List[KpiTemplate]
    :raises ValueError: If duplicate KPI names are found in the provided
        templates.
    :return: A dictionary where the keys are KPI names and the
        values are corresponding KPI objects.
    :rtype: Dict[str, KPI]
    """
    kpi_dict = {}

    for template in kpi_templates:
        if template.name in kpi_dict:
            raise ValueError(f"Duplicate KPI name '{template.name}' found.")

        kpi_dict[template.name] = KPI(
            name=template.name,
            better_when=template.better_when,
            callback=template.callback,
            bm=template.measurement_base,
        )

    return kpi_dict
