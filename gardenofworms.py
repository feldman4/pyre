import math
import pyre.ai
import pyre.engine
from pyre.garden import Worm, Slug, Butterfly, Seed, Plant
import pyglet
import pyglet.graphics
import random
import os

NUM_SEEDS = 20
GARDEN_LENGTH = 20


def main():
    window = None
    if os.name == 'nt':
        window = pyre.engine.Window(width=800, height=600, caption='Pyglet', resizable=True)

    # load file with face textures and make a group of it
    texture_region = pyglet.resource.texture('textures/garden.png')
    texture_group = pyglet.graphics.TextureGroup(texture_region)
    # make an engine to control graphics
    engine = pyre.engine.Engine()

    # coordinates within garden.png (subclass of Avatar)
    tex_dict = {'slug': pyre.engine.tex_coord((0, 1), 4),
                'plant': pyre.engine.tex_coord((0, 0), 4),
                'butterfly': pyre.engine.tex_coord((1, 0), 4),
                'seed': pyre.engine.tex_coord((1, 1), 4)}

    for i in range(NUM_SEEDS):
        spacing = GARDEN_LENGTH / math.sqrt(NUM_SEEDS)
        sz = 0.66 + random.random() / 3
        worm = Worm(position=(random.random() * spacing, random.random() * spacing, 0),
                    size=(sz, sz, sz),
                    guises={
                        'butterfly': Butterfly(texture_group, engine.batch, tex_dict=tex_dict),
                        'seed': Seed(texture_group, engine.batch, tex_dict=tex_dict),
                        'plant': Plant(texture_group, engine.batch, tex_dict=tex_dict),
                        'slug': Slug(texture_group, engine.batch, tex_dict=tex_dict),
                        })
        worm.swap_ai(pyre.garden.WormAI)
        engine.add_agent(worm)

    if os.name == 'posix':
        window = pyre.engine.Window(width=800, height=600, caption='Pyglet', resizable=True)

    window.engine = engine
    window.position = (0, 0, 8)
    window.setup()
    window.minimize()

    # rpyc service for remote access
    pyre.engine.start_server(window)

    window.run()


if __name__ == '__main__':
    main()
