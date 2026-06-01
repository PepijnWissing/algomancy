from .asisalgorithm import AsIsAlgorithm
from .batchingalgorithm import BatchingAlgorithm
from .randomalgorithm import RandomAlgorithm
from .slowalgorithm import SlowAlgorithm
from .warehouse_slotting import AsIsSlotting, GreedySlotting, SimulatedAnnealingSlotting

# The As-is/Batching/Random/Slow classes are kept as minimal BaseAlgorithm
# examples but intentionally NOT registered: they return bare ScenarioResults
# that the warehouse-aware pages can't render meaningfully.
__all__ = [
    "AsIsAlgorithm",
    "BatchingAlgorithm",
    "RandomAlgorithm",
    "SlowAlgorithm",
    "AsIsSlotting",
    "GreedySlotting",
    "SimulatedAnnealingSlotting",
    "algorithm_templates",
]

algorithm_templates = {
    "AsIs Slotting": AsIsSlotting,
    "Greedy Slotting": GreedySlotting,
    "SA Slotting": SimulatedAnnealingSlotting,
}
