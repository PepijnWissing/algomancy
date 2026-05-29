(fundamentals-ref)=
# Framework overview

The Algomancy framework is a web-based application designed for the analysis, visualization, and comparison of complex 
analytical scenarios. It provides a structured environment where users can define data sources, implement algorithms, 
and evaluate results through a set of KPIs.

The framework is built with a strong emphasis on **modularity**, **extensibility**, and **reliability**. By adhering to the single-responsibility principle, it divides the system into distinct layers—Data, Logic, Execution, and Analysis—ensuring that each component has a clear and focused purpose. This architecture not only simplifies development and maintenance but also allows the framework to scale with the complexity of the problems it addresses.

Key features and design goals include:
- **Customizable Backend**: Users can implement their own algorithms and data processes, tailoring the core functionality to their specific needs.
- **Minimal Boilerplate**: The framework handles the heavy lifting of data management, state persistence, and communication, letting developers focus on their core logic.
- **Flexible Frontend**: Built on Plotly Dash, the frontend provides a robust scaffolding for navigation and state management while remaining highly customizable for domain-specific visualizations.

For a deeper dive into the principles and components that make up Algomancy, explore the following sections:
- [Scenario architecture](scenario-architecture-ref): A detailed look at the `DataSource`, `Algorithm`, `Scenario`, and `KPI` components.
- [Frontends](fundamentals-frontends-ref): The three ways to drive an Algomancy backend — Dash GUI, CLI shell, and HTTP API.
- [Graphical interface](fundamentals-frontend-ref): An overview of the Dash web interface and its functional areas.

```{toctree}
:maxdepth: 1
:hidden:

architecture
frontends
front_end
extending
```