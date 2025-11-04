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


class ImprovementDirection(StrEnum):
    HIGHER = auto()
    LOWER = auto()
