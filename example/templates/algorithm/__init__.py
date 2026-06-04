from .edge_instant import InstantAlgorithm
from .edge_progress_long import LongProgressAlgorithm
from .edge_failure_modes import FailureModesAlgorithm
from .edge_parameter_matrix import ParameterMatrixAlgorithm
from .warehouse_slotting import AsIsSlotting, GreedySlotting, SimulatedAnnealingSlotting

# The As-is/Batching/Random/Slow classes are kept as minimal BaseAlgorithm
# examples but intentionally NOT registered: they return bare ScenarioResults
# that the warehouse-aware pages can't render meaningfully.
__all__ = [
    "AsIsSlotting",
    "GreedySlotting",
    "SimulatedAnnealingSlotting",
    "algorithms",
]

algorithms = {
    "AsIs Slotting": AsIsSlotting,
    "Greedy Slotting": GreedySlotting,
    "SA Slotting": SimulatedAnnealingSlotting,
    "Instant": InstantAlgorithm,
    "Long Progress": LongProgressAlgorithm,
    "Failure Modes": FailureModesAlgorithm,
    "Parameter Matrix": ParameterMatrixAlgorithm,
}
