#!/usr/bin/env python

import argparse
import json
import pdb
from pykafka import KafkaClient
from pykafka.exceptions import OffsetOutOfRangeError, RequestTimedOut
from pykafka.partitioners import HashingPartitioner
import sys
from tc.schema.serialization import Utils
from tc.schema.records.parsing import CDMParser
from tc.schema.serialization.kafka import KafkaAvroGenericDeserializer
from constants import *

parser = argparse.ArgumentParser()
parser.add_argument('--url', help='Input filename or Kafka URL', required=True)
parser.add_argument('--format', help='Consume Avro or JSON serialised CDM',
                    choices=['avro', 'json'], required=True)
parser.add_argument('--source', help='Consume from Kafka or a file',
                    choices=['kafka', 'file'], required=True)
parser.add_argument('--concise', help='Single-byte types, needed by StreamSpot',
                    required=False, action='store_true')
parser.add_argument('--kafka-topic', help='Kafka topic to consume from',
                    required=False)
parser.add_argument('--kafka-group', help='Kafka consumer group', required=False)
args = vars(parser.parse_args())

input_url = args['url']
input_source = args['source']
input_format = args['format']

pid_to_graph_id = {}

def print_streamspot_edge(streamspot_edge, concise):
    # HACK: Don't print self-loop edges
    if concise and streamspot_edge['source_id'] == streamspot_edge['dest_id']:
        return
    if not concise:
        print str(streamspot_edge['source_id']) + '\t' +\
              str(streamspot_edge['source_name']) + '\t' +\
              str(streamspot_edge['source_type']) + '\t' +\
              str(streamspot_edge['dest_id']) + '\t' +\
              str(streamspot_edge['dest_name']) + '\t' +\
              str(streamspot_edge['dest_type']) + '\t' +\
              str(streamspot_edge['edge_type']) + '\t' +\
              str(streamspot_edge['graph_id'])
    else:
        print str(streamspot_edge['source_id']) + '\t' +\
              type_map[streamspot_edge['source_type']] + '\t' +\
              str(streamspot_edge['dest_id']) + '\t' +\
              type_map[streamspot_edge['dest_type']] + '\t' +\
              type_map[streamspot_edge['edge_type']] + '\t' +\
              str(streamspot_edge['graph_id'])

def read_field(object, format):
    if format == 'avro':
        return str(object)
    elif format == 'json':
        if type(object) is int:
            return object
        return object.encode('utf-8')
    else:
        print 'Unknown format:', format
        sys.exit(-1)

# initialise empty streamspot edge
event_metadata_buffer = {} # filled/cleared on every new event
streamspot_edge = {'event_uuid': None,
                   'source_id': None,
                   'source_name': None,
                   'source_type': None,
                   'dest_id': None,
                   'dest_name': 'NA',
                   'dest_type': None,
                   'edge_type': None,
                   'graph_id': None
                  } # filled/cleared on every new event

# setup input source and format
if input_source == 'kafka':
    if not input_format == 'avro':
        print 'Input format must be Avro for Kafka source'
        sys.exit(-1)
    if args['kafka_topic'] is None:
        print 'Argument --kafka-topic is required'
        sys.exit(-1)
    if args['kafka_group'] is None:
        print 'Argument --kafka-group is required'
        sys.exit(-1)

    kafka_client = KafkaClient(input_url)
    kafka_topic = kafka_client.topics[args['kafka_topic']]
    consumer = kafka_topic.get_balanced_consumer(
                consumer_group=args['kafka_group'], auto_commit_enable=True,
                auto_commit_interval_ms=1000, reset_offset_on_start=False,
                consumer_timeout_ms=100, fetch_wait_max_ms=0, managed=True)
    
    schema = Utils.load_schema(SCHEMA_FILE)
    deserializer = KafkaAvroGenericDeserializer(schema, schema)
    parser = CDMParser(schema)
    
    f = consumer
elif input_source == 'file':
    if input_format == 'avro':
        ifile = open(input_url, 'rb')
        schema = Utils.load_schema(SCHEMA_FILE)
        deserializer = KafkaAvroGenericDeserializer(schema, input_file=ifile)
        parser = CDMParser(schema)
        f = deserializer.deserialize_from_file()
    elif input_format == 'json':
        f = open(input_url, 'r')

# process records
lineno = 0
while True:
    try:
        for line in f:
            if input_format == 'json':
                cdm_record = json.loads(line.strip())
                cdm_record_type = cdm_record['datum'].keys()[0]
                cdm_record_values = cdm_record['datum'][cdm_record_type]
            elif input_format == 'avro':
                if input_source == 'kafka':
                    if line.value is None:
                        continue
                    cdm_record = deserializer.deserialize(args['kafka_topic'],
                                                          line.value)
                elif input_source == 'file':
                    cdm_record = line

                cdm_record_type = 'com.bbn.tc.schema.avro.' +\
                                   parser.get_record_type(cdm_record)
                cdm_record_values = cdm_record['datum']

            lineno += 1
            #print lineno, cdm_record_type, cdm_record

            if cdm_record_type == CDM_TYPE_PRINCIPAL:
                continue # we don't care about PRINCIPALs

            elif cdm_record_type == CDM_TYPE_SRCSINK:
                # treat this like a file with filename UUID
                srcsink_uuid = read_field(cdm_record_values['uuid'], input_format)

            elif cdm_record_type == CDM_TYPE_SUBJECT:
                proc_uuid = read_field(cdm_record_values['uuid'], input_format)
                subject_type = read_field(cdm_record_values['type'], input_format)
                if subject_type == 'SUBJECT_PROCESS':
                    pid = read_field(cdm_record_values['pid'], input_format)
                    ppid = read_field(cdm_record_values['ppid'], input_format)

                    if input_format == 'avro':
                        pname = read_field(cdm_record_values['properties']['name'],
                                          input_format)
                        unitid = read_field(cdm_record_values['unitId'], input_format)
                    elif input_format == 'json':
                        pname = read_field(cdm_record_values['properties']['map']['name'],
                                          input_format)
                        unitid = read_field(cdm_record_values['unitId']['int'],
                                           input_format)

                    if not proc_uuid in pid_to_graph_id:
                        pid_to_graph_id[proc_uuid] = proc_uuid
                else:
                    print "Unknown subject type:", subject_type
                    sys.exit(-1)

            elif cdm_record_type == CDM_TYPE_FILE:
                file_uuid = read_field(cdm_record_values['uuid'], input_format)
                url = read_field(cdm_record_values['url'], input_format)

            elif cdm_record_type == CDM_TYPE_SOCK:
                sock_uuid = read_field(cdm_record_values['uuid'], input_format)

                src = read_field(cdm_record_values['srcAddress'], input_format)
                dest = read_field(cdm_record_values['destAddress'], input_format)
                src_port = read_field(cdm_record_values['srcPort'], input_format)
                dest_port = read_field(cdm_record_values['destPort'], input_format)
                sock_id = src + ':' + str(src_port) + ':' + dest + ':' + str(dest_port)

            elif cdm_record_type == CDM_TYPE_MEM:
                mem_uuid = read_field(cdm_record_values['uuid'], input_format)
                addr = read_field(cdm_record_values['memoryAddress'], input_format)

            elif cdm_record_type == CDM_TYPE_EVENT:
                # print previous streamspot edge if it is ready
                if not None in streamspot_edge.values():
                    print_streamspot_edge(streamspot_edge, args['concise'])

                    # clear old edge data
                    streamspot_edge = {'event_uuid': None,
                                       'source_id': None,
                                       'source_name': None,
                                       'source_type': None,
                                       'dest_id': None,
                                       'dest_name': 'NA',
                                       'dest_type': None,
                                       'edge_type': None,
                                       'graph_id': None
                                      }

                event_uuid = read_field(cdm_record_values['uuid'], input_format)
                event_type = read_field(cdm_record_values['type'], input_format)
                streamspot_edge['edge_type'] = event_type
                streamspot_edge['event_uuid'] = event_uuid        # to map metadata

            elif cdm_record_type == CDM_TYPE_EDGE:
                edge_type = read_field(cdm_record_values['type'], input_format)
                if edge_type == 'EDGE_SUBJECT_HASLOCALPRINCIPAL':
                    pass
                elif edge_type == 'EDGE_OBJECT_PREV_VERSION':
                    pass
                elif edge_type == 'EDGE_FILE_AFFECTS_EVENT':
                    # HACK! FIXME
                    # Special case for
                    #   - EVENT_UPDATE
                    #   - EVENT_RENAME
                    if streamspot_edge['edge_type'] == 'EVENT_UPDATE' or \
                       streamspot_edge['edge_type'] == 'EVENT_RENAME':

                        # to_uuid is of the event
                        assert read_field(cdm_record_values['toUuid'],
                                         input_format) == \
                                streamspot_edge['event_uuid']

                        # from_uuid is of the file
                        from_uuid = read_field(cdm_record_values['fromUuid'],
                                              input_format)

                        streamspot_edge['dest_id'] = from_uuid
                        streamspot_edge['dest_name'] = url
                        streamspot_edge['dest_type'] = 'OBJECT_FILE'
                    else:

                        # from_uuid is of the event
                        assert read_field(cdm_record_values['fromUuid'],
                                         input_format) == \
                                streamspot_edge['event_uuid']

                        # to_uuid is of the file
                        to_uuid = read_field(cdm_record_values['toUuid'],
                                            input_format)

                        streamspot_edge['dest_id'] = to_uuid
                        streamspot_edge['dest_name'] = url
                        streamspot_edge['dest_type'] = 'OBJECT_FILE'
                elif edge_type == 'EDGE_EVENT_AFFECTS_FILE':

                    # from_uuid is of the event
                    assert read_field(cdm_record_values['fromUuid'],
                                     input_format) ==\
                           streamspot_edge['event_uuid']

                    # to_uuid is of the file
                    to_uuid = read_field(cdm_record_values['toUuid'], input_format)

                    streamspot_edge['dest_id'] = to_uuid
                    streamspot_edge['dest_name'] = url
                    streamspot_edge['dest_type'] = 'OBJECT_FILE'
                elif edge_type == 'EDGE_MEMORY_AFFECTS_EVENT' or \
                        edge_type == 'EDGE_EVENT_AFFECTS_MEMORY':

                    # from_uuid is of the event
                    assert read_field(cdm_record_values['fromUuid'],
                                     input_format) ==\
                           streamspot_edge['event_uuid']

                    # to_uuid is of the memory location
                    to_uuid = read_field(cdm_record_values['toUuid'], input_format)
                    streamspot_edge['dest_id'] = to_uuid
                    streamspot_edge['dest_name'] = addr
                    streamspot_edge['dest_type'] = 'OBJECT_MEM'
                elif edge_type == 'EDGE_EVENT_AFFECTS_NETFLOW' or \
                        edge_type == 'EDGE_NETFLOW_AFFECTS_EVENT':

                    # from_uuid is of the event
                    assert read_field(cdm_record_values['fromUuid'],
                                    input_format) ==\
                           streamspot_edge['event_uuid']

                    # to_uuid is of the socket
                    to_uuid = read_field(cdm_record_values['toUuid'], input_format)
                    streamspot_edge['dest_id'] = to_uuid
                    streamspot_edge['dest_name'] = sock_id
                    streamspot_edge['dest_type'] = 'OBJECT_SOCK'
                elif edge_type == 'EDGE_EVENT_AFFECTS_SRCSINK' or \
                        edge_type == 'EDGE_SRCSINK_AFFECTS_EVENT':

                    # from_uuid is of the event
                    assert read_field(cdm_record_values['fromUuid'],
                                    input_format) ==\
                           streamspot_edge['event_uuid']

                    # to_uuid is of the source-sink
                    to_uuid = read_field(cdm_record_values['toUuid'], input_format)
                    streamspot_edge['dest_id'] = to_uuid
                    streamspot_edge['dest_name'] = to_uuid
                    streamspot_edge['dest_type'] = 'OBJECT_SRCSINK'
                elif edge_type == 'EDGE_EVENT_AFFECTS_SUBJECT' or \
                        edge_type == 'EDGE_EVENT_ISGENERATEDBY_SUBJECT':

                    # from_uuid is of the event
                    assert read_field(cdm_record_values['fromUuid'],
                                     input_format) ==\
                           streamspot_edge['event_uuid']

                    # to_uuid is of the subject
                    to_uuid = read_field(cdm_record_values['toUuid'], input_format)

                    if edge_type == 'EDGE_EVENT_AFFECTS_SUBJECT':
                        streamspot_edge['dest_id'] = to_uuid
                        streamspot_edge['dest_name'] = 'NA'
                        streamspot_edge['dest_type'] = 'SUBJECT_PROCESS'
                    elif edge_type == 'EDGE_EVENT_ISGENERATEDBY_SUBJECT':
                        streamspot_edge['source_id'] = to_uuid
                        streamspot_edge['source_name'] = 'NA'
                        streamspot_edge['source_type'] = 'SUBJECT_PROCESS'

                    # graph ID assignment to streamspot edge
                    if edge_type == 'EDGE_EVENT_ISGENERATEDBY_SUBJECT':
                        streamspot_edge['graph_id'] = \
                                pid_to_graph_id[streamspot_edge['source_id']]

                        # handle graph ID propagate on FORK/CLONE and UNIT
                        if streamspot_edge['edge_type'] == 'EVENT_FORK' or \
                           streamspot_edge['edge_type'] == 'EVENT_CLONE' or \
                           streamspot_edge['edge_type'] == 'EVENT_UNIT':
                            pid_to_graph_id[streamspot_edge['dest_id']] = \
                                    pid_to_graph_id[streamspot_edge['source_id']]

                        # handle graph ID change on EXECUTE
                        elif streamspot_edge['edge_type'] == 'EVENT_EXECUTE':
                            pass # just don't propagate the graph id

                else:
                    print 'Unknown edge type:', edge_type
                    print cdm_record
                    sys.exit(-1)

            else:
                print 'Unknown CDM record type', cdm_record_type
                sys.exit(-1)
        # for line in f

        # last event in buffer
        if not None in streamspot_edge.values():
            print_streamspot_edge(streamspot_edge, args['concise'])
            streamspot_edge = {'event_uuid': None,
                               'source_id': None,
                               'source_name': None,
                               'source_type': None,
                               'dest_id': None,
                               'dest_name': 'NA',
                               'dest_type': None,
                               'edge_type': None,
                               'graph_id': None
                              }

    except RequestTimedOut:
        continue # continue waiting 
    except OffsetOutOfRangeError:
        continue # ignore error
    # try

    sys.stdout.flush()

    if input_source == "file":
        break
# while True
