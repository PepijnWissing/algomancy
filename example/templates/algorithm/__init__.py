from .asisalgorithm import AsIsAlgorithm
from .batchingalgorithm import BatchingAlgorithm
from .randomalgorithm import RandomAlgorithm
from .slowalgorithm import SlowAlgorithm
from .edge_instant import InstantAlgorithm
from .edge_progress_long import LongProgressAlgorithm
from .edge_failure_modes import FailureModesAlgorithm
from .edge_parameter_matrix import ParameterMatrixAlgorithm

algorithm_templates = {
    "As is": AsIsAlgorithm,
    "Batching": BatchingAlgorithm,
    "Random": RandomAlgorithm,
    "Slow": SlowAlgorithm,
    "Instant": InstantAlgorithm,
    "Long Progress": LongProgressAlgorithm,
    "Failure Modes": FailureModesAlgorithm,
    "Parameter Matrix": ParameterMatrixAlgorithm,
}
