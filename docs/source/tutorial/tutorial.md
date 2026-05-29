(tutorial-ref)=
# Tutorial
```{toctree}
:maxdepth: 1
:hidden:
etl
results
kpi
algorithms
pages
```
In this tutorial, we build a complete Algomancy application step by step, using a vehicle routing example to illustrate each framework concept in context.

## What we are building

We model a **Traveling Salesman Problem (TSP)**: given a set of locations distributed on a grid, find a route that visits each location exactly once at minimum total cost.
By the end of the tutorial, we will have a fully functioning Algomancy dashboard that can:

- import and validate location data from multiple input files,
- run and compare two routing algorithms against the same dataset,
- evaluate results through a KPI, and
- visualize routes and compare scenario outcomes through a set of custom dashboard pages.

## Steps

The tutorial walks through the following pages in order:

1. **{ref}`Data intake<tutorial-etl-ref>`** — define the input file schemas and implement the {ref}`ETL<etl-ref>` pipeline to extract, validate, transform, and load location data into a domain-specific data model.
2. **{ref}`Results<tutorial-results-ref>`** — create a `ResultModel` class to carry the solution produced by an algorithm.
3. **{ref}`KPIs<tutorial-kpi-ref>`** — define a `TotalCostsKPI` that measures the total travel cost of a computed tour.
4. **{ref}`Algorithms<tutorial-algorithms-ref>`** — implement a deterministic Nearest Neighbor heuristic and a parameter-driven Simulated Annealing algorithm.
5. **{ref}`Pages<tutorial-pages-ref>`** — build custom dashboard pages for scenario detail, side-by-side comparison, and a scenario overview table.

## Setting up

### Data

The tutorial data is available at [this link](https://github.com/PepijnWissing/Algomancy), under `tutorial/data`.
Create a new project directory and place the three input files in a `data/setup/` subdirectory:

```text
root/
└── data/
    └── setup/
        ├── dc.xlsx
        ├── otherlocations.xlsx
        └── stores.csv
```

```{tip}
Placing files in `data/setup/` *before* running the wizard lets it scan and configure the ETL pipeline automatically in Step 3.
```

### Run the quickstart wizard

From your project root, run:

```bash
algomancy-quickstart
```

The wizard walks through five interactive steps. For this tutorial, respond as follows:

**Step 1 – Folder structure**
- *Project title:* `TSP Tutorial` (or any name you like)
- *Host:* `127.0.0.1` (default)
- *Port:* `8050` (default)

**Step 2 – Custom implementation templates**

Accept the prompt (default: yes), then enter `TSP` as the domain name.

The wizard generates skeleton files under `src/` for schemas, ETL, algorithms, KPIs, and all page types, and updates `main.py` to wire them together.

**Step 3 – ETL pipeline from data**

Accept the prompt (default: yes). The wizard scans `data/setup/`, detects the three input files, infers their column types, and generates `src/data_handling/generated_schemas.py` and `src/data_handling/etl_factory.py`.

When prompted for `otherlocations.xlsx`, select all sheets.

**Step 4 – Assets**

Accept (default: yes) to install default CSS and images into `assets/`.

**Step 5 – Styling**

Choose a preset or accept the defaults — either works for this tutorial.

### Project layout after setup

After the wizard completes, your project looks like this:

```text
root/
├── assets/
├── data/
│   └── setup/
│       ├── dc.xlsx
│       ├── otherlocations.xlsx
│       └── stores.csv
├── main.py
└── src/
    ├── data_handling/
    │   ├── etl_factory.py
    │   └── generated_schemas.py
    ├── pages/
    │   ├── compare_page.py
    │   ├── data_page.py
    │   ├── home_page.py
    │   ├── overview_page.py
    │   └── scenario_page.py
    └── templates/
        ├── algorithm/
        │   └── tsp_algorithm.py
        └── kpi/
            └── tsp_kpi.py
```

## Next step
With the project scaffold in place, we can start building the Algomancy app.
We choose to start off by building the data-intake procedure on the {ref}`next page<tutorial-etl-ref>`.
