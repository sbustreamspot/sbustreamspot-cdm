#!/usr/bin/env python

# Kafka stuff
KAFKA_URL = 'ta3.tc.dev:9092'

# Based on CDM 13
# Schema: https://git.tc.bbn.com/bbn/ta3-serialization-schema/blob/master/avro/CDM13.avdl
SCHEMA_FILE = 'schema/TCCDMDatum.avsc'

# CDM record type constants
CDM_TYPE_PRINCIPAL = 'Principal'
CDM_TYPE_SUBJECT = 'Subject'
CDM_TYPE_FILE = 'FileObject'
CDM_TYPE_MEM = 'MemoryObject'
CDM_TYPE_SOCK = 'NetFlowObject'
CDM_TYPE_SRCSINK = 'SrcSinkObject'
CDM_TYPE_EDGE = 'SimpleEdge'
CDM_TYPE_EVENT = 'Event'

type_map = {
    # SubjectType
    'SUBJECT_PROCESS': 'a',
    'SUBJECT_THREAD': 'b',
    'SUBJECT_UNIT': 'c',
    'SUBJECT_BASIC_BLOCK': 'd',

    # Object Type
    'FILE_OBJECT_FILE': 'e',
    'FILE_OBJECT_DIR': 'e', # same as file
    'FILE_OBJECT_NAMED_PIPE': 'f', # CDM17
    'FILE_OBJECT_UNIX_SOCKET': 'g', # CDM17

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
    #'EVENT_OS_UNKNOWN': 'G',
    #'EVENT_KERNEL_UNKNOWN': 'H',
    #'EVENT_APP_UNKNOWN': 'I',
    #'EVENT_UI_UNKNOWN': 'J',
    'EVENT_MOUNT': 'G',
    'EVENT_STARTSERVICE': 'H',
    'EVENT_LOGIN': 'I',
    'EVENT_LOGOUT': 'J',
    #'EVENT_UNKNOWN': 'K',
    'EVENT_BLIND': 'L',
    'EVENT_UNIT': 'M',
    'EVENT_UPDATE': 'N',
    
    'FILE_OBJECT_PEFILE': 'O', # Added CDM13
    
    # CDM17
    'EVENT_DUP': 'P',
    'EVENT_FNCTL': 'Q',
    'EVENT_LSEEK': 'R',
    'EVENT_OTHER': 'S',
    'EVENT_SENDTO': 'T',
    'EVENT_SENDMSG': 'U',
    'EVENT_SHM': 'V',
    'EVENT_EXIT': 'W',
    'EVENT_LOADLIBRARY': 'X',
    'EVENT_BOOT': 'Y',
    'EVENT_LOGCLEAR': 'Z',

    # objects without subtypes
    'UnnamedPipeObject': '1',
    'RegistryKeyObject': '2',
    'NetFlowObject': '3',
    'MemoryObject': '4',
    'SrcSinkObject': '5', # subtypes exist but are Android-specific, except IPC
}
