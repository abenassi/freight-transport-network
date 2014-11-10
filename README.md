freight_transport_network
=========================

Python implementation of a bimodal (railway and roadway) freight transport network cost model.

This a cost model for the freight transport network of Argentina. It is still under heavy development so big changes should be expected and should not be used, as it is still an object of active research on railway and roadway freight transport network costs. The partial results that can be extracted from running the model are not still reliable in any way.

Also, there is no yet a full scheme of unit tests, and docstrings may fail at somepoint if they are not updated quick enough. Some classes are informally tested.

The only module a user should see is freight_network.py, which is the user interface and uses RoadwayNetwork and RailwayNetwork classes from modal_networks.py to build the entire bimodal FreightNetwork.


## Usage

freight_network.py can be run as it is

```cmd
python freight_network.py
```

It takes railway and roadway data from "data" directory:

1. **Links** that make up the network.
2. **OD pairs** with freight in tons being transported.
3. **Parameters** used in calculations.
4. **Paths** being sequences of links used to go from an origin to a destination.

The output is stored in "reports" directory as excel files:

1. **railway_links_by_od.xlsx** is just a table with links used by each od pair.
2. **report_simple_mobility.xlsx** is the result of cost the railway network costing each od pair as it would be serviced independently by trains dedicated only to one od pair freight.
3. **report_optimized_mobility.xlsx** is the result of cost the railway network reorganizing trains in each link to minimize idleness of locomotives capacity (making larger trains of smaller ones when possible).
4. **roadway_results_report.xlsx** is still limited for the moment. RoadwayNetwork cost methods are not yet developed as we are still doing research on truck costs.

You can see in main() method inside freight_network module how user interface and most common usage of the model is going to be. It is not the method triggered when you run freight_network.py, that is replaced by a test method for the moment.


## Test

Existing unit tests can be run all at once just by running run_tests.py

```cmd
python run_tests.py
```


## Find shortest paths

As a separate feature from the main modules structure of the package, there is a dijkstra subpackage to calculate the shortest paths between all nodes from a network.

In dijkstra folder you should update "railway_links_table.xlsx" or "roadway_links_table.xlsx" with the links of the network to be evaluated, as they are in the example files located there.

From the dijkstra folder you could just run find_paths.py to find both roadway and railway shortest paths:

```cmd
python find_paths.py
```

You could pass parameters to find shortest paths of any other links table you may have, providing:

1. Name of excel from which links are to be taken
2. Name of gauges of the network separated by commas
3. Name of excel where calculated paths will be written

```cmd
python find_paths.py xl_input.xlsx gauge1,gauge2,gauge3 xl_output.xlsx
```

Also, from the main folder of the package, you could import find_paths module in python:

```python
from dijkstra import find_paths

xl_input = "xl_input.xlsx"
network_names = ["gauge1", "gauge2", "gauge3"]
xl_output = "xl_output.xlsx"

find_paths.main(xl_input, network_names, xl_output)
```

Or you could execute railway and roadway main methods without parameters:

```python
from dijkstra import find_paths

find_paths.main_railway()
find_paths.main_roadway()
```
