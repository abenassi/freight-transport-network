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


