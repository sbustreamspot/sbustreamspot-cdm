# CDM to StreamSpot Translation

<img src="http://www3.cs.stonybrook.edu/~emanzoor/streamspot/img/streamspot-logo.jpg" height="150" align="right"/>

[http://www3.cs.stonybrook.edu/~emanzoor/streamspot/](http://www3.cs.stonybrook.edu/~emanzoor/streamspot/)

## Requirements

   * Access to `git.tc.bbn.com`, to install the TA3 API Python bindings.
   * [graph-tool](https://graph-tool.skewed.de/download) to visualise graphs
     (optional).
   * The usual Python dev-tools: `python2.7`, `virtualenv`, `pip`

## Quickstart

### Preliminaries

   * Clone: `git clone https://github.com/sbustreamspot/sbustreamspot-cdm.git`
   * Create environment:
     `virtualenv --python=python2.7 virtualenv --system-site-packages env`
   * Activate environment: `source env/bin/activate`
   * Install dependencies: `pip install -r requirements.txt`

If installing requirements fails on `tc-bbn-py`, try:
```
pip install git+https://git.tc.bbn.com/bbn/ta3-api-bindings-python.git
```

### CDM-StreamSpot Translation

   * Convert CDM/Avro to CDM/JSON for local testing:
     (requires [avro-utils-1.8.1](http://www.apache.org/dyn/closer.cgi/avro/)):
     `java -jar avro-tools-1.8.1.jar tojson avro/infoleak_small_units.CDM13.avro`

   * Convert CDM/JSON in a file to StreamSpot edges on standard output:
     `python translate_cdm_to_streamspot.py --url json/infoleak_small_units.CDM13.json --format json --source file`

   * Convert CDM/Avro in a file to StreamSpot edges on standard output:
     `python translate_cdm_to_streamspot.py --url avro/infoleak_small_units.CDM13.avro --format avro --source file`

   * Convert CDM/JSON from Kafka to StreamSpot edges on standard output:
     `python translate_cdm_to_streamspot.py --url <kafka-zookeeper-url>
      --format json --source kafka`

   * Convert CDM/Avro from Kafka to StreamSpot edges on standard output:
     `python translate_cdm_to_streamspot.py --url <kafka-zookeeper-url>
      --format avro --source kafka`

The [translation mechanism](/TRANSLATION.md) proceeds according to carefully chosen
heuristics.

### StreamSpot Graph Visualisation


`python visualise_streamspot_graph.py -i streamspot/infoleak_small_units.ss`

### Convert `.avdl` to `.avsc`

Avro parsing libraries require schemas in the `.avsc` format.
Conversion to `.avsc` can be done using `avro-tools` as follows:
```
wget http://apache.claz.org/avro/stable/java/avro-tools-1.8.1.jar
cd schema/
java -jar ../avro-tools-1.8.1.jar idl2schemata CDM13.avdl
cd ..
```

## Contact

   * emanzoor@cs.stonybrook.edu
   * leman@cs.stonybrook.edu
