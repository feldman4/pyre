import pyre.ai
import pyre.engine
from pyre.agent import Spin, Cube
import pyglet
import pyglet.graphics
import random
import os

CRYSTAL_SIZE = 4


def main():

    window = None
    if os.name == 'nt':
        window = pyre.engine.Window(width=800, height=600, caption='Pyglet', resizable=True)

    # load file with face textures and make a group of it
    texture_region = pyglet.resource.texture('texture.png')
    texture_group = pyglet.graphics.TextureGroup(texture_region)
    # make an engine to control graphics
    engine = pyre.engine.Engine()

    # make a bunch of Spins and associate them with Cubes (subclass of Avatar)
    tex_dict = {'red': pyre.engine.tex_coord((0, 0), 4),
                'blue': pyre.engine.tex_coord((1, 0), 4)}

    state_dict = {True: ('red',)*6, False: ('blue',)*6}

    spin_list = [[0 for _ in range(2*CRYSTAL_SIZE)] for _ in range(2*CRYSTAL_SIZE)]
    """:type: list[list[Spin]]"""

    for i in range(-CRYSTAL_SIZE, CRYSTAL_SIZE):
        for j in range(-CRYSTAL_SIZE, CRYSTAL_SIZE):
            cube = Cube(texture_group, engine.batch,
                        tex_dict=tex_dict, state_dict=state_dict,
                        size=(0.8, 0.8, 0.8))
            spin = Spin(position=(i, j, 0), avatar=cube, spin=random.random() > 0.3)
            spin.swap_ai(pyre.ai.GameOfLife)
            engine.add_agent(spin)
            spin_list[i][j] = spin

    for i in range(-CRYSTAL_SIZE, CRYSTAL_SIZE):
        for j in range(-CRYSTAL_SIZE, CRYSTAL_SIZE):
            for m, n in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                spin_list[i][j].link_neighbor(spin_list[i + m][j+n])

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
