from enum import StrEnum, auto


class ScenarioStatus(StrEnum):
    """
    Constants representing the possible states of a scenario.
    """
    CREATED = auto()
    QUEUED = auto()
    PROCESSING = auto()
    COMPLETE = auto()
    FAILED = auto()


class KpiType(StrEnum):
    NUMERIC = auto()
    TIME = auto()
    RATIO = auto()
    PERCENT = auto()


class ImprovementDirection(StrEnum):
    HIGHER = auto()
    LOWER = auto()


class UnitOfMeasurement(StrEnum):
    # Mass/Weight
    KG = auto()  # Kilogram
    G = auto()  # Gram
    MG = auto()  # Milligram
    TON = auto()  # Metric ton

    # Length/Distance
    M = auto()  # Meter
    KM = auto()  # Kilometer
    CM = auto()  # Centimeter
    MM = auto()  # Millimeter

    # Area
    SQ_M = auto()  # Square meter
    SQ_KM = auto()  # Square kilometer
    SQ_CM = auto()  # Square centimeter
    HECTARE = auto()  # Hectare

    # Volume
    L = auto()  # Liter
    ML = auto()  # Milliliter
    CU_M = auto()  # Cubic meter

    # Time
    SEC = auto()  # Second
    MIN = auto()  # Minute
    HOUR = auto()  # Hour
    DAY = auto()  # Day
    WEEK = auto()  # Week
    MONTH = auto()  # Month
    YEAR = auto()  # Year

    # Speed
    KMH = auto()  # Kilometers per hour
    MPS = auto()  # Meters per second

    # Temperature
    C = auto()  # Celsius
    F = auto()  # Fahrenheit
    K = auto()  # Kelvin

    # Pressure
    PA = auto()  # Pascal
    KPA = auto()  # Kilopascal
    MPA = auto()  # Megapascal
    BAR = auto()  # Bar
    PSI = auto()  # Pounds per square inch
    ATM = auto()  # Atmosphere

    # Energy
    J = auto()  # Joule
    KJ = auto()  # Kilojoule
    CAL = auto()  # Calorie
    KCAL = auto()  # Kilocalorie
    KWH = auto()  # Kilowatt-hour

    # Power
    W = auto()  # Watt
    KW = auto()  # Kilowatt
    MW = auto()  # Megawatt
    HP = auto()  # Horsepower

    # Electric
    V = auto()  # Volt
    KV = auto()  # Kilovolt
    A = auto()  # Ampere
    MA = auto()  # Milliampere
    OHM = auto()  # Ohm

    # Data
    BIT = auto()  # Bit
    BYTE = auto()  # Byte
    KB = auto()  # Kilobyte
    MB = auto()  # Megabyte
    GB = auto()  # Gigabyte
    TB = auto()  # Terabyte

    # Frequency
    HZ = auto()  # Hertz
    KHZ = auto()  # Kilohertz
    MHZ = auto()  # Megahertz
    GHZ = auto()  # Gigahertz

    # Angle
    DEG = auto()  # Degree
    RAD = auto()  # Radian

    # Concentration
    PPM = auto()  # Parts per million
    PPB = auto()  # Parts per billion

    # Currency
    USD = auto()  # US Dollar
    EUR = auto()  # Euro
    GBP = auto()  # British Pound

    # Count/Unitless
    UNIT = auto()  # Unit (count)
    PERCENT = auto()  # Percent

