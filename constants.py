#!/usr/bin/env python

# Based on CDM 13
# Schema: https://git.tc.bbn.com/bbn/ta3-serialization-schema/blob/master/avro/CDM13.avdl
SCHEMA_FILE = 'schema/TCCDMDatum.avsc'

# CDM record type constants
CDM_TYPE_PRINCIPAL = 'com.bbn.tc.schema.avro.Principal'
CDM_TYPE_SUBJECT = 'com.bbn.tc.schema.avro.Subject'
CDM_TYPE_FILE = 'com.bbn.tc.schema.avro.FileObject'
CDM_TYPE_MEM = 'com.bbn.tc.schema.avro.MemoryObject'
CDM_TYPE_SOCK = 'com.bbn.tc.schema.avro.NetFlowObject'
CDM_TYPE_EDGE = 'com.bbn.tc.schema.avro.SimpleEdge'
CDM_TYPE_EVENT = 'com.bbn.tc.schema.avro.Event'
CDM_TYPE_SRCSINK = 'com.bbn.tc.schema.avro.SrcSinkObject'

type_map = {
    # SubjectType
    'SUBJECT_PROCESS': 'a',
    #'SUBJECT_THREAD': 'b',
    #'SUBJECT_UNIT': 'c',
    #'SUBJECT_BASIC_BLOCK': 'd'

    # Object Type
    'OBJECT_FILE': 'e',
    'OBJECT_MEM': 'f',
    'OBJECT_SOCK': 'g',
    'OBJECT_SRCSINK': 'O', # Added CDM13

    # EventType
    'EVENT_ACCEPT': 'h',
    'EVENT_BIND': 'i',
    'EVENT_CHANGE_PRINCIPAL': 'j',
    'EVENT_CHECK_FILE_ATTRIBUTES': 'k',
    'EVENT_CLONE': 'l',
    'EVENT_CLOSE': 'm',
    'EVENT_CONNECT': 'n',
    'EVENT_CREATE_OBJECT': 'o',
    'EVENT_CREATE_THREAD': 'p',
    'EVENT_EXECUTE': 'q',
    'EVENT_FORK': 'r',
    'EVENT_LINK': 's',
    'EVENT_UNLINK': 't',
    'EVENT_MMAP': 'u',
    'EVENT_MODIFY_FILE_ATTRIBUTES': 'v',
    'EVENT_MPROTECT': 'w',
    'EVENT_OPEN': 'x',
    'EVENT_READ': 'y',
    'EVENT_RECVFROM': 'z',
    'EVENT_RECVMSG': 'A',
    'EVENT_RENAME': 'B',
    'EVENT_WRITE': 'C',
    'EVENT_SIGNAL': 'D',
    'EVENT_TRUNCATE': 'E',
    'EVENT_WAIT': 'F',
    'EVENT_OS_UNKNOWN': 'G',
    'EVENT_KERNEL_UNKNOWN': 'H',
    'EVENT_APP_UNKNOWN': 'I',
    'EVENT_UI_UNKNOWN': 'J',
    'EVENT_UNKNOWN': 'K',
    'EVENT_BLIND': 'L',
    'EVENT_UNIT': 'M',
    'EVENT_UPDATE': 'N',
}
