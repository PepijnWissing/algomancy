(fundamentals-frontend-ref)=
# Web application

## Pages
The frontend is built using **Plotly Dash** and is organized into several functional areas:
- **Home Page**: Landing page of the application.
- **Data Page**: Allows users to import, export, view, and manipulate underlying `DataSource`s.
- **Scenario Page**: The main workspace for creating scenarios, tuning algorithm parameters, executing runs, and visualizing specific results.
- **Compare Page**: Enables side-by-side comparison of multiple scenarios, highlighting differences in KPI performance.
- **Overview Page**: Provides a high-level summary of all scenarios in the current session.
- **Admin Page**: Provides access to administrative functions such as session management and logging. 

The frontend follows a **case-dependent** design philosophy: the framework provides the scaffolding (navigation, layout, state management), while the user provides the domain-specific visualizations.

```{note}
Almost all pages can be customized to fit the case requirements, allowing for a flexible and adaptable user interface 
tailored to specific use cases. The `admin` page is an exception, as it provides core functionality. 
```
### Implementation
A page in the Algomancy framework is implemented by subclassing the appropriate base class (e.g., `BaseDataPage`, `BaseScenarioPage`) and defining its layout and behavior through two primary methods:

- **`create_content()`**: Responsible for defining the visual layout of the page. It receives the relevant data object (like a `DataSource` for data pages or a `Scenario` for scenario pages) and returns a Dash component tree (typically an `html.Div`).
- **`register_callbacks()`**: A static method used to define the interactive behavior of the page. This is where Dash `@app.callback` functions are registered to handle user inputs and update the UI dynamically.

:::{dropdown} {octicon}`eye` Example: DataPage
:color: success
To create a custom data visualization page, you would subclass `BaseDataPage`. This class ensures that the page is 
provided with the current `DataSource` when it is rendered. 
```{code-block} python
:caption: Custom data page
:linenos: 
from dash import html, dcc
from algomancy_content import BaseDataPage

class MyDataPage(BaseDataPage):
    @staticmethod
    def create_content(data):
        # 'data' is the current DataSource object
        return html.Div([
            html.H2(f"Analyzing: {data.name}"),
            dcc.Graph(figure=create_custom_plot(data))
        ])

    @staticmethod
    def register_callbacks():
        # Define interactivity here
        pass
```
The page creation template can then be passed to the app via the AppConfiguration. 
```{code-block} python
:caption: Using Pages in the AppConfiguration
:linenos: 
config = AppConfiguration(
    ...
    data_page=MyDataPage(),
    ...
)
```
:::
```{tip}
As the **Compare** and **Scenario** pages often share similar visualization requirements, it is recommended to build 
reusable components that can be called from the `create_content` methods of both page types to maintain consistency.
```

### Intended use
The frontend is designed to support a hierarchical workflow of exploration and decision-making:

1.  **Scenario Page (The Workspace)**: This is the primary entry point for active work. Users create new scenarios, tune algorithm parameters, and execute runs. Once a run is complete, this page provides a "deep dive" into the specific results of that single scenario.
2.  **Compare Page (The Evaluator)**: Once multiple scenarios have been executed, the Compare page allows for a side-by-side evaluation. The focus here is on identifying significant differences in KPI performance and understanding how parameter changes influenced the results.
3.  **Overview Page (The Summary)**: Provides a high-level "eagle-eye" view of all scenarios in the session. It is used to quickly assess the overall progress and identify the most promising scenarios for further investigation.

#### Data Management
The framework provides built-in functions for managing `DataSource` objects, accessible through the UI:
- **Derive**: Create a new `DataSource` based on an existing one, allowing for controlled modifications.
- **Save/Delete**: Persist or remove data sources from the backend storage.
- **Import**: Bring external source files in to the framework and trigger ETL. 
- **Upload**: Bring a serialized `DataSource` into the framework. 
- **Download**: Export a `DataSource` for external use.

For a complete technical description of the page classes and their interfaces, refer to the {ref}`Pages reference <pages-ref>`.

## Styling
Consistency in the visual interface is maintained through the `StylingConfigurator`. This component allows you to define a cohesive theme for the entire application, including:

- **Theme Colors**: Primary, secondary, and tertiary colors used for backgrounds, headers, and accents.
- **Logos and Branding**: Paths to custom logo and button images.
- **Highlight Modes**: Options for how cards and surfaces are shaded relative to the theme (e.g., light, subtle-dark).
- **Button Styling**: Options for unified button colors or separate colors for different functional actions (e.g., a specific color for "Delete" vs. "Save").

Consistent layout and spacing are handled by the framework's CSS, ensuring that custom-built pages still feel like part of the unified application.

For detailed configuration options, see the {ref}`Styling configuration reference <styling-ref>`.
