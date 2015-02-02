import math
import pyre.ai
import pyre.engine
import pyre.level
from pyre.garden import Worm, Slug, Butterfly, Seed, Plant
import pyglet
import pyglet.graphics
import random
import os
import numpy as np

NUM_SEEDS = 18
GARDEN_LENGTH = 10
player = pyre.engine.RTSPlayer


def main():
    window = None
    if os.name == 'nt':
        window = pyre.engine.Window(width=800, height=600, caption='Pyglet', resizable=True)
    if os.name == 'posix':
        window = pyre.engine.Window(width=800, height=600, caption='Pyglet', resizable=True)

    pyglet.resource.path = ['.', './textures', './levels']
    pyglet.resource.reindex()

    # load file with face textures and make a group of it
    texture_region = pyglet.resource.texture('garden.png')
    texture_group = pyglet.graphics.TextureGroup(texture_region)
    # make an engine to control graphics
    engine = pyre.engine.Engine(window=window)
    engine.player = player()

    # load level
    engine.levels = [pyre.level.Level('garden2.json', batch=engine.batch, scale=0.025,
                                      center_flag=True)]
    engine.show_levels()

    # coordinates within garden.png
    tex_dict = {'slug': pyre.engine.tex_coord((0, 1), 4),
                'plant': pyre.engine.tex_coord((0, 0), 4),
                'butterfly': pyre.engine.tex_coord((1, 0), 4),
                'seed': pyre.engine.tex_coord((1, 1), 4)}

    for i in range(NUM_SEEDS):
        spacing = GARDEN_LENGTH / math.sqrt(NUM_SEEDS)
        sz = 0.66 + random.random() / 3
        worm = Worm(position=np.array([random.random() * spacing - spacing/2,
                                       random.random() * spacing - spacing/2,
                                       0.5]),
                    size=(sz, sz, sz), butterfly_speed=np.array([0, 2, 0]),
                    lifetimes={
                        'butterfly': 6,
                        'seed': 1.5,
                        'plant': 1,
                        'slug': 1},
                    lifecycle=('butterfly', 'seed', 'plant', 'slug'),
                    guises={
                        'butterfly': Butterfly(texture_group, engine.batch, tex_dict=tex_dict),
                        'seed': Seed(texture_group, engine.batch, tex_dict=tex_dict),
                        'plant': Plant(texture_group, engine.batch, tex_dict=tex_dict),
                        'slug': Slug(texture_group, engine.batch, tex_dict=tex_dict),
                        },
                    lifetime_noise=3)
        worm.swap_ai(pyre.garden.WormAI)
        engine.add_agent(worm)

    window.engine = engine
    engine.player.position = np.array((0., 0., 12.))
    window.setup()
    # window.minimize()

    # rpyc service for remote access
    pyre.engine.start_server(window)

    window.run()


if __name__ == '__main__':
    main()
