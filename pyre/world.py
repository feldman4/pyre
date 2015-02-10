import subprocess

import networkx as nx

from pyre import objgraph_test


class World(object):
    def __init__(self, parent=None, agents=None, engine=None, name=None, switches=None):
        self.parent = parent
        self.agents = [] if agents is None else agents
        self.switches = [] if switches is None else switches
        """":type list[pyre.switch.Switch]:"""
        self.active = False
        self.last_active = False
        self.engine = engine
        self.name = name
        self.children = []

    def update(self, dt):
        for agent in self.agents:
            agent.update(dt)
        for switch in self.switches:
            switch.evaluate()
        for world in self.children:
            if world.active:
                world.update(dt)

    def activate(self, activate_children=True):
        """Activates World, adding itself to Engine.
        :param bool activate_children: apply to child Worlds
        :return:
        """
        self.last_active = self.active
        self.active = True
        for agent in self.agents:
            agent.show()
        for switch in self.switches:
            if switch.initialize_on_activation:
                switch.initialize()
        if activate_children:
            for world in self.children:
                world.activate(activate_children=True)

    def inactivate(self, inactivate_children=True):
        """Inactivate World, hiding Agents and removing them from Engine.
        :param bool inactivate_children: apply to child Worlds
        :return:
        """
        self.last_active = self.active
        self.active = False
        for agent in self.agents:
            agent.hide()
        if inactivate_children:
            for world in self.children:
                world.inactivate(inactivate_children=inactivate_children)

    def restore(self, restore_children=True):
        """Restores last active state
        :param bool restore_children: apply to child Worlds
        :return:
        """
        if self.last_active:
            self.activate(activate_children=restore_children)
        else:
            self.inactivate(inactivate_children=restore_children)

    def show_world_tree(self, types_to_filter=(list, dict), max_depth=10, too_many=10, open_dot=True,
                        filter_edges=('json',), dot_path="world_tree.dot"):
        """Saves directed graph of objects referenced by World to .dot file.
        :param tuple types_to_filter: types in this tuple are included in graph (dict mandatory to connect objects,
            World automatically included)
        :param int max_depth: max depth to explore
        :param int too_many: max edges explored for each node
        :param bool open_dot: if True, open graph in xdot
        :param tuple filter_edges: don't explore properties with names in this list
        """
        highlight_filter = lambda x: not isinstance(x, (list, dict))
        types_to_filter += (type(self),)
        graph_filter = lambda x: isinstance(x, types_to_filter)
        graph = objgraph_test.show_refs([self],
                                        filename=dot_path,
                                        max_depth=max_depth,
                                        too_many=too_many, filter=graph_filter,
                                        highlight=highlight_filter)
        graph = filter_object_graph(graph, filter_edges=filter_edges)
        nx.write_dot(graph, dot_path)
        import fileinput

        for i, line in enumerate(fileinput.input(dot_path, inplace=1)):
            if i == 1:
                print "node[shape=box, style=filled, fillcolor=white]",
            # doesn't work, for reasons unknown
            print line[:-1].replace('\n', '\\n') + '\n',

        if open_dot:
            subprocess.Popen(['xdot', dot_path])


def filter_object_graph(graph, filter_dict=True, filter_edges=()):
    """
    :param networkx.DiGraph graph: graph to filter
    :param bool filter_dict: if True, remove nodes pointed to by "__dict__" edges and reconnect edges
    :param tuple filter_edges: names of edges to remove (entire branch below edge is also removed)
    :return:
    """
    # cut out __dict__ objects
    top_node = nx.topological_sort(graph)[0]
    for start, end, data in graph.edges(data=True):
        if filter_dict:
            if 'label' in data.keys() and data['label'] == '"__dict__"':
                # reassign edges
                for edge in graph.edges(end, data=True):
                    graph.add_edge(start, edge[1], attr_dict=edge[2])
                # delete node
                graph.remove_node(end)
                continue
        for label_to_filter in filter_edges:
            if 'label' in data.keys() and data['label'] == '"' + label_to_filter + '"':
                graph.remove_node(end)
                break
    for L in nx.weakly_connected_component_subgraphs(graph):
        if top_node in L:
            return L


def swap_world(world_to_activate, world_to_inactivate, swap_children=False,
               restore=False):
    world_to_inactivate.inactivate(inactivate_children=True)
    if restore:
        world_to_activate.restore(restore_children=swap_children)
    else:
        world_to_activate.activate(activate_children=swap_children)