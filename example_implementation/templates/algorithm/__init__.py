from .AsIsAlgorithmTemplate import as_is_algorithm_template
from .BatchingAlgorithmTemplate import batching_algorithm_template
from .RandomAlgorithmTemplate import random_algorithm_template
from .SlowSampleAlgorithmTemplate import slow_sample_algorithm_template

algorithm_templates = {
    as_is_algorithm_template.name: as_is_algorithm_template,
    batching_algorithm_template.name: batching_algorithm_template,
    random_algorithm_template.name: random_algorithm_template,
    slow_sample_algorithm_template.name: slow_sample_algorithm_template,
}
