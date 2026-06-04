(scenario-architecture-ref)=
# Scenario architecture
 
The backend of the framework is structured around a clear conceptual model. At its core, the model consists of several
primary components: `DataSource`, `Algorithm`, `Scenario`, `ScenarioResult`, and `KPI`. Each plays a distinct role in 
representing, processing, and analyzing data within the system.

The following diagram illustrates the overall architecture and the relationships between these components:

```{eval-rst}
.. mermaid::

    flowchart LR
        subgraph Data [Data Layer]
            Raw([Raw Data]) --> ETL{ETL Process}
            ETL --> DS[DataSource]
        end

        subgraph Logic [Logic Layer]
            Params([Parameters]) --> Algo[Algorithm]
            Template([Template]) --> Algo
        end

        subgraph Execution [Execution Layer]
            DS --> Scen[Scenario]
            Algo --> Scen
            Scen --> Run{Run}
            Run --> Res[Scenario Result]
        end

        subgraph Analysis [Analysis Layer]
            Res --> KPI_Comp{Compute KPIs}
            KPI_Comp --> KPIs[KPI Results]
            KPIs --> Viz[Visualization]
            Viz --> Dash((Dashboard))
        end
```

## DataSource
A `DataSource` serves as the foundation for any scenario, encapsulating the data required to describe a physical or 
logical situation. Typically, this data is aggregated from multiple files through an **Extract, Transform, Load (ETL)** 
process, which standardizes and prepares the information for further analysis. 

The framework distinguishes between:
- **Master Data**: Immutable data tied directly to source files.
- **Derived Data**: Data that can be modified or extended during an experiment.

To optimize performance, the framework supports serialization and deserialization of data sources to and from JSON, 
significantly reducing loading times for large datasets. Additionally, the `DataSource` component is designed to be 
extensible, allowing developers to implement object-oriented data models tailored to their specific domain requirements.

> A **DataSource** should **define** the world in which one is trying to solve a problem. It should **not** contain any 
> logic about **how** to solve the problem.

## Algorithm
The `Algorithm` component defines the logic that processes a `DataSource` and produces a `ScenarioResult`. This 
transformation can range from straightforward business rule evaluations to sophisticated optimization or machine 
learning procedures. 

Key aspects of an `Algorithm` include parameters, execution, and progress tracking. 
Parameters are defined using `BaseParameterSet` and allow users to tune the algorithm's behavior without changing the code. 
Algorithms run against a `DataSource` to produce results, with built-in support for tracking and reporting execution progress.

> An **Algorithm** should contain the **logic** and parameters for processing a `DataSource` into a `ScenarioResult`. It 
> should **not** contain any data manipulation.

An elaborated intuitive explanation can be found [here](fundamentals-algorithm-ref); a complete technical explanation 
can be found in the [reference](algorithm-ref).

## Scenario
A `Scenario` represents a unique combination of a `DataSource` and an `Algorithm` (with a specific set of parameters). 
It encapsulates both the input data and the processing logic, serving as the primary unit of execution in the framework.

Scenarios manage the lifecycle of a run through three stages. 
Creation involves binding data and algorithm together.
During queuing and processing, the execution state is managed. 
Finally, completion entails storing the resulting `ScenarioResult` and triggering KPI computation.

> A **Scenario** facilitates the interaction between `DataSource` and `Algorithm` to produce a `ScenarioResult`, and 
> provides a structured way for the front-end and the back-end to communicate. 

## ScenarioResult
The `ScenarioResult` captures the raw output of an `Algorithm` after execution. 
When an algorithm processes a `DataSource`, it produces a result object that contains all the computational outputs, 
solution details, and any intermediate artifacts generated during the run.

While the result itself contains the complete details of the "solution," it is often too dense and detailed for direct 
comparison between different scenarios. The raw data may include complex data structures, large datasets, or numerous 
intermediate calculations that make side-by-side evaluation challenging. This is where KPIs become essential—they 
extract and summarize the most relevant metrics from these comprehensive results.

A `ScenarioResult` typically stores references to its source data, execution metadata (such as completion time), and 
domain-specific outputs that are meaningful for your particular use case. By design, the framework provides a minimal 
base implementation that you extend to capture your algorithm's specific outputs.

For in-depth technical detail, refer to the {ref}`Scenario Result reference <result-ref>`.

## KPI
**Key Performance Indicators (KPIs)** are used to distill `ScenarioResult`s into comparable metrics. They serve as the 
primary mechanism for extracting meaningful, quantifiable insights from complex algorithmic outputs, enabling users to 
quickly evaluate and compare the quality of different solutions.

Each KPI defines a specific metric (e.g., "Total Cost", "Throughput", "Service Level") that represents an important 
aspect of solution quality. The KPI implements a `compute` method that knows how to extract and calculate this metric 
from a `ScenarioResult`, translating raw output data into a single, interpretable value. Additionally, KPIs can include 
thresholds for "success" or "failure" (binary KPIs), allowing you to define acceptance criteria and automatically flag 
solutions that don't meet requirements.

KPIs leverage the framework's measurement system for intelligent unit formatting and automatic scaling, ensuring values 
are displayed in human-readable formats (e.g., "2.5 km" instead of "2500 m", or "$1.2M" instead of "$1,234,567"). This 
makes comparison across scenarios intuitive and accessible.

For in-depth technical detail, refer to the {ref}`KPI reference <kpi-ref>`.


## Sessions
The framework wraps every running backend in a `SessionManager` that owns
one or more **sessions** — each an isolated workspace with its own
scenarios, runs, KPIs, and data. The split between an immutable session
``id`` (UUID) and a mutable ``display_name`` is what lets you rename or
reorganize workspaces without breaking URLs or database FKs.

See {ref}`Sessions <fundamentals-sessions-ref>` for the full model:
identity, persistence backends (filesystem vs. database), lifecycle, and
how the HTTP API / Dash GUI scope by session.

## More
For an in-depth discussion of the underlying concepts, visit the pages below. 
```{toctree}
:maxdepth: 1

data
ETL
algorithms
result
sessions
```
