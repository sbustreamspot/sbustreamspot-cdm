# CDM to StreamSpot Translation

<img src="http://www3.cs.stonybrook.edu/~emanzoor/streamspot/img/streamspot-logo.jpg" height="150" align="right"/>

[http://www3.cs.stonybrook.edu/~emanzoor/streamspot/](http://www3.cs.stonybrook.edu/~emanzoor/streamspot/)

## Requirements

   * Access to `git.tc.bbn.com`, to install the TA3 API Python bindings.
   * [graph-tool](https://graph-tool.skewed.de/download) to visualise graphs
     (optional).
   * `tc-in-a-box` to read/write from Kafka.
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

   * Convert CDM/Avro from Kafka to StreamSpot edges on standard output:
     `python translate_cdm_to_streamspot.py --url <kafka-zookeeper-url>
      --format avro --source kafka --kafka-topic topic --kafka-group group`

   * Visualise Streamspot graphs:
     `python visualise_streamspot_graph.py -i streamspot/infoleak_small_units.ss`

The [translation mechanism](/TRANSLATION.md) proceeds according to carefully chosen
heuristics.

## Convert `.avdl` to `.avsc`

Avro parsing libraries require schemas in the `.avsc` format.
Conversion to `.avsc` can be done using `avro-tools` as follows:
```
wget http://apache.claz.org/avro/stable/java/avro-tools-1.8.1.jar
cd schema/
java -jar ../avro-tools-1.8.1.jar idl2schemata CDM13.avdl
cd ..
```

## Setup tc-in-a-box

```
git clone git@git.tc.bbn.com:bbn/tc-in-a-box.git
cd tc-in-a-box
./pre-vagrant.sh
vagrant up ta3
```

Test StreamSpot's producer/consumer:
`python test_kafka_vm.py --kafka-group $(date +'%s')`

Test StreamSpot's CDM translator:
```
python translate_cdm_to_streamspot.py --url ta3.tc.dev:9092 --format avro --source kafka --kafka-topic test --kafka-group test
python test_kafka_vm.py --kafka-group test --only-produce
```

## Contact

   * emanzoor@cs.stonybrook.edu
   * leman@cs.stonybrook.edu
