import copy
from pyglet import image
import numpy as np
from pyglet.gl import GL_QUADS
from pyglet.graphics import Batch, TextureGroup
import pyre.ai
import time


class Agent(object):
    def __init__(self, avatar=None, visible=False, position=None):
        """

        :param bool avatar:
        :param bool visible:
        :param tuple position:
        :return:
        """

        self.avatar = avatar
        self.visible = visible
        self.position = position
        self.guise_state = {}
        self.ai = None
        self.whatever = lambda x: x**2

    def update(self, dt):
        """Updates agent internal state.

        :param float dt: Real time interval since last update.
        :return:
        """
        if self.avatar:
            self.avatar.position = self.position
            # FIXME add rotation
            self.avatar.show()

    def __del__(self):
        if self.avatar:
            self.avatar.delete()


class Critter(Agent):
    def __init__(self, position, color='undecided', visible=False, *args, **kwargs):
        super(Critter, self).__init__(*args, **kwargs)

        self.color = color
        self.position = position
        self.visible = visible


class Spin(Agent):
    def __init__(self, spin=False, avatar_state=None, *args, **kwargs):
        """Creates a binary spin.

        :param bool spin: state of spin
        :return:
        """
        super(Spin, self).__init__(*args, **kwargs)

        self.spin = spin
        self.neighbors = []
        self.lifetime = 0.3
        self.t = 0
        self.next_ai = pyre.ai.game_of_life
        """:type : list[Agent]"""
        if not avatar_state:
            self.avatar_state = {True: 'red', False: 'blue'}
        else:
            self.avatar_state = avatar_state

    def update(self, dt):
        """Flip spin, then do Agent update.

        :param dt:
        :return:
        """
        self.t += dt
        if self.t > self.lifetime:
            self.flip()
            self.t = 0
        super(Spin, self).update(dt)


    def neighbor_sum(self):
        return sum(n.spin for n in self.neighbors)

    def new_ai(self, func):
        self.ai = copy.deepcopy(func)

    def flip(self):
        """Flip spin.

        :return: Spin after flip
        :rtype: bool
        """
        # self.spin = not self.spin
        up = ('red',)*6
        down = ('blue',)*6


        self.spin = self.ai(self.spin, self.neighbor_sum())

        if self.avatar:
            if self.spin:
                self.avatar.faces = up
            else:
                self.avatar.faces = down

        return self.spin

    def link_neighbor(self, spin):
        """Add a neighboring spin.

        :param Spin spin: spin to add
        :return:
        """
        self.neighbors.append(spin)

    def unlink_neighbor(self, neighbor=None):
        """Forget a neighboring spin.

        :param Spin neighbor: Spin to remove, pops last if none provided.
        :return:
        """
        if neighbor in self.neighbors:
            self.neighbors.remove(neighbor)
        elif self.neighbors:
            self.neighbors.pop()
        else:
            print 'attempted to remove neighbor from empty neighborhood'


class Avatar(object):
    def __init__(self, texture_group, batch, tex_dict=None):
        """Visual manifestation of Agent. Manipulated by the Agent's update method.
        Graphics:
            The Avatar is informed of a Batch, which it uses to track any VertexLists it creates.

        :param TextureGroup texture_group: Binds Texture containing all textures.
        :param Batch batch: Master Batch located in Engine.
        :param dict tex_dict: Dictionary to look up texture coordinates. Usage depends on subclass.
        :return:
        """
        self.texture_group = texture_group
        self.tex_dict = tex_dict
        self.vertex_lists = []
        """:type: list[pyglet.graphics.vertexdomain.VertexList]"""
        self.position = (0, 0, 0)
        self.rotation = (0, 0)
        self.batch = batch

    def show(self):
        pass


CUBE_VERTICES = [[0, 0, 0],
                 [0, 0, 1],
                 [0, 1, 0],
                 [0, 1, 1],
                 [1, 0, 0],
                 [1, 0, 1],
                 [1, 1, 0],
                 [1, 1, 1]]
CUBE_LEFT = [0, 1, 3, 2]
CUBE_RIGHT = [4, 5, 7, 6]
CUBE_FRONT = [0, 1, 5, 4]
CUBE_BACK = [2, 3, 7, 6]
CUBE_TOP = [1, 3, 7, 5]
CUBE_BOTTOM = [0, 2, 6, 4]


class Cube(Avatar):
    def __init__(self, texture_group, batch, size=(1, 1, 1), faces=('red',)*6, tex_dict=None):
        """

        :param TextureGroup texture_group: Contains textures for Cube faces.
        :param Batch batch: pyglet Batch to which VertexList is added
        :param size:
        :param tuple faces: list of keys into tex_dict for each face, (TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT)
        :param tex_dict: contains tex_coords in texture_group corresponding to keys in faces
        :return:
        """
        super(Cube, self).__init__(texture_group, batch, tex_dict=tex_dict)

        self.size = size
        self.faces = faces

    # noinspection PyTypeChecker
    def cube_vertices(self):
        """Returns coordinates of cube after scaling, translation, rotation.

        :return: 24 x 3 array of vertex coordinates
        """
        # FIXME add rotation
        vertices = np.array(CUBE_VERTICES)
        vertices = (vertices - 0.5) * self.size + self.position
        return vertices[CUBE_TOP + CUBE_BOTTOM + CUBE_FRONT + CUBE_BACK + CUBE_LEFT + CUBE_RIGHT].flatten()

    def show(self):
        """Add a VertexList to the Batch or update existing.

        :return:
        """
        vertex_data = self.cube_vertices()
        tex_coords = [x for face in self.faces for x in self.tex_dict[face]]

        if not self.vertex_lists:
            # create vertex list
            self.vertex_lists = [self.batch.add(24, GL_QUADS, self.texture_group,
                                                ('v3f', vertex_data), ('t2f', tex_coords))]
        else:
            self.vertex_lists[0].vertices = vertex_data
            self.vertex_lists[0].tex_coords = tex_coords

    def hide(self):
        self.vertex_lists[0].delete()


