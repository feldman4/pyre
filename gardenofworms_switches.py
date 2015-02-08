from pyre.switch import Switch, Counter
import pyre.garden
import pyre.world
from pyre.central_dispatch import central_dispatch
# define a Switch that loads the next level if all the Worms have transitioned through Seed


class MoveToLevelTwo(Switch):
    def __init__(self, engine, world, next_world):
        super(MoveToLevelTwo, self).__init__(engine, world)
        self.worms = []
        self.evolved = []
        self.next_world = next_world
        self.initialize_on_activation = True

    def initialize(self):
        # track all the Worms in the level
        for agent in self.world.agents:
            if agent.__class__ == pyre.garden.Worm:
                self.worms.append(agent)
                self.evolved.append(False)

    def evaluate(self):
        super(MoveToLevelTwo, self).evaluate()
        for i, worm in enumerate(self.worms):
            if worm.state == 'seed':
                self.evolved[i] = True
        if all(self.evolved) and len(self.evolved) > 0:
            self.do()

    def do(self):
        pyre.world.swap_world(self.next_world, self.world)