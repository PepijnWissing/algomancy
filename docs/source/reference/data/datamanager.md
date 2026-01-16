# DataManager

The DataManager class is responsible for data ingestion and internal storage. 
It is usually not accessed directly, but rather through the ScenarioManager facade. 
We distinguish between two types of DataManagers:
- `StatefulDataManager`
- `StatelessDataManager`

The former is able to save data sets to the drive and load said data on startup; the latter does not have this behavior.
 
```{eval-rst}
.. automodule:: algomancy_data.datamanager
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource
```
