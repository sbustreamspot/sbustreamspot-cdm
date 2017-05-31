#!/usr/bin/env python

import argparse
import json
import traceback
import pdb
import sys
import time
import urllib2
import uuid
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
parser.add_argument('--train-edges', help='Training edges',
                    required=False)
args = vars(parser.parse_args())

url = args['url']
graph = args['graph']
start_ts = args['start']
end_ts = args['end']

t0 = time.time()
print >> sys.stderr, 'Getting all events'
start = int(start_ts)
step = int(86400) # 3 hours
end = min(start + step, int(end_ts))
all_events = []
while start < end:
    t1 = time.time()
    print >> sys.stderr, '\t', start, end, 
    try:
        endpoint = 'http://' + url + '/queryeventbytime/' + graph + '/' + str(int(start)) + '/' + str(int(end))
        response = urllib2.urlopen(endpoint)
        response = response.read()
    except:
        print >> sys.stderr, 'Error connecting to endpoint:', endpoint
        sys.exit()
    print >> sys.stderr, 'done in %.2fs.' % (time.time() - t1)
    
    # Response is a list of edges with fields:
    #    uuid, subject (uuid),
    #    predicate (uuid), type (string), path (string), timestampNanos (long) 
    events = json.loads(response)
    events = events['events']

    print >> sys.stderr, '\tHandling events without timestamps...'
    events_without_timestamps = []
    for e in events:
        if not e['timeStampNano'].isdigit():
            events_without_timestamps.append(e['uuid'])
    try:
        uuid_string = ','.join(events_without_timestamps)
        endpoint = 'http://' + url + '/queryelembyuuid/' + graph + '/' + uuid_string
        response = urllib2.urlopen(endpoint)
        response = response.read()
    except:
        print >> sys.stderr, 'Error connecting to endpoint:', endpoint
        sys.exit()
    e_ts = {}
    for e in json.loads(response)['events']:
        e_ts[e['uuid']] = e['timestampNanos']
    for e in events:
        euuid = e['uuid']
        if euuid in e_ts:
            e['timeStampNano'] = e_ts[euuid]

    events = [e for e in events
              if int(e['timeStampNano']) >= start * 10**9 and
                 int(e['timeStampNano']) < end * 10**9]
    all_events.extend(events)
    
    start = end + 1
    end = min(start + step, int(end_ts))
print >> sys.stderr, len(all_events), 'events done in %.2fs.' % (time.time() - t0)

if len(all_events) == 0:
    print >> sys.stderr, 'No events'
    sys.exit()

# Collect all subject and predicate uuids to get their types
all_subject_uuids = [e['subject'] for e in all_events if len(e) > 0]
all_predicate_uuids = [e['predicate'] for e in all_events if len(e) > 0]
all_uuids = all_subject_uuids + all_predicate_uuids

uuid_type_map = {}
uuid_mapped_type_map = {}
uuid_gid_map = {}
t0 = time.time()
if args['train_edges'] is not None:
    train_edges = args['train_edges']
    print >> sys.stderr, 'Reading training edges',
    with open(train_edges, 'r') as f:
        for line in f:
            line = line.strip()
            fields = line.split(' ')
            subject_uuid = fields[0]
            subject_type = fields[1]
            predicate_uuid = fields[2]
            predicate_type = fields[3]
            gid = fields[-1]
            uuid_gid_map[subject_uuid] = gid
            uuid_mapped_type_map[subject_uuid] = subject_type
            uuid_mapped_type_map[predicate_uuid] = predicate_type
print >> sys.stderr, 'done in %.2fs.' % (time.time() - t0)

all_uuids = set(all_uuids) - set(uuid_mapped_type_map.keys())
all_uuids = list(all_uuids)

start = 0
step = 500
end = min(start + step, len(all_uuids))
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
        euuid = entity['uuid']
        main_type = entity['type']
        if main_type == CDM_TYPE_SUBJECT: 
            uuid_type_map[euuid] = entity['subtype']
            if not euuid in uuid_gid_map:
                uuid_gid_map[euuid] = euuid
        elif main_type == CDM_TYPE_FILE:
            uuid_type_map[euuid] = entity['subtype']
        else:
            uuid_type_map[euuid] = main_type

    start = end
    end = min(len(all_uuids), start + step)
print >> sys.stderr, 'done in %.2fs.' % (time.time() - t0)

print >> sys.stderr, 'Writing StreamSpot edges...'
for eidx, event in enumerate(sorted(all_events,
                                    key=lambda e: int(e['timeStampNano']))):
    #if 'path' in event:
    #    print event_type
    try:
        event_uuid = event['uuid']
        subject_uuid = event['subject']
        predicate_uuid = event['predicate']
        event_type = event['type']
        event_ts = event['timeStampNano']

        if predicate_uuid == '':
            continue
        if event_type == 'EVENT_OTHER':
            continue
        if subject_uuid == predicate_uuid: # self loop
            continue

        #print event_type

        if subject_uuid in uuid_mapped_type_map:
            mapped_subject_type = uuid_mapped_type_map[subject_uuid] 
        else:
            subject_type = uuid_type_map[subject_uuid]
            mapped_subject_type = type_map[subject_type]

        if predicate_uuid in uuid_mapped_type_map:
            mapped_predicate_type = uuid_mapped_type_map[predicate_uuid]
        else:
            predicate_type = uuid_type_map[predicate_uuid]
            mapped_predicate_type = type_map[predicate_type]
        
        mapped_event_type = type_map[event_type]
        gid = uuid_gid_map[subject_uuid]
        
        if event_type == 'EVENT_CLONE' or event_type == 'EVENT_FORK':
            uuid_gid_map[predicate_uuid] = gid # propogate gid
        if event_type == 'EVENT_EXECUTE':
            new_uuid = uuid.uuid1().hex # new graph
            uuid_gid_map[subject_uuid] = new_uuid

        print subject_uuid, mapped_subject_type,
        print predicate_uuid, mapped_predicate_type,
        print mapped_event_type, gid, event_uuid, event_ts
    except Exception, e:
        print >> sys.stderr, 'Error writing edges.'
        print >> sys.stderr, event
        print >> sys.stderr, traceback.format_exc()
        sys.exit(-1)
