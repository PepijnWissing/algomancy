from .asisalgorithm import AsIsAlgorithm
from .batchingalgorithm import BatchingAlgorithm
from .randomalgorithm import RandomAlgorithm
from .slowalgorithm import SlowAlgorithm
from .warehouse_slotting import AsIsSlotting, GreedySlotting, SimulatedAnnealingSlotting

algorithm_templates = {
    "As is": AsIsAlgorithm,
    "Batching": BatchingAlgorithm,
    "Random": RandomAlgorithm,
    "Slow": SlowAlgorithm,
    "AsIs Slotting": AsIsSlotting,
    "Greedy Slotting": GreedySlotting,
    "SA Slotting": SimulatedAnnealingSlotting,
}
