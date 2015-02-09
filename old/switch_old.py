import pyre.central_dispatch


central_dispatch = pyre.central_dispatch.central_dispatch


class Switch(object):
    def __init__(self, conditions=None, actions=None, world=None, name=None):
        """Changes state of World out of time. Needs
        :param list[Condition] conditions:
        :param list[Action] actions:
        :param pyre.world.World world: parent World, used by Conditions and Actions to refer to World, Engine, Player
        :return:
        """
        self.conditions = [] if conditions is None else conditions
        self.actions = [] if actions is None else actions
        self.world = world
        self.world.switches.append(self)
        self.t = 0
        self.name = 'switch' if name is None else name

    def update(self, dt):
        self.t += dt
        switch_state = True
        for condition in self.conditions:
            state = condition.check()
            # unlatched conditions only need to be True once
            if state and not condition.latch:
                self.conditions.remove(condition)
                condition.remove()
            switch_state &= state
        if switch_state:
            self.act()

    def act(self):
        for action in self.actions:
            action.do()


class Condition(object):
    def __init__(self, switch, latch=True):
        self.latch = latch
        self.switch = switch

    def check(self):
        return False

    def remove(self):
        """Called when Condition is removed. De-registers listener from event dispatcher
            if applicable.
        :return:
        """
        pass


class PlayerCondition(Condition):
    def __init__(self, player_condition=lambda *args, **kwargs: False, *args, **kwargs):
        """Checks provided condition against current Engine.Player.
        :param function player_condition: accepts Engine.Player as argument, returns bool
        :return:
        """
        super(PlayerCondition, self).__init__(*args, **kwargs)
        self.player_condition = player_condition
        self.engine = self.switch.world.engine

    def check(self):
        return self._check_player_condition()

    def _check_player_condition(self):
        # get Player every time in case Player changes after Switch is defined
        return self.player_condition(self.engine.player)


class ObjectCondition(Condition):
    def __init__(self, target, object_condition, *args, **kwargs):
        """Evaluates object_condition applied to target.
        :param object target: argument for object_condition
        :param function object_condition: takes object as argument, returns bool
        :return:
        """
        super(ObjectCondition, self).__init__(*args, **kwargs)
        self.target = target
        self.object_condition = object_condition

    def check(self):
        return self.object_condition(self.target)


class RemoteCondition(Condition):
    def __init__(self, target_method, *args, **kwargs):
        """True when target method is called.
        :param function target:
        :return:
        """
        super(RemoteCondition, self).__init__(*args, **kwargs)
        self.target_method = target_method
        self.state = False

    def initialize(self):
        central_dispatch.watch(self.target_method, self.notify)

    def notify(self):
        self.state = True

    def check(self):
        return self.state


class Action(object):
    def __init__(self, switch):
        self.switch = switch

    def do(self):
        pass


class LoadWorldAction(Action):
    pass


class AttachAIAction(Action):
    pass


class SwapWorldAction(Action):
    def __init__(self, world_to_activate, world_to_inactivate=None, swap_children=False,
                 restore=False, *args, **kwargs):
        """Inactivate World containing Switch and
        :param pyre.world.World world:
        :return:
        """
        super(SwapWorldAction, self).__init__(*args, **kwargs)
        self.target_world = world_to_activate
        """:type: pyre.world.World"""
        self.swap_children = swap_children
        self.restore = restore
        self.world_to_inactivate = self.switch.world if world_to_inactivate is None else world_to_inactivate

    def do(self):
        self.world_to_inactivate.inactivate(inactivate_children=True)
        if self.restore:
            self.target_world.restore(restore_children=self.swap_children)
        else:
            self.target_world.activate(activate_children=self.swap_children)


class SetAgentAction(Action):
    pass


class SpawnAgentAction(Action):
    pass
