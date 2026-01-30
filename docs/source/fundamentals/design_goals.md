(design-goals-ref)=
# Design goals

## Robust and reliable
The framework is designed with a strong emphasis on robustness, reliability, and flexibility. Its modular backend architecture divides the system into smaller, manageable components, making development and maintenance straightforward. Leveraging the mature Dash framework for the frontend ensures extensibility and ease of customization, while integrated logging facilitates effective debugging and monitoring.

## Customizable backend
A key design goal is to provide a customizable backend. Users are encouraged to implement their own algorithms and data sources, allowing the framework to support a wide range of applications without being limited to a specific use case. For more advanced requirements, users can extend the standard classes, using the framework as a library and tailoring its core functionality to their needs.

## Minimize boiler plate code
The framework is designed to minimize the amount of boilerplate code required to implement a new algorithm or data source. This approach ensures that users can focus on the core logic of their application, while the framework handles the details of data management, processing, and visualization.

## Case-dependent frontend
The frontend is intentionally case-dependent, offering only the scaffolding dictated by the backend architecture. It is designed for easy extension, enabling users to supply functions that render page content and define custom callback functions for interactive elements. This approach ensures a highly flexible and customizable frontend, empowering developers to focus on creating visualizations specific to their scenarios.

## Single-responsibility principle
Adhering to the single-responsibility principle, the framework breaks down requirements into distinct components, each with a clear and focused purpose. This structure enhances code clarity, simplifies testing, and improves maintainability.
