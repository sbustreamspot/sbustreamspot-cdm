#!/usr/bin/env python

import argparse
from constants import *
import json
import logging.config
import pdb
from pykafka import KafkaClient
from pykafka.exceptions import OffsetOutOfRangeError, RequestTimedOut
from pykafka.partitioners import HashingPartitioner
import sys
from tc.schema.serialization import Utils
from tc.schema.serialization.kafka import KafkaAvroGenericSerializer, KafkaAvroGenericDeserializer

logging.config.fileConfig('conf/logging.conf')
logger = logging.getLogger("tc")

parser = argparse.ArgumentParser()
parser.add_argument('--kafka-group', help='Kafka consumer group', required=True) 
parser.add_argument('--only-produce', help='Only produce messages',
                     required=False, action='store_true')
parser.add_argument('--only-consume', help='Only produce messages',
                     required=False, action='store_true')
args = vars(parser.parse_args())

kafka_client = KafkaClient(KAFKA_URL)
kafka_topic = kafka_client.topics[args['kafka_group']]
producer = kafka_topic.get_producer(
            partitioner=HashingPartitioner(),
            sync=True, linger_ms=1, ack_timeout_ms=30000, max_retries=0)

schema = Utils.load_schema(SCHEMA_FILE)
input_file = open('avro/infoleak_small_units.CDM13.avro', 'rb')
serializer = KafkaAvroGenericSerializer(schema)
deserializer = KafkaAvroGenericDeserializer(schema, input_file=input_file)
records = deserializer.deserialize_from_file()

i = 0
produced = []
for edge in records:
    #kafka_key = str(i).encode() # this is hashed to select a partition
    kafka_key = '0'

    produced.append(edge)
    message = serializer.serialize(args['kafka_group'], edge)
    producer.produce(message, kafka_key)

    i += 1

print 'Pushed', i, 'messages'

producer.stop()
input_file.close()

if args['only_produce']:
    sys.exit(0)

consumer = kafka_topic.get_balanced_consumer(
            consumer_group=args['kafka_group'], auto_commit_enable=True,
            auto_commit_interval_ms=1000, reset_offset_on_start=False,
            consumer_timeout_ms=100, fetch_wait_max_ms=0, managed=True)

j = 0
consumed = []
while True:
    if j >= i:
        break
    try:
        for kafka_message in consumer:
            if kafka_message.value is not None:
                message = deserializer.deserialize(args['kafka_group'],
                                                   kafka_message.value)
                consumed.append(message)
                j += 1
    except RequestTimedOut:
        logger.warn('Kafka consumer request timed out')
    except OffsetOutOfRangeError:
        logger.warn('Kafka consumer offset out of range')
    

print 'Consumed', i, 'messages'

consumer.stop()

for i in range(len(produced)):
    assert consumed[i] == produced[i] 
