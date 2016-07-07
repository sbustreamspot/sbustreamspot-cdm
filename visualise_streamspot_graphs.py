#!/usr/bin/env python

"""
    Visualises streamspot/infoleak_small_units.ss
    python visualise_streamspot_graph.py
"""

import argparse
from graph_tool.all import *
import pdb
import sys

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', help='Input StreamSpot file', required=True)
args = vars(parser.parse_args())

input_file = args['input']

process_color = [179/256.,205/256.,227/256.,0.8]
file_color = [251/256.,180/256.,174/256.,0.8]
mem_color = [204/256.,235/256.,197/256.,0.8]
sock_color = [222/256.,203/256.,228/256.,0.8]
srcsink_color = [0.,0.,0.,0.8]

group_map = {'SUBJECT_PROCESS': 0,
             'OBJECT_FILE': 1,
             'OBJECT_SOCK': 2,
             'OBJECT_MEM': 3,
             'OBJECT_SRCSINK': 4}

def create_new_graph():
    g = Graph()

    gid = g.new_graph_property('int')
    
    vid = g.new_vertex_property('string')
    vtype = g.new_vertex_property('string')
    vlabel = g.new_vertex_property('string')
    vgroup = g.new_vertex_property('int32_t')
    vcolor = g.new_vertex_property('vector<double>')
    
    etype = g.new_edge_property('string')
    elabel = g.new_edge_property('string')
    ecolor = g.new_edge_property('vector<double>')
    
    g.gp.id = gid

    g.vp.id = vid
    g.vp.type = vtype
    g.vp.label = vlabel
    g.vp.group = vgroup
    g.vp.color = vcolor

    g.ep.type = etype
    g.ep.label = elabel
    g.ep.color = ecolor

    return g

lno = 0
graphs = {} # from gid to graph
with open(input_file, 'r') as f:
    for line in f:
        lno += 1
        #if lno > 20:
        #    break
        line = line.strip()
        fields = line.split('\t')
        source_id = fields[0]
        source_name = fields[1]
        source_type = fields[2]
        dest_id = fields[3]
        dest_name = fields[4]
        dest_type = fields[5]
        edge_type = fields[6]
        graph_id = int(fields[7])

        if edge_type == 'EVENT_UNIT':
            continue

        if edge_type == 'EVENT_EXECUTE':
            continue # do not add this edge: it's a self-loop

        if not graph_id in graphs:
            graphs[graph_id] = create_new_graph()
        g = graphs[graph_id]

        # check if source vertex exists
        matches = find_vertex(g, g.vp.id, source_id)
        if len(matches) == 0:
            u = g.add_vertex()
            
            g.vp.id[u] = source_id
            g.vp.type[u] = source_type
            g.vp.label[u] = source_id + '\\' + source_name
            g.vp.group[u] = group_map[source_type]
           
            if source_type == 'SUBJECT_PROCESS':
                g.vp.color[u] = process_color
            elif source_type == 'OBJECT_FILE':
                g.vp.color[u] = file_color
            elif source_type == 'OBJECT_MEM':
                g.vp.color[u] = mem_color
            elif source_type == 'OBJECT_SOCK':
                g.vp.color[u] = sock_color
            elif source_type == 'OBJECT_SRCSINK':
                g.vp.color[u] = srcsink_color
            else:
                print 'unknown type', source_type
        else:
            u = matches[0]
        
        # check if destination vertex exists
        matches = find_vertex(g, g.vp.id, dest_id)
        if len(matches) == 0:
            v = g.add_vertex()
            
            g.vp.id[v] = dest_id
            g.vp.type[v] = dest_type
            g.vp.label[v] = dest_name
            g.vp.group[v] = group_map[dest_type]
            
            if dest_type == 'SUBJECT_PROCESS':
                g.vp.color[v] = process_color
            elif dest_type == 'OBJECT_FILE':
                g.vp.color[v] = file_color
                g.vp.label[v] = dest_name.split('/')[-1]
                #g.vp.label[v] = dest_name
            elif dest_type == 'OBJECT_MEM':
                g.vp.color[v] = mem_color
            elif dest_type == 'OBJECT_SOCK':
                g.vp.color[v] = sock_color
            elif dest_type == 'OBJECT_SRCSINK':
                g.vp.color[v] = srcsink_color
            else:
                print 'unknown type', dest_type
        else:
            v = matches[0]

        e = g.add_edge(u,v)
        g.ep.type[e] = edge_type
        g.ep.label[e] = str(lno) + ':' + edge_type.split('_')[-1]

        if edge_type in ['EVENT_EXECUTE', 'EVENT_CLONE', 'EVENT_FORK']:
            g.ep.color[e] = process_color
        elif edge_type in ['EVENT_OPEN', 'EVENT_READ', 'EVENT_WRITE',
                           'EVENT_UPDATE', 'EVENT_RENAME', 'EVENT_CREATE_OBJECT']:
            g.ep.color[e] = file_color
        elif edge_type in ['EVENT_BIND', 'EVENT_ACCEPT', 'EVENT_CONNECT']:
            g.ep.color[e] = sock_color
        else:
            g.ep.color[e] = [0.179, 0.203,0.210, 0.8]
 
for graph_id, g in graphs.iteritems():
    pos = sfdp_layout(g, groups=g.vp.group)
    graph_draw(g, pos, output_size=(2000, 2000),
               vertex_text=g.vp.label, edge_text=g.ep.label,
               vertex_shape='circle',
               #vertex_size=5.0,
               vertex_color=g.vp.color,
               edge_color=g.ep.color,
               vertex_fill_color=[1.0,1.0,1.0,0.8],
               vertex_pen_width=5.0, 
               edge_pen_width=5.0,
               edge_font_size=16,
               edge_font_weight=1.0,
               #nodesfirst=True,
               output='infoleaks_small_units_gid' + str(graph_id) + '.pdf')
