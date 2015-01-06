import numpy as np
from pyglet.gl import GL_QUADS
from pyglet.graphics import Batch, TextureGroup
import copy
import pyre.ai


class Agent(object):
    def __init__(self, avatar=None, visible=False, position=None,
                 rotation=None):
        """Represents an entity physically embodied by an Avatar and updated by an AI

        :param bool avatar:
        :param bool visible: whether to show
        :param tuple position: (x,y,z)
        :param tuple rotation: (theta, phi)
        :return:
        """

        self.avatar = avatar
        self.visible = visible
        self.position = position
        self.rotation = rotation
        self.guise_state = {}
        self.t = 0
        self.ai = pyre.ai.AI(self)

    def update(self, dt):
        """Updates AI, then updates avatar, then shows avatar.

        :param float dt: Real time interval since last update.
        :return:
        """
        self.t += dt
        self.update_ai(dt)
        if self.avatar:
            self.update_avatar()

    def update_ai(self, dt):
        """Call AI object's update function.

        :param dt: Real time interval since last update.
        :return:
        """
        self.ai.update(dt)
        pass

    def update_avatar(self):
        """Updates state of Avatar to reflect Agent.

        :return:
        """
        self.avatar.position = self.position
        self.avatar.rotation = self.rotation
        self.avatar.show()

    def __del__(self):
        if self.avatar:
            self.avatar.delete()


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
        """:type : list[Agent]"""
        if not avatar_state:
            self.avatar_state = {True: 'red', False: 'blue'}
        else:
            self.avatar_state = avatar_state

    def neighbor_sum(self):
        return sum(n.spin for n in self.neighbors)

    def swap_ai(self, ai):
        self.ai = copy.deepcopy(ai)(self)

    def update_avatar(self):
        """Update linked Avatar with possible states True, False

        :return:
        """
        self.avatar.state = self.spin
        super(Spin, self).update_avatar()

    def flip(self):
        """Flip spin.

        :return: Spin after flip
        :rtype: bool
        """
        self.spin = not self.spin

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
    def __init__(self, texture_group, batch, tex_dict=None, state_dict=None):
        """Visual manifestation of Agent. Manipulated by the Agent's update method.
        Graphics:
            The Avatar is informed of a Batch, which it uses to track any VertexLists it creates.

        :param TextureGroup texture_group: Binds Texture containing all textures.
        :param Batch batch: Master Batch located in Engine.
        :param dict tex_dict: Dictionary to look up texture coordinates. Usage depends on subclass.
        :param dict state_dict: Dictionary with self.state as key, returns tuple of keys to tex_dict
                                (exact form depends on subclass).
        :return:
        """
        self.texture_group = texture_group
        self.batch = batch
        self.tex_dict = tex_dict
        self.state_dict = state_dict

        self.vertex_lists = []
        """:type: list[pyglet.graphics.vertexdomain.VertexList]"""
        self.position = (0, 0, 0)
        self.rotation = (0, 0)

        self.state = None

    def show(self):
        """ Update Avatar state based on state dict
        :return:
        """
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
    def __init__(self, texture_group, batch, size=(1, 1, 1),
                 tex_dict=None, state_dict=None):
        """

        :param TextureGroup texture_group: Contains textures for Cube faces.
        :param Batch batch: pyglet Batch to which VertexList is added
        :param tuple size: (x,y,z) extension of cube (more like a rectangular prism)
        :param dict state_dict: Keys are True, False; entries are tuple of keys into tex_dict
                                    for each face, (TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT)
        :param dict tex_dict: contains tex_coords in texture_group corresponding to keys in faces
        :return:
        """
        super(Cube, self).__init__(texture_group, batch, tex_dict=tex_dict, state_dict=state_dict)

        self.size = size

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
        faces = self.state_dict[self.state]
        vertex_data = self.cube_vertices()
        tex_coords = [x for face in faces for x in self.tex_dict[face]]

        if not self.vertex_lists:
            # create vertex list
            self.vertex_lists = [self.batch.add(24, GL_QUADS, self.texture_group,
                                                ('v3f', vertex_data), ('t2f', tex_coords))]
        else:
            self.vertex_lists[0].vertices = vertex_data
            self.vertex_lists[0].tex_coords = tex_coords

    def hide(self):
        self.vertex_lists[0].delete()
