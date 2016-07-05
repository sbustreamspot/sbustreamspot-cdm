#!/usr/bin/env python

import argparse
import json
import pdb
import sys
from constants import *

parser = argparse.ArgumentParser()
parser.add_argument('--url', help='Input filename or Kafka URL', required=True)
parser.add_argument('--source', help='CDM/Avro from Kafka or CDM/JSON from a file',
                    choices=['kafka', 'file'], required=True)
parser.add_argument('--concise', help='Single-byte types, needed by StreamSpot',
                    required=False, action='store_true')
args = vars(parser.parse_args())

input_url = args['url']
input_source = args['source']

uuid_to_pid = {}
uuid_to_pname = {}
uuid_to_url = {}
uuid_to_sockid = {}
uuid_to_addr = {}

pid_to_graph_id = {}
current_graph_id = 0

with open(input_url, 'r') as f:
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
    lineno = 0 
    for line in f:
        line = line.strip()
        lineno += 1
        cdm_record = json.loads(line)
        cdm_record_type = cdm_record['datum'].keys()[0]
        cdm_record_values = cdm_record['datum'][cdm_record_type]

        #print cdm_record

        if cdm_record_type == CDM_TYPE_PRINCIPAL:
            continue # we don't care about principals

        elif cdm_record_type == CDM_TYPE_SUBJECT:
            uuid = cdm_record_values['uuid']
            type = cdm_record_values['type']
            if type == 'SUBJECT_PROCESS':
                pid = cdm_record_values['pid']          # source ID
                ppid = cdm_record_values['ppid']        # needed to assign graph ID
                pname = cdm_record_values['properties']['map']['programName']
                unitid = cdm_record_values['unitId']['int']
                #uuid_to_pid[uuid] = str(pid) + '/' + pname + '/' + str(unitid)
                uuid_to_pid[uuid] = pid
                uuid_to_pname[uuid] = pname 
                if not pid in pid_to_graph_id: # pid has no gid assigned
                    if not ppid in pid_to_graph_id: # ppid has no gid assigned
                        pid_to_graph_id[pid] = current_graph_id
                        pid_to_graph_id[ppid] = current_graph_id
                        current_graph_id += 1
                    else: # parent has a gid assigned
                        pid_to_graph_id[pid] = pid_to_graph_id[ppid]
            else:
                print "Unknown subject type:", type
                sys.exit(-1)

        elif cdm_record_type == CDM_TYPE_FILE:
            uuid = cdm_record_values['uuid']
            url = cdm_record_values['url']              # destination ID
            uuid_to_url[uuid] = url

        elif cdm_record_type == CDM_TYPE_SOCK:
            uuid = cdm_record_values['uuid']
            
            src = cdm_record_values['srcAddress']
            dest = cdm_record_values['destAddress']
            src_port = cdm_record_values['srcPort']
            dest_port =  cdm_record_values['destPort']
            sock_id = src + ':' + str(src_port) + ':' + dest + ':' + str(dest_port)

            uuid_to_sockid[uuid] = sock_id

        elif cdm_record_type == CDM_TYPE_MEM:
            uuid = cdm_record_values['uuid']
            addr = cdm_record_values['memoryAddress']
            uuid_to_addr[uuid] = addr

        elif cdm_record_type == CDM_TYPE_EVENT:
            # print previous streamspot edge if it is ready
            if not None in streamspot_edge.values():
                print str(streamspot_edge['source_id']) + '\t' +\
                      str(streamspot_edge['source_name']) + '\t' +\
                      str(streamspot_edge['source_type']) + '\t' +\
                      str(streamspot_edge['dest_id']) + '\t' +\
                      str(streamspot_edge['dest_name']) + '\t' +\
                      str(streamspot_edge['dest_type']) + '\t' +\
                      str(streamspot_edge['edge_type']) + '\t' +\
                      str(streamspot_edge['graph_id'])

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

            uuid = cdm_record_values['uuid']
            type = cdm_record_values['type']
            streamspot_edge['edge_type'] = type         # streamspot edge type 
            streamspot_edge['event_uuid'] = uuid        # to map metadata

        elif cdm_record_type == CDM_TYPE_EDGE:
            type = cdm_record_values['type']
            if type == 'EDGE_SUBJECT_HASLOCALPRINCIPAL':
                pass
            elif type == 'EDGE_FILE_AFFECTS_EVENT':
                # HACK! FIXME
                # Special case for
                #   - EVENT_UPDATE
                #   - EVENT_RENAME
                if streamspot_edge['edge_type'] == 'EVENT_UPDATE' or \
                   streamspot_edge['edge_type'] == 'EVENT_RENAME':
                    assert cdm_record_values['toUuid'] == \
                            streamspot_edge['event_uuid']
                    from_uuid = cdm_record_values['fromUuid']
                    url = uuid_to_url[from_uuid]
                    streamspot_edge['dest_id'] = url
                    streamspot_edge['dest_type'] = 'OBJECT_FILE'
                else:
                    assert cdm_record_values['fromUuid'] == \
                            streamspot_edge['event_uuid']
                    to_uuid = cdm_record_values['toUuid']
                    url = uuid_to_url[to_uuid]
                    streamspot_edge['dest_id'] = url
                    streamspot_edge['dest_type'] = 'OBJECT_FILE'
            elif type == 'EDGE_EVENT_AFFECTS_FILE':
                assert cdm_record_values['fromUuid'] == streamspot_edge['event_uuid']

                to_uuid = cdm_record_values['toUuid']
                url = uuid_to_url[to_uuid]
                streamspot_edge['dest_id'] = url
                streamspot_edge['dest_type'] = 'OBJECT_FILE'
            elif type == 'EDGE_MEMORY_AFFECTS_EVENT':
                assert cdm_record_values['fromUuid'] == streamspot_edge['event_uuid']

                to_uuid = cdm_record_values['toUuid']
                addr = uuid_to_addr[to_uuid]
                streamspot_edge['dest_id'] = addr
                streamspot_edge['dest_type'] = 'OBJECT_MEM'
            elif type == 'EDGE_EVENT_AFFECTS_MEMORY':
                assert cdm_record_values['fromUuid'] == streamspot_edge['event_uuid']

                to_uuid = cdm_record_values['toUuid']
                addr = uuid_to_addr[to_uuid]
                streamspot_edge['dest_id'] = addr
                streamspot_edge['dest_type'] = 'OBJECT_MEM'
            elif type == 'EDGE_EVENT_AFFECTS_NETFLOW':
                assert cdm_record_values['fromUuid'] == streamspot_edge['event_uuid']

                to_uuid = cdm_record_values['toUuid']
                sock_id = uuid_to_sockid[to_uuid]
                streamspot_edge['dest_id'] = sock_id
                streamspot_edge['dest_type'] = 'OBJECT_SOCK'
            elif type == 'EDGE_EVENT_AFFECTS_SUBJECT' or \
                    type == 'EDGE_EVENT_ISGENERATEDBY_SUBJECT':
                assert cdm_record_values['fromUuid'] == streamspot_edge['event_uuid']

                to_uuid = cdm_record_values['toUuid']
                pid = uuid_to_pid[to_uuid]
                pname = uuid_to_pname[to_uuid]

                if type == 'EDGE_EVENT_AFFECTS_SUBJECT':
                    streamspot_edge['dest_id'] = pid 
                    streamspot_edge['dest_name'] = pname
                    streamspot_edge['dest_type'] = 'SUBJECT_PROCESS'
                elif type == 'EDGE_EVENT_ISGENERATEDBY_SUBJECT':
                    streamspot_edge['source_id'] = pid
                    streamspot_edge['source_name'] = pname
                    streamspot_edge['source_type'] = 'SUBJECT_PROCESS'

                # graph ID assignment to streamspot edge
                if type == 'EDGE_EVENT_ISGENERATEDBY_SUBJECT':
                    streamspot_edge['graph_id'] = \
                            pid_to_graph_id[streamspot_edge['source_id']]
                    
                    # handle graph ID change on EXECUTE
                    if streamspot_edge['edge_type'] == 'EVENT_EXECUTE':
                        pid_to_graph_id[streamspot_edge['source_id']] = \
                                current_graph_id # change graph ID of caller process
                        current_graph_id += 1
                
            else:
                print 'Unknown edge type:', type
                sys.exit(-1)
        
        else:
            print 'Unknown CDM record type', cdm_record_type
            sys.exit(-1)

    
    # last event in buffer
    print str(streamspot_edge['source_id']) + '\t' +\
          str(streamspot_edge['source_name']) + '\t' +\
          str(streamspot_edge['source_type']) + '\t' +\
          str(streamspot_edge['dest_id']) + '\t' +\
          str(streamspot_edge['dest_name']) + '\t' +\
          str(streamspot_edge['dest_type']) + '\t' +\
          str(streamspot_edge['edge_type']) + '\t' +\
          str(streamspot_edge['graph_id'])
