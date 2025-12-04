from typing import List, Tuple, Dict

"""
Measurement and unit scaling framework

This module provides a small, self-contained framework to represent quantities,
units, and measured values with smart, human-friendly formatting. It is used
throughout the project (notably in KPI templates) to present values using the
most appropriate unit and number of digits without writing formatting logic in
multiple places.

Core concepts
- Quantity: A domain of measurement (e.g., Length, Time, Data). A quantity owns
  a chain of related units and knows how they convert.
- Unit: A single unit with a symbol (e.g., m, s, B). Units are linked from
  smaller to larger and vice versa so values can scale up or down.
- BaseMeasurement: A formatting preference object: it stores the base unit for a
  value and how it should be displayed (min/max significant digits and decimal
  places, optional smallest/largest unit clamps).
- Measurement: A concrete value bound to a BaseMeasurement. It can be scaled to
  a better unit and formatted with the desired precision.

Why this exists
Displaying 15320.0 seconds as "4.26 h" or 12_345_678 B as "11.77 MiB" should be
trivial for users of the framework, and consistent across the app. This module
centralizes unit chains, conversions, and pretty-printing so KPIs and UI code
just construct a Measurement and call `pretty()`.

Quick start
1) Pick a quantity and base unit using the global `QUANTITIES` registry.
2) Create a `BaseMeasurement` describing how you want values formatted.
3) Create a `Measurement(base_measurement, value)` and call `pretty()`.

Example: length
```python
from scenario.unit import QUANTITIES, BaseMeasurement, Measurement

length = QUANTITIES["length"]
length_m = BaseMeasurement(length["m"], min_digits=1, max_digits=3, decimals=2)

for val in [0.000005, 0.025, 2.5, 250, 25_000, 2_500_000]:
    m = Measurement(length_m, val)
    print(m.pretty())  # auto-scales across nm, μm, mm, cm, m, km as appropriate
```

Example: time with tighter bounds
```python
time = QUANTITIES["time"]
# Clamp scaling between seconds and hours, show 1 decimal
prefs = BaseMeasurement(time["s"], min_digits=1, max_digits=2, decimals=1,
                        smallest_unit="s", largest_unit="h")
for val in [0.5, 45, 3_665, 86_400]:
    print(Measurement(prefs, val).pretty())
```

Example: money
```python
money = QUANTITIES["money"]
usd = BaseMeasurement(money["$"], min_digits=0, max_digits=3, decimals=2)
print(Measurement(usd, 1_234_567).pretty())   # $1.23M
```

Notes
- min_digits / max_digits bound the number of significant digits before a unit
  change is attempted. This keeps values compact while avoiding "0.00" noise.
- decimals controls the decimal places in the final formatted string.
- smallest_unit / largest_unit can be set to restrict automatic scaling range.
- See the runnable examples at the end of the file (the `__main__` section) for
  more sample outputs across quantities like mass, time, money, and data.
"""


# ============================================================================
# Scaling unit framework
# ============================================================================
class Unit:
    """A single unit in a quantity (e.g., m, s, B)

    A `Unit` knows its textual `name` and printable `symbol` and can be linked to
    an adjacent smaller or larger unit with known conversion factors. These
    links are used by `Measurement` to automatically scale values up or down to
    keep within the configured digit bounds.

    Notes
    - Links are set when units are added to a `Quantity` via
      `Quantity.add_unit(...)`. You generally don't set them manually.
    - `conversion_factor_to_larger` represents how many of the current unit make
      one of the larger unit. The reverse factor is stored on the larger unit to
      point back to the smaller.
    - `__str__` prints a human-readable description for debugging.
    """

    def __init__(self, name: str, symbol: str):
        self.name: str = name
        self.symbol: str = symbol
        self.smaller_unit: "Unit | None" = None
        self.conversion_factor_to_smaller: float | None = None
        self.larger_unit: "Unit | None" = None
        self.conversion_factor_to_larger: float | None = None

    def __str__(self):
        return f"Unit: {self.name}, ({self.symbol})"

    def _set_smaller_unit(self, smaller_unit: "Unit", conversion_factor: float):
        self.smaller_unit = smaller_unit
        self.conversion_factor_to_smaller = conversion_factor

    def set_larger_unit(self, larger_unit: "Unit", conversion_factor: float):
        self.larger_unit = larger_unit
        self.conversion_factor_to_larger = conversion_factor

        larger_unit._set_smaller_unit(self, 1 / conversion_factor)


class Quantity:
    """A domain of measurement that owns and links units

    A `Quantity` groups a set of related `Unit`s (e.g., meters, kilometers for
    length; seconds, hours for time) and stores their conversion relationships in
    increasing order. It provides convenient access by unit name via
    `quantity["m"]` and is responsible for wiring the chain of smaller/larger
    units so values can scale automatically.

    Typical usage
    - Obtain a quantity from the global `QUANTITIES` registry (e.g.,
      `length = QUANTITIES["length"]`).
    - Access a unit by name (e.g., `length["m"]`).
    - Define custom quantities and units if your domain requires them, then
      register them with `QuantityRegistry`.

    Notes
    - Units are sorted by their factor relative to the standard/base unit you
      provide when adding them.
    - When you add a new unit, bidirectional links between adjacent units are
      re-built automatically.
    """

    def __init__(self, name: str, standard_unit: Unit):
        self.name: str = name
        self.standard_unit: Unit = standard_unit
        self.sorted_units: List[Tuple[Unit, float]] = [(standard_unit, 1)]
        self.associated_units: Dict[str, Unit] = {standard_unit.name: standard_unit}

    def __getitem__(self, key) -> Unit | None:
        try:
            return self.associated_units[key]
        except KeyError:
            raise KeyError(
                f"Unit '{key}' not found in quantity '{self.name}'\n"
                f"  Available units are: {', '.join(self.associated_units.keys())}"
            )

    def add_unit(self, base_unit: Unit, factor_to_base: float):
        if base_unit.name in self.associated_units:
            raise ValueError(
                f"Unit '{base_unit.name}' already exists in quantity '{self.name}'"
            )
        self.associated_units[base_unit.name] = base_unit
        self.sorted_units.append((base_unit, factor_to_base))
        self._sort_associated_units()
        self._relink_units()

    def _sort_associated_units(self):
        self.sorted_units.sort(key=lambda x: x[1])

    def _relink_units(self):
        self._sort_associated_units()
        for i, (unit, factor) in enumerate(self.sorted_units):
            if i == len(self.sorted_units) - 1:
                break
            next_unit, next_factor = self.sorted_units[i + 1]
            unit.set_larger_unit(next_unit, factor / next_factor)


class BaseMeasurement:
    """Display and scaling preferences for measurements

    A `BaseMeasurement` binds a base `Unit` with formatting and scaling rules
    that `Measurement` instances will follow when pretty-printing values.

    Parameters
    - base_unit: The unit in which input values are expressed (e.g., seconds,
      meters, bytes). Auto-scaling starts from this unit.
    - min_digits: Minimum number of significant digits to keep before trying to
      scale down to a smaller unit. Helps avoid values like "0.00".
    - max_digits: Maximum number of significant digits to allow before trying to
      scale up to a larger unit. Keeps values compact (e.g., 2500 m -> 2.5 km).
    - decimals: Fixed number of decimal places to show in the final formatted
      value.
    - smallest_unit: Optional name of the smallest unit allowed during scaling.
    - largest_unit: Optional name of the largest unit allowed during scaling.

    Typical usage
    ```python
    length = QUANTITIES["length"]
    prefs = BaseMeasurement(length["m"], min_digits=1, max_digits=3, decimals=2)
    print(Measurement(prefs, 2500).pretty())  # 2.50 km
    ```

    Notes
    - This class contains no value; it is reused across many `Measurement`
      instances that share the same formatting rules.
    - If `smallest_unit`/`largest_unit` are provided, they must match unit names
      registered in the corresponding `Quantity`.
    """

    def __init__(
        self,
        base_unit: Unit,
        min_digits: int = 0,
        max_digits: int = 3,
        decimals: int = 2,
        smallest_unit: str | None = None,
        largest_unit: str | None = None,
    ):
        self.unit: Unit = base_unit
        self.min_digits: int = min_digits
        self.max_digits: int = max_digits
        self.decimals: int = decimals
        self.smallest_unit: str | None = smallest_unit
        self.largest_unit: str | None = largest_unit

    def __str__(self):
        return (
            f"{self.unit.name}, {self.unit.symbol} | {self.min_digits} to {self.max_digits} digits |"
            f" {self.decimals} decimals"
        )


class Measurement:
    """A value bound to display rules with auto-scaling and pretty output

    `Measurement` holds a numeric `value` together with a `BaseMeasurement`
    (formatting/scaling preferences) and the current `Unit`. It can:
    - auto-scale up/down across the unit chain using `scale()` and `pretty()`;
    - scale to match another measurement's unit via `scale_to_unit(other)`;
    - format its numeric value using the `decimals` preference.

    Attributes
    - base_measurement: The `BaseMeasurement` with rules for formatting/scaling.
    - value: The numeric value, expressed in `base_measurement.unit` unless
      scaled.
    - unit: The current `Unit` in which `value` is expressed. It starts as the
      base unit and changes when scaling.

    Special values
    - INITIAL_VALUE: Sentinel used as default constructor value. Ensure you
      assign a real value before presenting to users.

    Common operations
    ```python
    length = QUANTITIES["length"]
    prefs = BaseMeasurement(length["m"], min_digits=1, max_digits=3, decimals=2)
    m = Measurement(prefs, 2500)
    print(m.pretty())           # 2.50 km (auto-scales)

    other = Measurement(prefs, 1)    # 1 m
    m.scale_to_unit(other)           # force same unit as `other` (meters)
    print(m.pretty())           # 2500.00 m
    ```
    """

    INITIAL_VALUE = -9999999999

    def __init__(self, base_measurement: BaseMeasurement, value: float = INITIAL_VALUE):
        self.base_measurement: BaseMeasurement = base_measurement
        self.value: float = value
        self.unit: Unit = base_measurement.unit

    def __str__(self):
        return self.to_string()

    def to_string(self) -> str:
        return f"{self._format_value()} {self.unit.symbol}"

    def pretty(self) -> str:
        return f"{str(self.scale())}"
        if self.value == Measurement.INITIAL_VALUE:
            return "N/A"
        scaled = self.scale()
        formatted = scaled.to_string()
        return formatted

    def _format_value(self) -> str:
        """Format the value according to the specified decimal places"""
        return f"{self.value:.{self.base_measurement.decimals}f}"

    def scale(self) -> "Measurement":
        """Scale the measurement to fit within the desired digit range"""
        # If no value was set, do nothing
        if self.value == Measurement.INITIAL_VALUE:
            return self

        # Handle edge case of zero
        if self.value == 0:
            return Measurement(self.base_measurement, 0)

        # determine the number of digits (ignoring sign and decimal)
        n_digits = self._get_digits()

        # if the number of digits is within the range, return formatted measurement
        if (
            self.base_measurement.min_digits
            <= n_digits
            <= self.base_measurement.max_digits
        ):
            formatted_value = float(self._format_value())
            return Measurement(self.base_measurement, formatted_value)

        # Too many digits - scale up to larger unit
        elif n_digits > self.base_measurement.max_digits:
            return self._scale_up()

        # Too few digits - scale down to smaller unit
        else:
            return self._scale_down()

    def _get_digits(self, value=None, progress=1) -> int:
        """
        Determine the number of digits (ignoring sign and decimal) of the value.

        examples:
            value = 1000 => n_digits= 4
            value = 0.001 => n_digits= -2

        Returns:
            integer value of the number of digits
        """
        if value is None:
            value = abs(self.value)

        if 1 <= value < 10:
            return progress
        elif 10 <= value:
            return self._get_digits(value / 10, progress + 1)
        elif value < 1:
            return self._get_digits(value * 10, progress - 1)
        else:
            raise ValueError("Invalid value")

    def scale_to_unit(self, other_unit: Unit) -> "Measurement":
        """
        Scale this measurement to use the same unit as another measurement.

        Args:
            other_unit: The unit to match

        Returns:
            A new Measurement with the same unit as other

        Raises:
            ValueError: If the measurements are incompatible (different quantity types)
        """
        # If already the same unit, just return a copy with formatted value
        if self.unit.name == other_unit.name:
            formatted_value = float(self._format_value())
            return Measurement(
                BaseMeasurement(
                    self.unit,
                    min_digits=self.base_measurement.min_digits,
                    max_digits=self.base_measurement.max_digits,
                    decimals=self.base_measurement.decimals,
                    smallest_unit=self.base_measurement.smallest_unit,
                    largest_unit=self.base_measurement.largest_unit,
                ),
                formatted_value,
            )

        # Find conversion path from self to other's unit
        conversion_factor = self._find_conversion_factor(other_unit)

        if conversion_factor is None:
            raise ValueError(
                f"Cannot convert from {self.unit.name} to {other_unit.name}: "
                f"units are not in the same quantity system"
            )

        # Convert value to target unit
        new_value = self.value * conversion_factor

        # Create new measurement with other's unit
        new_base_measurement = BaseMeasurement(
            base_unit=other_unit,
            min_digits=self.base_measurement.min_digits,
            max_digits=self.base_measurement.max_digits,
            decimals=self.base_measurement.decimals,
            smallest_unit=self.base_measurement.smallest_unit,
            largest_unit=self.base_measurement.largest_unit,
        )

        return Measurement(new_base_measurement, new_value)

    def _find_conversion_factor(self, target_unit: Unit) -> float | None:
        """
        Find the conversion factor from this unit to the target unit.
        Uses bidirectional search through the unit chain.

        Args:
            target_unit: The unit to convert to

        Returns:
            Conversion factor if found, None otherwise
        """
        # BFS to find path from self.unit to target_unit
        visited = set()
        queue = [(self.unit, 1.0)]  # (unit, cumulative_factor)

        while queue:
            current_unit, current_factor = queue.pop(0)

            if current_unit.name in visited:
                continue
            visited.add(current_unit.name)

            # Found the target
            if current_unit.name == target_unit.name:
                return current_factor

            # Explore larger unit
            if current_unit.larger_unit is not None:
                new_factor = current_factor * current_unit.conversion_factor_to_larger
                queue.append((current_unit.larger_unit, new_factor))

            # Explore smaller unit
            if current_unit.smaller_unit is not None:
                new_factor = current_factor * current_unit.conversion_factor_to_smaller
                queue.append((current_unit.smaller_unit, new_factor))

        return None

    def _scale_up(self) -> "Measurement":
        """Scale up to a larger unit"""
        # Check if we can scale up
        if self.unit.larger_unit is None:
            # Already at largest unit, return as is
            formatted_value = float(self._format_value())
            return Measurement(self.base_measurement, formatted_value)

        # Check if largest_unit constraint prevents scaling
        if (
            self.base_measurement.largest_unit is not None
            and self.unit.name == self.base_measurement.largest_unit
        ):
            formatted_value = float(self._format_value())
            return Measurement(self.base_measurement, formatted_value)

        # Scale to larger unit
        new_value = self.value * self.unit.conversion_factor_to_larger
        new_base_measurement = BaseMeasurement(
            base_unit=self.unit.larger_unit,
            min_digits=self.base_measurement.min_digits,
            max_digits=self.base_measurement.max_digits,
            decimals=self.base_measurement.decimals,
            smallest_unit=self.base_measurement.smallest_unit,
            largest_unit=self.base_measurement.largest_unit,
        )
        new_measurement = Measurement(new_base_measurement, new_value)

        # Recursively scale if still too many digits
        return new_measurement.scale()

    def _scale_down(self) -> "Measurement":
        """Scale down to a smaller unit"""
        # Check if we can scale down
        if self.unit.smaller_unit is None:
            # Already at smallest unit, return as is
            formatted_value = float(self._format_value())
            return Measurement(self.base_measurement, formatted_value)

        # Check if smallest_unit constraint prevents scaling
        if (
            self.base_measurement.smallest_unit is not None
            and self.unit.name == self.base_measurement.smallest_unit
        ):
            formatted_value = float(self._format_value())
            return Measurement(self.base_measurement, formatted_value)

        # Scale to smaller unit
        new_value = self.value * self.unit.conversion_factor_to_smaller
        new_base_measurement = BaseMeasurement(
            base_unit=self.unit.smaller_unit,
            min_digits=self.base_measurement.min_digits,
            max_digits=self.base_measurement.max_digits,
            decimals=self.base_measurement.decimals,
            smallest_unit=self.base_measurement.smallest_unit,
            largest_unit=self.base_measurement.largest_unit,
        )
        new_measurement = Measurement(new_base_measurement, new_value)

        # Recursively scale if still too few digits
        return new_measurement.scale()


# ============================================================================
# Pre-defined Quantities with Extensive Unit Options
# ============================================================================


def create_length_quantity() -> Quantity:
    """Create a length quantity with metric units"""
    length = Quantity("Length", Unit("m", "m"))
    # Smaller units
    length.add_unit(Unit("mm", "mm"), 0.001)
    length.add_unit(Unit("cm", "cm"), 0.01)
    length.add_unit(Unit("dm", "dm"), 0.1)
    # Larger units
    length.add_unit(Unit("km", "km"), 1_000)
    # Micro and nano
    length.add_unit(Unit("μm", "μm"), 0.000_001)
    length.add_unit(Unit("nm", "nm"), 0.000_000_001)
    # Mega
    length.add_unit(Unit("Mm", "Mm"), 1_000_000)
    return length


def create_mass_quantity() -> Quantity:
    """Create a mass quantity with metric units"""
    mass = Quantity("Mass", Unit("g", "g"))
    # Smaller units
    mass.add_unit(Unit("mg", "mg"), 0.001)
    mass.add_unit(Unit("μg", "μg"), 0.000_001)
    # Larger units
    mass.add_unit(Unit("kg", "kg"), 1_000)
    mass.add_unit(Unit("t", "t"), 1_000_000)  # metric ton
    mass.add_unit(Unit("kt", "kt"), 1_000_000_000)  # kiloton
    mass.add_unit(Unit("Mt", "Mt"), 1_000_000_000_000)  # megaton
    return mass


def create_time_quantity() -> Quantity:
    """Create a time quantity with various units"""
    time = Quantity("Time", Unit("s", "s"))
    # Smaller units
    time.add_unit(Unit("ms", "ms"), 0.001)
    time.add_unit(Unit("μs", "μs"), 0.000_001)
    time.add_unit(Unit("ns", "ns"), 0.000_000_001)
    # Larger units
    time.add_unit(Unit("min", "min"), 60)
    time.add_unit(Unit("h", "h"), 3_600)
    time.add_unit(Unit("d", "d"), 86_400)
    time.add_unit(Unit("wk", "wk"), 604_800)
    time.add_unit(Unit("yr", "yr"), 31_536_000)
    return time


def create_area_quantity() -> Quantity:
    """Create an area quantity with metric units"""
    area = Quantity("Area", Unit("m²", "m²"))
    # Smaller units
    area.add_unit(Unit("mm²", "mm²"), 0.000_001)
    area.add_unit(Unit("cm²", "cm²"), 0.0001)
    area.add_unit(Unit("dm²", "dm²"), 0.01)
    # Larger units
    area.add_unit(Unit("km²", "km²"), 1_000_000)
    area.add_unit(Unit("ha", "ha"), 10_000)  # hectare
    return area


def create_volume_quantity() -> Quantity:
    """Create a volume quantity with metric units"""
    volume = Quantity("Volume", Unit("L", "L"))
    # Smaller units
    volume.add_unit(Unit("mL", "mL"), 0.001)
    volume.add_unit(Unit("cL", "cL"), 0.01)
    volume.add_unit(Unit("dL", "dL"), 0.1)
    # Larger units
    volume.add_unit(Unit("m³", "m³"), 1_000)
    volume.add_unit(Unit("kL", "kL"), 1_000)
    # Very small
    volume.add_unit(Unit("μL", "μL"), 0.000_001)
    return volume


def create_speed_quantity() -> Quantity:
    """Create a speed quantity"""
    speed = Quantity("Speed", Unit("m/s", "m/s"))
    speed.add_unit(Unit("km/h", "km/h"), 0.277778)
    speed.add_unit(Unit("cm/s", "cm/s"), 0.01)
    speed.add_unit(Unit("mm/s", "mm/s"), 0.001)
    return speed


def create_temperature_quantity() -> Quantity:
    """Create a temperature quantity (Celsius scale)"""
    temp = Quantity("Temperature", Unit("°C", "°C"))
    # Note: These are NOT convertible via simple multiplication
    # This is a simplified example - real temperature conversion needs offset
    temp.add_unit(Unit("K", "K"), 1)  # Kelvin (simplified)
    return temp


def create_energy_quantity() -> Quantity:
    """Create an energy quantity"""
    energy = Quantity("Energy", Unit("J", "J"))
    # Smaller units
    energy.add_unit(Unit("mJ", "mJ"), 0.001)
    energy.add_unit(Unit("μJ", "μJ"), 0.000_001)
    # Larger units
    energy.add_unit(Unit("kJ", "kJ"), 1_000)
    energy.add_unit(Unit("MJ", "MJ"), 1_000_000)
    energy.add_unit(Unit("GJ", "GJ"), 1_000_000_000)
    energy.add_unit(Unit("kWh", "kWh"), 3_600_000)
    energy.add_unit(Unit("MWh", "MWh"), 3_600_000_000)
    return energy


def create_power_quantity() -> Quantity:
    """Create a power quantity"""
    power = Quantity("Power", Unit("W", "W"))
    # Smaller units
    power.add_unit(Unit("mW", "mW"), 0.001)
    power.add_unit(Unit("μW", "μW"), 0.000_001)
    # Larger units
    power.add_unit(Unit("kW", "kW"), 1_000)
    power.add_unit(Unit("MW", "MW"), 1_000_000)
    power.add_unit(Unit("GW", "GW"), 1_000_000_000)
    return power


def create_pressure_quantity() -> Quantity:
    """Create a pressure quantity"""
    pressure = Quantity("Pressure", Unit("Pa", "Pa"))
    # Smaller/Larger units
    pressure.add_unit(Unit("kPa", "kPa"), 1_000)
    pressure.add_unit(Unit("MPa", "MPa"), 1_000_000)
    pressure.add_unit(Unit("bar", "bar"), 100_000)
    pressure.add_unit(Unit("mbar", "mbar"), 100)
    return pressure


def create_frequency_quantity() -> Quantity:
    """Create a frequency quantity"""
    frequency = Quantity("Frequency", Unit("Hz", "Hz"))
    frequency.add_unit(Unit("kHz", "kHz"), 1_000)
    frequency.add_unit(Unit("MHz", "MHz"), 1_000_000)
    frequency.add_unit(Unit("GHz", "GHz"), 1_000_000_000)
    frequency.add_unit(Unit("mHz", "mHz"), 0.001)
    return frequency


def create_data_quantity() -> Quantity:
    """Create a data storage quantity (binary)"""
    data = Quantity("Data", Unit("B", "B"))
    # Binary prefixes (IEC standard)
    data.add_unit(Unit("KiB", "KiB"), 1_024)
    data.add_unit(Unit("MiB", "MiB"), 1_048_576)
    data.add_unit(Unit("GiB", "GiB"), 1_073_741_824)
    data.add_unit(Unit("TiB", "TiB"), 1_099_511_627_776)
    data.add_unit(Unit("PiB", "PiB"), 1_125_899_906_842_624)
    return data


def create_data_decimal_quantity() -> Quantity:
    """Create a data storage quantity (decimal)"""
    data = Quantity("Data (Decimal)", Unit("B", "B"))
    # Decimal prefixes (SI standard)
    data.add_unit(Unit("KB", "KB"), 1_000)
    data.add_unit(Unit("MB", "MB"), 1_000_000)
    data.add_unit(Unit("GB", "GB"), 1_000_000_000)
    data.add_unit(Unit("TB", "TB"), 1_000_000_000_000)
    data.add_unit(Unit("PB", "PB"), 1_000_000_000_000_000)
    return data


def create_money_quantity() -> Quantity:
    """Create a money quantity with scaling prefixes"""
    money = Quantity("Money", Unit("$", "$"))
    money.add_unit(Unit("k$", "k$"), 1_000)
    money.add_unit(Unit("M$", "M$"), 1_000_000)
    money.add_unit(Unit("B$", "B$"), 1_000_000_000)
    money.add_unit(Unit("T$", "T$"), 1_000_000_000_000)
    # Cents
    money.add_unit(Unit("¢", "¢"), 0.01)
    return money


def create_currency_quantity(symbol: str, name: str) -> Quantity:
    """Create a generic currency quantity"""
    currency = Quantity(name, Unit(symbol, symbol))
    currency.add_unit(Unit(f"k{symbol}", f"k{symbol}"), 1_000)
    currency.add_unit(Unit(f"M{symbol}", f"M{symbol}"), 1_000_000)
    currency.add_unit(Unit(f"B{symbol}", f"B{symbol}"), 1_000_000_000)
    return currency


def create_percentage_quantity() -> Quantity:
    """Create a percentage quantity"""
    percentage = Quantity("Percentage", Unit("%", "%"))
    percentage.add_unit(Unit("‰", "‰"), 0.1)  # per mille
    percentage.add_unit(Unit("bp", "bp"), 0.01)  # basis points
    return percentage


def create_count_quantity() -> Quantity:
    """Create a generic count quantity for items"""
    count = Quantity("Count", Unit("", ""))
    count.add_unit(Unit("k", "k"), 1_000)
    count.add_unit(Unit("M", "M"), 1_000_000)
    count.add_unit(Unit("B", "B"), 1_000_000_000)
    return count


def create_electric_current_quantity() -> Quantity:
    """Create an electric current quantity"""
    current = Quantity("Electric Current", Unit("A", "A"))
    current.add_unit(Unit("mA", "mA"), 0.001)
    current.add_unit(Unit("μA", "μA"), 0.000_001)
    current.add_unit(Unit("kA", "kA"), 1_000)
    return current


def create_voltage_quantity() -> Quantity:
    """Create a voltage quantity"""
    voltage = Quantity("Voltage", Unit("V", "V"))
    voltage.add_unit(Unit("mV", "mV"), 0.001)
    voltage.add_unit(Unit("μV", "μV"), 0.000_001)
    voltage.add_unit(Unit("kV", "kV"), 1_000)
    voltage.add_unit(Unit("MV", "MV"), 1_000_000)
    return voltage


def create_resistance_quantity() -> Quantity:
    """Create an electrical resistance quantity"""
    resistance = Quantity("Resistance", Unit("Ω", "Ω"))
    resistance.add_unit(Unit("mΩ", "mΩ"), 0.001)
    resistance.add_unit(Unit("kΩ", "kΩ"), 1_000)
    resistance.add_unit(Unit("MΩ", "MΩ"), 1_000_000)
    return resistance


def create_default_quantity() -> Quantity:
    """Create a default quantity with a single unit"""
    default = Quantity("Default", Unit("unit", ""))
    # default.add_unit(BaseUnit("default", ""), 1)
    return default


# ============================================================================
# Standard Quantities Registry
# ============================================================================


class QuantityRegistry:
    """Registry for commonly used quantities

    Provides convenient access to pre-defined `Quantity` objects and a simple
    way to register custom ones. Use the global instance `QUANTITIES` to look up
    quantities by name, e.g., `QUANTITIES["length"]`.

    Built-in quantities (keys)
    - length, mass, time, area, volume, speed, temperature, energy, power,
      pressure, frequency, data (binary multiples), data_decimal (decimal SI),
      money, percentage, count, current, voltage, resistance, default

    Customization
    - Create a `Quantity`, add units with `add_unit(...)`, then register it via
      `register(name, quantity)`. Afterwards it can be retrieved with the same
      index syntax: `QUANTITIES[name]`.

    Error handling
    - `__getitem__` raises a descriptive `KeyError` listing available quantities
      when a name is unknown.
    """

    def __init__(self):
        self._quantities: Dict[str, Quantity] = {}
        self._initialize_standard_quantities()

    def _initialize_standard_quantities(self):
        """Initialize all standard quantities"""
        self._quantities["length"] = create_length_quantity()
        self._quantities["mass"] = create_mass_quantity()
        self._quantities["time"] = create_time_quantity()
        self._quantities["area"] = create_area_quantity()
        self._quantities["volume"] = create_volume_quantity()
        self._quantities["speed"] = create_speed_quantity()
        self._quantities["temperature"] = create_temperature_quantity()
        self._quantities["energy"] = create_energy_quantity()
        self._quantities["power"] = create_power_quantity()
        self._quantities["pressure"] = create_pressure_quantity()
        self._quantities["frequency"] = create_frequency_quantity()
        self._quantities["data"] = create_data_quantity()
        self._quantities["data_decimal"] = create_data_decimal_quantity()
        self._quantities["money"] = create_money_quantity()
        self._quantities["percentage"] = create_percentage_quantity()
        self._quantities["count"] = create_count_quantity()
        self._quantities["current"] = create_electric_current_quantity()
        self._quantities["voltage"] = create_voltage_quantity()
        self._quantities["resistance"] = create_resistance_quantity()
        self._quantities["default"] = create_default_quantity()

    def get(self, name: str) -> Quantity | None:
        """Get a quantity by name"""
        return self._quantities.get(name)

    def register(self, name: str, quantity: Quantity):
        """Register a custom quantity"""
        if name in self._quantities:
            raise ValueError(f"Quantity '{name}' already registered")
        self._quantities[name] = quantity

    def list_quantities(self) -> List[str]:
        """List all registered quantity names"""
        return list(self._quantities.keys())

    def __getitem__(self, name: str) -> Quantity:
        """Get a quantity by name using [] operator"""
        quantity = self.get(name)
        if quantity is None:
            raise KeyError(
                f"Quantity '{name}' not found in registry.\n "
                f"  Available quantities: {self.list_quantities()}"
            )
        return quantity


# Global registry instance
QUANTITIES = QuantityRegistry()


def example_usage():
    """Example usage of the Measurement classes"""
    print("=== Available Quantities ===")
    for qty_name in QUANTITIES.list_quantities():
        print(f"  - {qty_name}")

    print("\n=== Length Examples ===")
    length = QUANTITIES["length"]
    length_m = BaseMeasurement(length["m"], min_digits=1, max_digits=3, decimals=2)

    examples = [0.000005, 0.025, 2.5, 250, 25_000, 2_500_000]
    for val in examples:
        m = Measurement(length_m, val)
        print(f"{val:>15} m -> {m.pretty()}")

    print("\n=== Mass Examples ===")
    mass = QUANTITIES["mass"]
    mass_g = BaseMeasurement(mass["g"], min_digits=1, max_digits=3, decimals=2)

    for val in [0.5, 50, 5_000, 500_000, 50_000_000]:
        m = Measurement(mass_g, val)
        print(f"{val:>15} g -> {m.pretty()}")

    print("\n=== Time Examples ===")
    time = QUANTITIES["time"]
    time_s = BaseMeasurement(time["s"], min_digits=1, max_digits=3, decimals=1)

    for val in [0.000_001, 0.5, 45, 3_665, 86_400, 31_536_000]:
        m = Measurement(time_s, val)
        print(f"{val:>15} s -> {m.pretty()}")

    print("\n=== Money Examples ===")
    money = QUANTITIES["money"]
    money_usd = BaseMeasurement(money["$"], min_digits=0, max_digits=3, decimals=2)

    for val in [0.50, 50, 1_234_567, 5_000_000_000, 1_500_000_000_000]:
        m = Measurement(money_usd, val)
        print(f"${val:>18,.2f} -> {m.pretty()}")

    print("\n=== Data Storage Examples (Binary) ===")
    data = QUANTITIES["data"]
    data_b = BaseMeasurement(data["B"], min_digits=1, max_digits=3, decimals=2)

    for val in [512, 5_120, 5_242_880, 5_368_709_120]:
        m = Measurement(data_b, val)
        print(f"{val:>15} B -> {m.pretty()}")

    print("\n=== Power Examples ===")
    power = QUANTITIES["power"]
    power_w = BaseMeasurement(power["W"], min_digits=1, max_digits=3, decimals=2)

    for val in [0.005, 5, 5_000, 5_000_000, 5_000_000_000]:
        m = Measurement(power_w, val)
        print(f"{val:>15} W -> {m.pretty()}")

    print("\n=== Energy Examples ===")
    energy = QUANTITIES["energy"]
    energy_j = BaseMeasurement(energy["J"], min_digits=1, max_digits=3, decimals=2)

    for val in [0.5, 500, 500_000, 3_600_000, 3_600_000_000]:
        m = Measurement(energy_j, val)
        print(f"{val:>15} J -> {m.pretty()}")

    print("\n=== Custom Currency Example (EUR) ===")
    eur = create_currency_quantity("€", "Euro")
    eur_base = BaseMeasurement(eur["€"], min_digits=1, max_digits=3, decimals=2)

    for val in [50, 5_000, 500_000, 50_000_000]:
        m = Measurement(eur_base, val)
        print(f"€{val:>15,.2f} -> {m.pretty()}")

    print("\n=== Scale to Same Unit Examples ===")
    # Example 1: Different lengths in different units
    length = QUANTITIES["length"]
    m1 = Measurement(BaseMeasurement(length["mm"], decimals=2), 1_500_000)
    m2 = Measurement(BaseMeasurement(length["km"], decimals=2), 2.5)

    print(f"Measurement 1: {m1}")
    print(f"Measurement 2: {m2}")
    print(f"M1 scaled to M2's unit: {m1.scale_to_unit(m2.unit)}")
    print(f"M2 scaled to M1's unit: {m2.scale_to_unit(m1.unit)}")

    # Example 2: Money at different scales
    print()
    money = QUANTITIES["money"]
    revenue = Measurement(BaseMeasurement(money["$"], decimals=2), 1_234_567)
    budget = Measurement(BaseMeasurement(money["M$"], decimals=2), 5.5)

    print(f"Revenue: {revenue}")
    print(f"Budget: {budget}")
    print(f"Revenue in M$: {revenue.scale_to_unit(budget.unit)}")
    print(f"Budget in $: {budget.scale_to_unit(revenue.unit)}")

    # Example 3: Compare auto-scaled measurements
    print()
    time = QUANTITIES["time"]
    time_s = BaseMeasurement(time["s"], min_digits=1, max_digits=2, decimals=1)

    t1 = Measurement(time_s, 45)
    t2 = Measurement(time_s, 7_200)

    t1_scaled = t1.scale()
    t2_scaled = t2.scale()

    print(f"Time 1 (auto-scaled): {t1_scaled}")
    print(f"Time 2 (auto-scaled): {t2_scaled}")
    print(f"Time 1 matched to Time 2's unit: {t1.scale_to_unit(t2_scaled.unit)}")
    print(f"Time 2 matched to Time 1's unit: {t2.scale_to_unit(t1_scaled.unit)}")


if __name__ == "__main__":
    example_usage()
