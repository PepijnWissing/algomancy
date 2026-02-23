(fundamentals-result-ref)=
## Scenario Result

A `ScenarioResult` is the direct output of an `Algorithm`. It represents the "solution" to the problem defined by a `DataSource` and serves as a detailed record of the algorithm's execution.

While a `DataSource` describes the world and its constraints, the `ScenarioResult` describes what happened within that world once the algorithm was applied.

### The Role of ScenarioResult

The `ScenarioResult` serves several critical functions in the framework:

1.  **Capturing the Solution**: It stores all the relevant details of the result produced by the algorithm. This might include a schedule, a set of assigned resources, optimized parameters, or any other domain-specific output.
2.  **Tracking Execution Metadata**: By default, it records which `DataSource` it was run against (`data_id`) and when the execution was completed (`completed_at`).
3.  **Providing a Foundation for KPIs**: Because raw results are often dense and complex, they are difficult to compare directly. The `ScenarioResult` acts as the data source for KPIs, which distill this complexity into a few comparable numbers.

You can think of a `ScenarioResult` as a "snapshot" of a specific moment in time—the state of the world after the algorithm has finished its work. 

Imagine you are using an algorithm to solve a delivery routing problem. 
*   The **DataSource** defines the locations, the trucks, and the delivery windows.
*   The **Algorithm** calculates the best paths for those trucks.
*   The **ScenarioResult** is the resulting schedule: which truck goes where, in what order, and at what time.
*   The **Scenario** ties all of these together, providing an access point for the front-end.

### Extension and Customization

The base `ScenarioResult` class is purposely minimal. In most applications, you will extend it to include fields that are specific to your domain. This allows you to store structured data that is easy for your KPIs to access and for your front-end to visualize.

For in-depth technical detail, refer to the {ref}`Scenario Result reference <result-ref>`.
