import math
import gardenofworms_setup
import pyre.ai
import pyre.engine
import pyre.level
from pyre.garden import Worm, Slug, Butterfly, Seed, Plant
import pyglet
import pyglet.graphics
import random
import os
import numpy as np

NUM_SEEDS = 2
GARDEN_LENGTH = 10
player = pyre.engine.RTSPlayer


def main():
    window = None
    if os.name == 'nt':
        window = pyre.engine.Window(width=800, height=600, caption='Pyglet', resizable=True)
    if os.name == 'posix':
        window = pyre.engine.Window(width=800, height=600, caption='Pyglet', resizable=True)

    current_path = os.path.abspath(__file__)
    current_path = '\\'.join(current_path.split('\\')[:-1])
    pyglet.resource.path = ['.', './textures', './levels']
    pyglet.resource.path = [current_path, current_path + '/textures', current_path + '/levels']
    pyglet.resource.reindex()


    texture_region = pyglet.resource.texture('garden.png')
    texture_group = pyglet.graphics.TextureGroup(texture_region)
    # make an engine to control graphics
    engine = pyre.engine.Engine(window=window)
    engine.player = player()

    # load levels
    gardenofworms_setup.setup(engine=engine)

    # coordinates within garden.png
    tex_dict = {'slug': (texture_group, pyre.engine.tex_coord((0, 1), 4)),
                'plant': (texture_group, pyre.engine.tex_coord((0, 0), 4)),
                'butterfly': (texture_group, pyre.engine.tex_coord((1, 0), 4)),
                'seed': (texture_group, pyre.engine.tex_coord((1, 1), 4))}
    for world in engine.top_world.children[1].children:
        for i in range(NUM_SEEDS):
            spacing = GARDEN_LENGTH / math.sqrt(NUM_SEEDS)
            sz = 0.66 + random.random() / 3
            worm = Worm(position=np.array([random.random() * spacing - spacing / 2,
                                           random.random() * spacing - spacing / 2,
                                           0.5]),
                        size=(sz, sz, sz), butterfly_speed=np.array([0, 2, 0]),
                        lifetimes={
                            'butterfly': 2,
                            'seed': 1.5,
                            'plant': 1,
                            'slug': 1},
                        lifecycle=('butterfly', 'seed', 'plant', 'slug'),
                        guises={
                            'butterfly': Butterfly(engine.batch, tex_dict=tex_dict),
                            'seed': Seed(engine.batch, tex_dict=tex_dict),
                            'plant': Plant(engine.batch, tex_dict=tex_dict),
                            'slug': Slug(engine.batch, tex_dict=tex_dict),
                            },
                        lifetime_noise=3)
            worm.swap_ai(pyre.garden.WormAI)
            world.agents.append(worm)

    start_world = 1
    engine.top_world.activate(activate_children=False)
    engine.top_world.children[1].activate(activate_children=False)
    engine.top_world.children[1].children[start_world].activate()

    window.engine = engine
    engine.player.position = np.array((0., 0., 12.))
    window.setup()
    # window.minimize()

    # rpyc service for remote access
    pyre.engine.start_server(window)

    window.run()


if __name__ == '__main__':
    main()
