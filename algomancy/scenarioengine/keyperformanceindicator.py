from dataclasses import dataclass
from typing import Callable, Dict, List

from algomancy.scenarioengine.enumtypes import KpiType, ImprovementDirection, UnitOfMeasurement
from algomancy.scenarioengine.result import ScenarioResult

KPICalculationFunction = Callable[[ScenarioResult], float]

# todo KpiType: at least value / at most value

@dataclass
class KpiTemplate:
    name: str
    type: KpiType
    better_when: ImprovementDirection
    callback: KPICalculationFunction
    UOM: UnitOfMeasurement | None = None

    def __post_init__(self):
        if self.name == "":
            raise TypeError("KPI name cannot be empty.")
        if self.type not in KpiType:
            raise TypeError("Invalid KPI type.")
        if self.better_when not in ImprovementDirection:
            raise TypeError("Invalid KPI direction.")
        if self.UOM and self.UOM not in UnitOfMeasurement:
            raise TypeError("Invalid KPI UOM.")
        if not callable(self.callback):
            raise TypeError("Callback function is not callable.")


class KPI:
    def __init__(
            self,
            name: str,
            type: KpiType,
            better_when: ImprovementDirection,
            callback: KPICalculationFunction,
            UOM: UnitOfMeasurement = None,
            value: float = None,
    ) -> None:
        self._name = name
        self._type = type
        self._better_when = better_when
        self._callback = callback
        self._UOM = UOM
        self._value = value

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> KpiType:
        return self._type

    @property
    def better_when(self) -> ImprovementDirection:
        return self._better_when

    @property
    def UOM(self) -> UnitOfMeasurement | None:
        return self._UOM

    @property
    def value(self) -> float | None:
        return self._value

    def __str__(self):
        if self.value:
            return f"{self.name}: {self.value}" + (str(self.UOM) if self.UOM else "")
        else:
            return f"{self.name}: -"

    def compute(self, result: ScenarioResult) -> None:
        """
        Computes a key performance indicator (KPI) value using the provided result data
        and a callback function.

        This method attempts to compute the KPI by invoking a specified callback with
        the result data. If an exception occurs during computation, it logs an error
        message indicating the KPI name and raises a ValueError to indicate failure.

        :param result: The result data of the type ScenarioResultData required for KPI
                       computation.
        :type result: ScenarioResult
        :raises ValueError: If an error occurs during the KPI computation.
        """
        try:
            value = self._callback(result)
            if not isinstance(value, (int, float)):
                raise TypeError("KPI callback must return a numeric value.")
            self._value = value
        except TypeError as e:
            raise TypeError("KPI callback must return a numeric value.")
        except Exception as e:
            print(f"Error computing KPI {self.name}: {e}")
            raise ValueError(f"Error computing KPI {self.name}")

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type.name,
            "better_when": self.better_when.name,
            "callback": self._callback.__name__,
            "UOM": self.UOM.name if self.UOM else None,
            "value": self.value
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
            type=template.type,
            better_when=template.better_when,
            callback=template.callback,
            UOM=template.UOM if template.UOM else None,
        )

    return kpi_dict


def build_kpis_from_file(kpis: Dict, kpi_templates: List[KpiTemplate]) -> Dict[str, KPI]:

    kpi_dict = {}
    try:
        for kpi in kpis.values():
            [template] = [t for t in kpi_templates if t.name == kpi["name"]]
            assert template, f"KPI template '{kpi['name']}' not found."
            assert template.type == KpiType[kpi["type"]], \
                f"Invalid KPI type for '{kpi['name']}'."
            assert template.better_when == ImprovementDirection[kpi["better_when"]], \
                f"Invalid KPI direction for '{kpi['name']}'."
            assert template.UOM == UnitOfMeasurement[kpi["UOM"]] if kpi["UOM"] else True, \
                f"Invalid KPI UOM for '{kpi['name']}'."

            kpi_dict[template.name] = KPI(
                name=template.name,
                type=template.type,
                better_when=template.better_when,
                callback=template.callback,
                UOM=template.UOM if template.UOM else None,
                value=kpi["value"],
            )
    except KeyError:
        raise ValueError("Invalid KPI name in serialized KPIs.")
    except AssertionError:
        raise ValueError("Invalid KPI definition in serialized KPIs.")

    return kpi_dict
