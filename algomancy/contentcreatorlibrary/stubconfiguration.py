from algomancy.appconfiguration import AppConfiguration
from algomancy.contentcreatorlibrary import PlaceholderETLFactory
from algomancy.contentcreatorlibrary.placeholderalgorithmtemplate import placeholder_algorithm_template
from algomancy.contentcreatorlibrary.placeholderinputconfig import placeholder_input_config
from algomancy.contentcreatorlibrary.placeholderkpitemplate import placeholder_kpi_template

stub_configuration = AppConfiguration(
    etl_factory=PlaceholderETLFactory,
    kpi_templates=[placeholder_kpi_template],
    algo_templates={placeholder_algorithm_template.name: placeholder_algorithm_template},
    input_configs=[placeholder_input_config],
)