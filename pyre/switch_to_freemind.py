import xml


def dict2xml(d, root_node=None):
    wrap = False if None == root_node or isinstance(d, list) else True
    root = 'objects' if None == root_node else root_node
    root_singular = root[:-1] if 's' == root[-1] and None == root_node else root
    xml = ''
    children = []

    if isinstance(d, dict):
        for key, value in dict.items(d):
            if isinstance(value, dict):
                children.append(dict2xml(value, key))
            elif isinstance(value, list):
                children.append(dict2xml(value, key))
            else:
                xml = xml + ' ' + key + '="' + str(value) + '"'
    else:
        for value in d:
            children.append(dict2xml(value, root_singular))

    end_tag = '>' if 0 < len(children) else '/>'

    if wrap or isinstance(d, dict):
        xml = '<' + root + xml + end_tag

    if 0 < len(children):
        for child in children:
            xml = xml + child

        if wrap or isinstance(d, dict):
            xml = xml + '</' + root + '>'

    return xml


class Object(object):
    pass

import random
def mm_dict(switch_tree):
    my_dict = {'node': []}
    for switch in switch_tree:

        my_dict['node'].append({'TEXT': switch.name,
                                'ID': random.random()})
        print my_dict
    return {'node': {'node': my_dict,
                     'text': 'top'}}

switch1 = Object()
switch1.name = 'top'
switch1.switches = [Object(), Object()]
switch1.switches[0].name = 'first'
switch1.switches[1].name = 'second'

switch_dict = mm_dict(switch1.switches)
switch_dict['node']['node']['node'][0]['node'] = {'text': 1}
switch_xml = dict2xml(switch_dict, 'map')
switch_xml = switch_xml.replace('>', '>\n')
open('blah.mm', 'w').write(switch_xml)

"""
    Simple xml serializer.

    @author Reimund Trost 2013

    Example:

    mydict = {
        'name': 'The Andersson\'s',
        'size': 4,
        'children': {
            'total-age': 62,
            'child': [
                { 'name': 'Tom', 'sex': 'male', },
                {
                    'name': 'Betty',
                    'sex': 'female',
                    'grandchildren': {
                        'grandchild': [
                            { 'name': 'herbert', 'sex': 'male', },
                            { 'name': 'lisa', 'sex': 'female', }
                        ]
                    },
                }
            ]
        },
    }

    print(dict2xml(mydict, 'family'))

    Output:

      <family name="The Andersson's" size="4">
        <children total-age="62">
          <child name="Tom" sex="male"/>
          <child name="Betty" sex="female">
            <grandchildren>
              <grandchild name="herbert" sex="male"/>
              <grandchild name="lisa" sex="female"/>
            </grandchildren>
          </child>
        </children>
      </family>
"""
