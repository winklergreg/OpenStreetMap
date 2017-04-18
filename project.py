#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import schema
import cerberus
from clean_data import clean

PATH = "/Users/GW/Documents/Udacity/Data_Wrangling/project/"
OSM_PATH = PATH + "buffalo-niagara-falls_new-york.osm"

NODES_PATH = PATH + "nodes.csv"
NODE_TAGS_PATH = PATH + "nodes_tags.csv"
WAYS_PATH = PATH + "ways.csv"
WAY_NODES_PATH = PATH + "ways_nodes.csv"
WAY_TAGS_PATH = PATH + "ways_tags.csv"

SCHEMA = schema.schema

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []
    temp_tags = {}
    colon_positions = []
    node = []
    pos = None # Used to store the position of a character in a string
    
    # Determine if the tag is a node or way tag and assign it to the appropriate dictionary
    if element.tag == 'node':
        node_attribs = {k: v for k, v in element.items() if k in node_attr_fields}

        # Find all node-tags
        if element.findall('tag'):
            for tag in element.findall('tag'):
                if not re.search(problem_chars, tag.attrib['k']):
                    temp_tags = ({'id': node_attribs['id']})
                    
                    if re.search(LOWER_COLON, tag.attrib['k']):
                        pos = tag.attrib['k'].index(":")
                        temp_tags.update({'key': tag.attrib['k'][pos+1:],
                                          'value': tag.attrib['v'],
                                          'type': tag.attrib['k'][:pos]})
                    else:
                        temp_tags.update({'key': tag.attrib['k'],
                                          'value': tag.attrib['v'],
                                          'type': default_tag_type})
        
                    tags.append(temp_tags)
        else:
            tags = []
        
        return {'node': node_attribs, 'node_tags': tags}
        
    elif element.tag == 'way':
        way_attribs = {k: v for k, v in element.items() if k in way_attr_fields}
        n = 0
        
        # Find all nodes and append to dictionary
        for node in element.findall('nd'):
            way_nodes.append({'id': way_attribs['id'],
                         'node_id': node.attrib['ref'],
                         'position': n})
            n += 1

        # Find all way-tags
        if element.findall('tag'):  
            for tag in element.findall('tag'):
                if not re.search(problem_chars, tag.attrib['k']):
                    temp_tags = ({'id': way_attribs['id']})
                    
                    if re.search(LOWER_COLON, tag.attrib['k']):
                        pos = tag.attrib['k'].index(':')
                        temp_tags.update({'key': tag.attrib['k'][pos+1:],
                                          'value': tag.attrib['v'],
                                          'type': tag.attrib['k'][:pos]})
                    else:
                        temp_tags.update({'key': tag.attrib['k'],
                                          'value': tag.attrib['v'],
                                          'type': default_tag_type})
        
                    tags.append(temp_tags)
        else:
            tags = []
        
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}
    else:
        pass
        

def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)
                
                # Write the data to csv files. Makes a call to the clean_data.py file before writing to csv
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    if len(el['node_tags']) > 0:
                        el['node_tags'] = clean(el['node_tags'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    if len(el['way_tags']) > 0:
                        el['way_tags'] = clean(el['way_tags'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    process_map(OSM_PATH, validate=True)

