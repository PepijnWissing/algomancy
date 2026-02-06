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
In this section, we will discuss the step-by-step implementation of a basic application
## Outline
We use an example of a TSP problem in this problem. 

```{warning}
The outline section of this tutorial is incomplete. A basic description of the tutorial intentions should be added
```

## Setting up
### Set up basic project
Follow the instructions in {ref}`quickstart-ref` to get set up with a basic project layout.

### Data
The tutorial data, as well as the final code, are available at [this link](http://www.google.com). 
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

```{warning}
The link is currently broken; a github project should be set up to share the data. 
```

## Next step
With the basic project setup in place, we can start building the Algomancy app. 
We choose to start off by creating the data-intake procedure, on the {ref}`next page<tutorial-etl-ref>`. 

