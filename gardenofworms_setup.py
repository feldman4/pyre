import pyre.world
import pyre.level
import gardenofworms_switches


def setup(engine=None):
    top_world = pyre.world.World(engine=engine, name='top')
    splash_screen = pyre.world.World(engine=engine, name='splash screen')
    garden = pyre.world.World(engine=engine, name='garden')
    garden.children = [pyre.world.World(engine=engine, name='garden1'),
                       pyre.world.World(engine=engine, name='garden2')]
    level1 = pyre.level.Level('garden.json', batch=engine.batch, scale=0.03125,
                              center_level_flag=True)
    level2 = pyre.level.Level('room.json', batch=engine.batch, scale=0.03125,
                              center_level_flag=True)
    garden.children[0].agents.append(level1)
    garden.children[1].agents.append(level2)

    top_world.children = [splash_screen, garden]

    # attach switches
    gardenofworms_switches.MoveToLevelTwo(engine, garden.children[0], garden.children[1])
    gardenofworms_switches.MoveToLevelTwo(engine, garden.children[1], garden.children[0])

    engine.top_world = top_world

    # butterflies get made in gardenofworms.py