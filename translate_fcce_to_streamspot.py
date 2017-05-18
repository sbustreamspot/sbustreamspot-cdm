#!/usr/bin/env python

import argparse
import json
import pdb
import sys
import time
import urllib2
from constants import *

parser = argparse.ArgumentParser()
parser.add_argument('--url', help='FCCE host:port', required=True)
parser.add_argument('--concise', help='Single-byte types, needed by StreamSpot',
                    required=False, action='store_true')
parser.add_argument('--graph', help='Graph to consume from',
                    required=True)
parser.add_argument('--start', help='Start training timestamp in microsecond epochs',
                    required=True)
parser.add_argument('--end', help='End training timestamp in microsecond epochs',
                    required=True)
args = vars(parser.parse_args())

url = args['url']
graph = args['graph']
start_ts = args['start']
end_ts = args['end']

t0 = time.time()
print >> sys.stderr, 'Getting all events',
try:
    endpoint = 'http://' + url + '/queryeventbytime/' + graph + '/' + start_ts + '/' + end_ts
    response = urllib2.urlopen(endpoint)
    response = response.read()
except:
    print 'Error connecting to endpoint:', endpoint
    sys.exit(1)

# Response is a list of edges with fields:
#    uuid, subject (uuid),
#    predicate (uuid), type (string), path (string), timeStampNano (long) 
events = json.loads(response)

print >> sys.stderr, len(events['events']), 'done in %.2fs.' % (time.time() - t0)

# Collect all subject and predicate uuids to get their types
all_subject_uuids = [e['subject'] for e in events['events'] if len(e) > 0]
all_predicate_uuids = [e['predicate'] for e in events['events'] if len(e) > 0]
all_uuids = all_subject_uuids + all_predicate_uuids

uuid_type_map = {}
uuid_gid_map = {}
current_graph_id = 0
start = 0
step = 500
end = start + step
t0 = time.time()
print >> sys.stderr, 'Getting all subject/predicate types', len(all_uuids)
while start < end:
    print >> sys.stderr, '\tRequest', start, end,
    t1 = time.time()
    try:
        uuid_string = ','.join(all_uuids[start:end])
        endpoint = 'http://' + url + '/queryelembyuuid/' + graph + '/' + uuid_string
        response = urllib2.urlopen(endpoint)
        response = response.read()
    except:
        print >> sys.stderr, 'Error connecting to endpoint:', endpoint[:100]
        sys.exit(-1)
    print >> sys.stderr, 'done in %.2fs.' % (time.time() - t1)

    #print '\tMapping ids...'
    # Response is a list of entities with fields: subtype, permissions, _directory, path, _filename, type, uuid
    entities = json.loads(response)
    for entity in entities['entities']:
        uuid = entity['uuid']
        main_type = entity['type']
        if main_type == CDM_TYPE_SUBJECT: 
            uuid_type_map[uuid] = entity['subtype']
            uuid_gid_map[uuid] = current_graph_id
            current_graph_id += 1
        elif main_type == CDM_TYPE_FILE:
            uuid_type_map[uuid] = entity['subtype']
        else:
            uuid_type_map[uuid] = main_type

    start = end
    end = min(len(all_uuids), start + step)
print >> sys.stderr, 'done in %.2fs.' % (time.time() - t0)

for eidx, event in enumerate(events['events']):
    #if 'path' in event:
    #    print event_type
    event_uuid = event['uuid']
    subject_uuid = event['subject']
    predicate_uuid = event['predicate']
    event_type = event['type']
    event_ts = event['timeStampNano']

    if predicate_uuid == '': # eg. fork, fcntl
        predicate_uuid = subject_uuid

    # This event type may have predicates that have not been seen before
    if event_type == 'EVENT_OTHER':
        continue

    if subject_uuid == predicate_uuid: # self loop
        continue

    subject_type = uuid_type_map[subject_uuid]
    predicate_type = uuid_type_map[predicate_uuid]
    gid = uuid_gid_map[subject_uuid]

    if event_type == 'EVENT_CLONE' or event_type == 'EVENT_FORK':
        uuid_gid_map[predicate_uuid] = gid # propogate gid
    if event_type == 'EVENT_EXECUTE':
        uuid_gid_map[subject_uuid] = current_graph_id # new graph
        current_graph_id += 1

    mapped_event_type = type_map[event_type]
    mapped_subject_type = type_map[subject_type]
    mapped_predicate_type = type_map[predicate_type]

    print subject_uuid, mapped_subject_type,
    print predicate_uuid, mapped_predicate_type,
    print mapped_event_type, gid
