# Introduction 
This package is designed to facilitate dashboarding and visualizations of the performance of algorithms and/or simulations.

# Installation
To install this package, make sure you have the artifacts-keyring package installed. Then, install the algomancy package with the following command:

```
pip install --index-url=https://pkgs.dev.azure.com/cqmbv/WARP/_packaging/WarpPython/pypi/simple/ algomancy
```

# Update version
Option A: Update Pipfile to point to the existing wheel (preferred)
In Pipfile, replace the algomancy source pointing to 0.2.5 with the local 0.2.6 wheel path:
Example: algomancy = {path = "dist/algomancy-0.2.6-py3-none-any.whl"}
Then regenerate lockfile and install:
pipenv lock --clear
pipenv install