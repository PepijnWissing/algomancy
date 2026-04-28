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
### Set up basic project
Follow the instructions in {ref}`quickstart-ref` to get set up with a basic project layout.

### Data
The tutorial data, as well as the final code, are available at [this link](https://github.com/PepijnWissing/Algomancy). 
Download the data files from the project and place them in your `data/` directory. It should look like:
```text
root/
...
├── data/ 
│   ├── dc.xlsx
│   ├── otherlocations.xlsx
│   └── stores.csv
...
```

```{tip}
The tutorial data is available at [this link](https://github.com/PepijnWissing/Algomancy), under tutorial/data
```

## Next step
With the basic project setup in place, we can start building the Algomancy app. 
We choose to start off by creating the data-intake procedure, on the {ref}`next page<tutorial-etl-ref>`. 

