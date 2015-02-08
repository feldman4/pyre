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


def swap_world(world_to_activate, world_to_inactivate, swap_children=False,
               restore=False):
    world_to_inactivate.inactivate(inactivate_children=True)
    if restore:
        world_to_activate.restore(restore_children=swap_children)
    else:
        world_to_activate.activate(activate_children=swap_children)