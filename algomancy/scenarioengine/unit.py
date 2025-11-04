from typing import List, Tuple, Dict

"""
Unit framework for scaling measurements

todo write details
"""


# ============================================================================
# Scaling unit framework
# ============================================================================
class Quantity:
    def __init__(self, name: str, standard_unit: BaseUnit):
        self.name: str = name
        self.standard_unit: BaseUnit = standard_unit
        self.sorted_units: List[Tuple[BaseUnit, float]] = [(standard_unit, 1)]
        self.associated_units: Dict[str, BaseUnit] = {standard_unit.name: standard_unit}

    def __getitem__(self, key) -> BaseUnit | None:
        try:
            return self.associated_units[key]
        except KeyError:
            raise KeyError(f"Unit '{key}' not found in quantity '{self.name}'\n"
                           f"  Available units are: {', '.join(self.associated_units.keys())}")

    def add_unit(self, base_unit: BaseUnit, factor_to_base: float):
        if base_unit.name in self.associated_units:
            raise ValueError(f"Unit '{base_unit.name}' already exists in quantity '{self.name}'")
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
            unit.set_larger_unit(
                next_unit,
                factor / next_factor
            )


class BaseUnit:
    def __init__(self, name: str, symbol: str):
        self.name: str = name
        self.symbol: str = symbol
        self.smaller_unit: 'BaseUnit | None' = None
        self.conversion_factor_to_smaller: float | None = None
        self.larger_unit: 'BaseUnit | None' = None
        self.conversion_factor_to_larger: float | None = None

    def __str__(self):
        return f'Unit: {self.name}, ({self.symbol})'

    def _set_smaller_unit(self, smaller_unit: 'BaseUnit', conversion_factor: float):
        self.smaller_unit = smaller_unit
        self.conversion_factor_to_smaller = conversion_factor

    def set_larger_unit(self, larger_unit: 'BaseUnit', conversion_factor: float):
        self.larger_unit = larger_unit
        self.conversion_factor_to_larger = conversion_factor

        larger_unit._set_smaller_unit(self, 1 / conversion_factor)


class BaseMeasurement:
    def __init__(
            self,
            base_unit: BaseUnit,
            min_digits: int = 0,
            max_digits: int = 3,
            decimals: int = 2,
            smallest_unit: str | None = None,
            largest_unit: str | None = None,
    ):
        self.unit: BaseUnit = base_unit
        self.min_digits: int = min_digits
        self.max_digits: int = max_digits
        self.decimals: int = decimals
        self.smallest_unit: str | None = smallest_unit
        self.largest_unit: str | None = largest_unit

    def __str__(self):
        return (f"{self.unit.name}, {self.unit.symbol} | {self.min_digits} to {self.max_digits} digits |"
                f" {self.decimals} decimals")


class Measurement:
    INITIAL_VALUE = -9999999999

    def __init__(self, base_measurement: BaseMeasurement, value: float = INITIAL_VALUE):
        self.base_measurement: BaseMeasurement = base_measurement
        self.value: float = value
        self.unit: BaseUnit = base_measurement.unit

    def __str__(self):
        return f"{self.value} {self.unit.symbol}"

    def pretty(self) -> str:
        return f'{str(self.scale())}'

    def _format_value(self) -> str:
        """Format the value according to the specified decimal places"""
        return f"{self.value:.{self.base_measurement.decimals}f}"

    def scale(self) -> 'Measurement':
        """Scale the measurement to fit within the desired digit range"""
        # Handle edge case of zero
        if self.value == 0:
            return Measurement(self.base_measurement, 0)

        # determine the number of digits (ignoring sign and decimal)
        n_digits = len(str(int(abs(self.value))))

        # if the number of digits is within the range, return formatted measurement
        if self.base_measurement.min_digits <= n_digits <= self.base_measurement.max_digits:
            formatted_value = float(self._format_value())
            return Measurement(self.base_measurement, formatted_value)

        # Too many digits - scale up to larger unit
        elif n_digits > self.base_measurement.max_digits:
            return self._scale_up()

        # Too few digits - scale down to smaller unit
        else:
            return self._scale_down()

    def scale_to_unit(self, other: 'Measurement') -> 'Measurement':
        """
        Scale this measurement to use the same unit as another measurement.

        Args:
            other: The measurement whose unit to match

        Returns:
            A new Measurement with the same unit as other

        Raises:
            ValueError: If the measurements are incompatible (different quantity types)
        """
        # If already the same unit, just return a copy with formatted value
        if self.unit.name == other.unit.name:
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
                formatted_value
            )

        # Find conversion path from self to other's unit
        conversion_factor = self._find_conversion_factor(other.unit)

        if conversion_factor is None:
            raise ValueError(
                f"Cannot convert from {self.unit.name} to {other.unit.name}: "
                f"units are not in the same quantity system"
            )

        # Convert value to target unit
        new_value = self.value * conversion_factor

        # Create new measurement with other's unit
        new_base_measurement = BaseMeasurement(
            base_unit=other.unit,
            min_digits=self.base_measurement.min_digits,
            max_digits=self.base_measurement.max_digits,
            decimals=self.base_measurement.decimals,
            smallest_unit=self.base_measurement.smallest_unit,
            largest_unit=self.base_measurement.largest_unit,
        )

        return Measurement(new_base_measurement, new_value)

    def _find_conversion_factor(self, target_unit: BaseUnit) -> float | None:
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

    def _scale_up(self) -> 'Measurement':
        """Scale up to a larger unit"""
        # Check if we can scale up
        if self.unit.larger_unit is None:
            # Already at largest unit, return as is
            formatted_value = float(self._format_value())
            return Measurement(self.base_measurement, formatted_value)

        # Check if largest_unit constraint prevents scaling
        if (self.base_measurement.largest_unit is not None and
                self.unit.name == self.base_measurement.largest_unit):
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

    def _scale_down(self) -> 'Measurement':
        """Scale down to a smaller unit"""
        # Check if we can scale down
        if self.unit.smaller_unit is None:
            # Already at smallest unit, return as is
            formatted_value = float(self._format_value())
            return Measurement(self.base_measurement, formatted_value)

        # Check if smallest_unit constraint prevents scaling
        if (self.base_measurement.smallest_unit is not None and
                self.unit.name == self.base_measurement.smallest_unit):
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
    length = Quantity("Length", BaseUnit("m", "m"))
    # Smaller units
    length.add_unit(BaseUnit("mm", "mm"), 0.001)
    length.add_unit(BaseUnit("cm", "cm"), 0.01)
    length.add_unit(BaseUnit("dm", "dm"), 0.1)
    # Larger units
    length.add_unit(BaseUnit("km", "km"), 1_000)
    # Micro and nano
    length.add_unit(BaseUnit("μm", "μm"), 0.000_001)
    length.add_unit(BaseUnit("nm", "nm"), 0.000_000_001)
    # Mega
    length.add_unit(BaseUnit("Mm", "Mm"), 1_000_000)
    return length


def create_mass_quantity() -> Quantity:
    """Create a mass quantity with metric units"""
    mass = Quantity("Mass", BaseUnit("g", "g"))
    # Smaller units
    mass.add_unit(BaseUnit("mg", "mg"), 0.001)
    mass.add_unit(BaseUnit("μg", "μg"), 0.000_001)
    # Larger units
    mass.add_unit(BaseUnit("kg", "kg"), 1_000)
    mass.add_unit(BaseUnit("t", "t"), 1_000_000)  # metric ton
    mass.add_unit(BaseUnit("kt", "kt"), 1_000_000_000)  # kiloton
    mass.add_unit(BaseUnit("Mt", "Mt"), 1_000_000_000_000)  # megaton
    return mass


def create_time_quantity() -> Quantity:
    """Create a time quantity with various units"""
    time = Quantity("Time", BaseUnit("s", "s"))
    # Smaller units
    time.add_unit(BaseUnit("ms", "ms"), 0.001)
    time.add_unit(BaseUnit("μs", "μs"), 0.000_001)
    time.add_unit(BaseUnit("ns", "ns"), 0.000_000_001)
    # Larger units
    time.add_unit(BaseUnit("min", "min"), 60)
    time.add_unit(BaseUnit("h", "h"), 3_600)
    time.add_unit(BaseUnit("d", "d"), 86_400)
    time.add_unit(BaseUnit("wk", "wk"), 604_800)
    time.add_unit(BaseUnit("yr", "yr"), 31_536_000)
    return time


def create_area_quantity() -> Quantity:
    """Create an area quantity with metric units"""
    area = Quantity("Area", BaseUnit("m²", "m²"))
    # Smaller units
    area.add_unit(BaseUnit("mm²", "mm²"), 0.000_001)
    area.add_unit(BaseUnit("cm²", "cm²"), 0.0001)
    area.add_unit(BaseUnit("dm²", "dm²"), 0.01)
    # Larger units
    area.add_unit(BaseUnit("km²", "km²"), 1_000_000)
    area.add_unit(BaseUnit("ha", "ha"), 10_000)  # hectare
    return area


def create_volume_quantity() -> Quantity:
    """Create a volume quantity with metric units"""
    volume = Quantity("Volume", BaseUnit("L", "L"))
    # Smaller units
    volume.add_unit(BaseUnit("mL", "mL"), 0.001)
    volume.add_unit(BaseUnit("cL", "cL"), 0.01)
    volume.add_unit(BaseUnit("dL", "dL"), 0.1)
    # Larger units
    volume.add_unit(BaseUnit("m³", "m³"), 1_000)
    volume.add_unit(BaseUnit("kL", "kL"), 1_000)
    # Very small
    volume.add_unit(BaseUnit("μL", "μL"), 0.000_001)
    return volume


def create_speed_quantity() -> Quantity:
    """Create a speed quantity"""
    speed = Quantity("Speed", BaseUnit("m/s", "m/s"))
    speed.add_unit(BaseUnit("km/h", "km/h"), 0.277778)
    speed.add_unit(BaseUnit("cm/s", "cm/s"), 0.01)
    speed.add_unit(BaseUnit("mm/s", "mm/s"), 0.001)
    return speed


def create_temperature_quantity() -> Quantity:
    """Create a temperature quantity (Celsius scale)"""
    temp = Quantity("Temperature", BaseUnit("°C", "°C"))
    # Note: These are NOT convertible via simple multiplication
    # This is a simplified example - real temperature conversion needs offset
    temp.add_unit(BaseUnit("K", "K"), 1)  # Kelvin (simplified)
    return temp


def create_energy_quantity() -> Quantity:
    """Create an energy quantity"""
    energy = Quantity("Energy", BaseUnit("J", "J"))
    # Smaller units
    energy.add_unit(BaseUnit("mJ", "mJ"), 0.001)
    energy.add_unit(BaseUnit("μJ", "μJ"), 0.000_001)
    # Larger units
    energy.add_unit(BaseUnit("kJ", "kJ"), 1_000)
    energy.add_unit(BaseUnit("MJ", "MJ"), 1_000_000)
    energy.add_unit(BaseUnit("GJ", "GJ"), 1_000_000_000)
    energy.add_unit(BaseUnit("kWh", "kWh"), 3_600_000)
    energy.add_unit(BaseUnit("MWh", "MWh"), 3_600_000_000)
    return energy


def create_power_quantity() -> Quantity:
    """Create a power quantity"""
    power = Quantity("Power", BaseUnit("W", "W"))
    # Smaller units
    power.add_unit(BaseUnit("mW", "mW"), 0.001)
    power.add_unit(BaseUnit("μW", "μW"), 0.000_001)
    # Larger units
    power.add_unit(BaseUnit("kW", "kW"), 1_000)
    power.add_unit(BaseUnit("MW", "MW"), 1_000_000)
    power.add_unit(BaseUnit("GW", "GW"), 1_000_000_000)
    return power


def create_pressure_quantity() -> Quantity:
    """Create a pressure quantity"""
    pressure = Quantity("Pressure", BaseUnit("Pa", "Pa"))
    # Smaller/Larger units
    pressure.add_unit(BaseUnit("kPa", "kPa"), 1_000)
    pressure.add_unit(BaseUnit("MPa", "MPa"), 1_000_000)
    pressure.add_unit(BaseUnit("bar", "bar"), 100_000)
    pressure.add_unit(BaseUnit("mbar", "mbar"), 100)
    return pressure


def create_frequency_quantity() -> Quantity:
    """Create a frequency quantity"""
    frequency = Quantity("Frequency", BaseUnit("Hz", "Hz"))
    frequency.add_unit(BaseUnit("kHz", "kHz"), 1_000)
    frequency.add_unit(BaseUnit("MHz", "MHz"), 1_000_000)
    frequency.add_unit(BaseUnit("GHz", "GHz"), 1_000_000_000)
    frequency.add_unit(BaseUnit("mHz", "mHz"), 0.001)
    return frequency


def create_data_quantity() -> Quantity:
    """Create a data storage quantity (binary)"""
    data = Quantity("Data", BaseUnit("B", "B"))
    # Binary prefixes (IEC standard)
    data.add_unit(BaseUnit("KiB", "KiB"), 1_024)
    data.add_unit(BaseUnit("MiB", "MiB"), 1_048_576)
    data.add_unit(BaseUnit("GiB", "GiB"), 1_073_741_824)
    data.add_unit(BaseUnit("TiB", "TiB"), 1_099_511_627_776)
    data.add_unit(BaseUnit("PiB", "PiB"), 1_125_899_906_842_624)
    return data


def create_data_decimal_quantity() -> Quantity:
    """Create a data storage quantity (decimal)"""
    data = Quantity("Data (Decimal)", BaseUnit("B", "B"))
    # Decimal prefixes (SI standard)
    data.add_unit(BaseUnit("KB", "KB"), 1_000)
    data.add_unit(BaseUnit("MB", "MB"), 1_000_000)
    data.add_unit(BaseUnit("GB", "GB"), 1_000_000_000)
    data.add_unit(BaseUnit("TB", "TB"), 1_000_000_000_000)
    data.add_unit(BaseUnit("PB", "PB"), 1_000_000_000_000_000)
    return data


def create_money_quantity() -> Quantity:
    """Create a money quantity with scaling prefixes"""
    money = Quantity("Money", BaseUnit("$", "$"))
    money.add_unit(BaseUnit("k$", "k$"), 1_000)
    money.add_unit(BaseUnit("M$", "M$"), 1_000_000)
    money.add_unit(BaseUnit("B$", "B$"), 1_000_000_000)
    money.add_unit(BaseUnit("T$", "T$"), 1_000_000_000_000)
    # Cents
    money.add_unit(BaseUnit("¢", "¢"), 0.01)
    return money


def create_currency_quantity(symbol: str, name: str) -> Quantity:
    """Create a generic currency quantity"""
    currency = Quantity(name, BaseUnit(symbol, symbol))
    currency.add_unit(BaseUnit(f"k{symbol}", f"k{symbol}"), 1_000)
    currency.add_unit(BaseUnit(f"M{symbol}", f"M{symbol}"), 1_000_000)
    currency.add_unit(BaseUnit(f"B{symbol}", f"B{symbol}"), 1_000_000_000)
    return currency


def create_percentage_quantity() -> Quantity:
    """Create a percentage quantity"""
    percentage = Quantity("Percentage", BaseUnit("%", "%"))
    percentage.add_unit(BaseUnit("‰", "‰"), 0.1)  # per mille
    percentage.add_unit(BaseUnit("bp", "bp"), 0.01)  # basis points
    return percentage


def create_count_quantity() -> Quantity:
    """Create a generic count quantity for items"""
    count = Quantity("Count", BaseUnit("", ""))
    count.add_unit(BaseUnit("k", "k"), 1_000)
    count.add_unit(BaseUnit("M", "M"), 1_000_000)
    count.add_unit(BaseUnit("B", "B"), 1_000_000_000)
    return count


def create_electric_current_quantity() -> Quantity:
    """Create an electric current quantity"""
    current = Quantity("Electric Current", BaseUnit("A", "A"))
    current.add_unit(BaseUnit("mA", "mA"), 0.001)
    current.add_unit(BaseUnit("μA", "μA"), 0.000_001)
    current.add_unit(BaseUnit("kA", "kA"), 1_000)
    return current


def create_voltage_quantity() -> Quantity:
    """Create a voltage quantity"""
    voltage = Quantity("Voltage", BaseUnit("V", "V"))
    voltage.add_unit(BaseUnit("mV", "mV"), 0.001)
    voltage.add_unit(BaseUnit("μV", "μV"), 0.000_001)
    voltage.add_unit(BaseUnit("kV", "kV"), 1_000)
    voltage.add_unit(BaseUnit("MV", "MV"), 1_000_000)
    return voltage


def create_resistance_quantity() -> Quantity:
    """Create an electrical resistance quantity"""
    resistance = Quantity("Resistance", BaseUnit("Ω", "Ω"))
    resistance.add_unit(BaseUnit("mΩ", "mΩ"), 0.001)
    resistance.add_unit(BaseUnit("kΩ", "kΩ"), 1_000)
    resistance.add_unit(BaseUnit("MΩ", "MΩ"), 1_000_000)
    return resistance


def create_default_quantity() -> Quantity:
    """Create a default quantity with a single unit"""
    default = Quantity("Default", BaseUnit("unit", ""))
    # default.add_unit(BaseUnit("default", ""), 1)
    return default


# ============================================================================
# Standard Quantities Registry
# ============================================================================

class QuantityRegistry:
    """Registry for commonly used quantities"""

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
            raise KeyError(f"Quantity '{name}' not found in registry.\n "
                           f"  Available quantities: {self.list_quantities()}")
        return quantity


# Global registry instance
QUANTITIES = QuantityRegistry()

if __name__ == "__main__":
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
    time_s = BaseMeasurement(time["s"], min_digits=1, max_digits=2, decimals=1)

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
    print(f"M1 scaled to M2's unit: {m1.scale_to_unit(m2)}")
    print(f"M2 scaled to M1's unit: {m2.scale_to_unit(m1)}")

    # Example 2: Money at different scales
    print()
    money = QUANTITIES["money"]
    revenue = Measurement(BaseMeasurement(money["$"], decimals=2), 1_234_567)
    budget = Measurement(BaseMeasurement(money["M$"], decimals=2), 5.5)

    print(f"Revenue: {revenue}")
    print(f"Budget: {budget}")
    print(f"Revenue in M$: {revenue.scale_to_unit(budget)}")
    print(f"Budget in $: {budget.scale_to_unit(revenue)}")

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
    print(f"Time 1 matched to Time 2's unit: {t1.scale_to_unit(t2_scaled)}")
    print(f"Time 2 matched to Time 1's unit: {t2.scale_to_unit(t1_scaled)}")
