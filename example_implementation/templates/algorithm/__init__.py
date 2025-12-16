from .asisalgorithm import AsIsAlgorithm
from .batchingalgorithm import BatchingAlgorithm
from .randomalgorithm import RandomAlgorithm
from .slowalgorithm import SlowAlgorithm

algorithm_templates = {
    "As is": AsIsAlgorithm,
    "Batching": BatchingAlgorithm,
    "Random": RandomAlgorithm,
    "Slow": SlowAlgorithm,
}
