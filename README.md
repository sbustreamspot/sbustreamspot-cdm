# CDM to StreamSpot Translation

<img src="http://www3.cs.stonybrook.edu/~emanzoor/streamspot/img/streamspot-logo.jpg" height="150" align="right"/>

[http://www3.cs.stonybrook.edu/~emanzoor/streamspot/](http://www3.cs.stonybrook.edu/~emanzoor/streamspot/)

## Quickstart

### CDM-StreamSpot Translation

   * Clone: `git clone https://github.com/sbustreamspot/sbustreamspot-cdm.git`
   * Convert CDM/Avro to CDM/JSON
     (requires [avro-utils-1.8.1](http://www.apache.org/dyn/closer.cgi/avro/)):
     `java -jar avro-tools-1.8.1.jar tojson cdm/infoleak_small_units.avro`
   * Convert CDM/JSON to StreamSpot edges:
     `python translate_cdm_to_streamspot.py --url json/infoleak_small_units.json  --source file`
   * Convert CDM/Avro to StreamSpot edges: `TODO`
   * Run as a service consuming CDM/Avro from Kafka: `TODO`

The [translation mechanism](/TRANSLATION.md) proceeds according to carefully chosen
heuristics.

### StreamSpot Graph Visualisation

Visualising the graphs requires [graph-tool](https://graph-tool.skewed.de/download)
installed.

`python visualise_streamspot_graph.py -i streamspot/infoleak_small_units.ss`

## Contact

   * emanzoor@cs.stonybrook.edu
   * leman@cs.stonybrook.edu
