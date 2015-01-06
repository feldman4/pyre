from pyre.ai import game_of_life
import pyre.engine
from pyre.agent import Spin, Cube
import pyglet
import pyglet.graphics
import random
import types
import time

import rpyc
from rpyc.utils.server import ThreadedServer
from threading import Thread

CRYSTAL_SIZE =2


def main():
    # rpyc service for remote access
    junk = 3
    class MyService(rpyc.Service):
        def exposed_get_main_window(self):
            return window
        def exposed_set_junk(self,x):
            global junk
            junk = x
            return junk

    start_server(MyService)

    # load file with face textures and make a group of it
    texture_region = pyglet.resource.texture('texture.png')
    texture_group = pyglet.graphics.TextureGroup(texture_region)

    # make an engine to control graphics
    engine = pyre.engine.Engine()
    engine.junk = junk

    # make a bunch of Spins and associate them with Cubes (subclass of Avatar)
    tex_dict = {'red': pyre.engine.tex_coord((0, 0), 4),
                'blue': pyre.engine.tex_coord((1, 0), 4)}
    spin_list = [[0 for _ in range(2*CRYSTAL_SIZE)] for _ in range(2*CRYSTAL_SIZE)]
    """:type: list[list[Spin]]"""
    for i in range(-CRYSTAL_SIZE, CRYSTAL_SIZE):
        for j in range(-CRYSTAL_SIZE, CRYSTAL_SIZE):
            cube = Cube(texture_group, engine.batch, tex_dict=tex_dict, size=(0.8, 0.8, 0.8))
            spin = Spin(position=(i, j, 0), avatar=cube, spin=random.random() > 0.3)
            spin.ai = game_of_life
            engine.add_agent(spin)
            spin_list[i][j] = spin

    for i in range(-CRYSTAL_SIZE, CRYSTAL_SIZE):
        for j in range(-CRYSTAL_SIZE, CRYSTAL_SIZE):
            for m, n in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                spin_list[i][j].link_neighbor(spin_list[i + m][j+n])

    window = pyre.engine.Window(width=800, height=600, caption='Pyglet', resizable=True, engine=engine)
    window.position = (0, 0, 8)
    window.setup()
    window.minimize()

    window.run()


def start_server(my_service):
    # start the rpyc server
    server = ThreadedServer(my_service, port=12345,
                            protocol_config={"allow_all_attrs": True,
                                             "allow_setattr": True,
                                             "allow_pickle": True})
    t = Thread(target=server.start)
    t.daemon = True
    t.start()


if __name__ == '__main__':
    main()

