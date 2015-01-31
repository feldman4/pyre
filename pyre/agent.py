import numpy as np
from pyglet.gl import GL_QUADS
from pyglet.graphics import Batch, TextureGroup
import copy
import pyre.ai


class Agent(object):
    def __init__(self, avatar=None, visible=False, position=None, guises=None,
                 rotation=None, size=np.array([1, 1, 1]), texture_group=None, batch=None):
        """Represents an entity physically embodied by an Avatar and updated by an AI

        :param bool avatar:
        :param bool visible: whether to show
        :param numpy.ndarray position: (x,y,z)
        :param numpy.ndarray rotation: (theta, phi)
        :param float speed:
        :param dict guises: Avatars corresponding to Agent state, must be initialized when Agent is created
        :return:
        """

        self.avatar = avatar
        self.visible = visible
        self.position = position
        self.rotation = rotation
        self.size = size
        self.texture_group = texture_group
        self.batch = batch
        self.guises = guises
        """:type : dict:"""
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

    def swap_ai(self, ai, *args, **kwargs):
        self.ai = copy.deepcopy(ai)(self, *args, **kwargs)

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
        self.avatar.size = self.size
        self.avatar.show()

    def __del__(self):
        if self.avatar:
            self.avatar.delete()


class PhysicalAgent(Agent):
    def __init__(self, velocity=None, angular_velocity=None, speed=None, *args, **kwargs):
        """An Agent that keeps track of its position, rotation, and corresponding velocities.
        :param velocity:
        :param angular_velocity:
        :param numpy.array speed: acts same as velocity, but automatically rotated and intended to be
            overwritten not incremented
        :param args:
        :param kwargs:
        :return:
        """
        super(PhysicalAgent, self).__init__(*args, **kwargs)

        self.velocity = np.array([0., 0., 0.]) if velocity is None else velocity
        self.angular_velocity = np.array([0., 0., 0.]) if angular_velocity is None else angular_velocity
        self.speed = np.array([0., 0., 0.]) if speed is None else speed

        self.rotation = np.array([0., 0., 0.]) if self.rotation is None else self.rotation


class Spin(Agent):
    def __init__(self, spin=False, avatar_state=None, *args, **kwargs):
        """Creates a binary spin.

        :param bool spin: state of spin
        :return:
        """
        super(Spin, self).__init__(*args, **kwargs)

        self.spin = spin
        self.neighbors = []
        """:type : list[Spin]"""
        self.lifetime = 0.3

        if not avatar_state:
            self.avatar_state = {True: 'red', False: 'blue'}
        else:
            self.avatar_state = avatar_state

    def neighbor_sum(self):
        return sum(n.spin for n in self.neighbors)

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
    def __init__(self, texture_group, batch, tex_dict=None, state_dict=None,
                 position=None, rotation=None):
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
        self.position = position
        self.rotation = rotation
        self.vertex_lists = []
        """:type: list[pyglet.graphics.vertexdomain.VertexList]"""

        self.state = None

    def show(self):
        """ Update Avatar state based on state dict
        :return:
        """
        pass

    def hide(self):
        pass


class Avatar2D(Avatar):
    def __init__(self, texture_group, batch,
                 size=(1, 1, 1), color=(255, 0, 0), *args, **kwargs):
        """Parent class for 2D Avatars, handles rotation before display.
        :param color:
        :return:
        """
        super(Avatar2D, self).__init__(texture_group, batch, *args, **kwargs)
        self.color = color
        self.size = size
        if self.rotation is None:
            self.rotation = np.array([0., 0., 0.])

    def square_vertices(self):
        """Get vertices of square after applying translation and rotation.
        :return:
        """
        vertices = np.array(SQUARE_VERTICES)
        vertices = np.array((vertices - 0.5) * self.size)
        vertices = rotate_vertices(vertices, self.rotation) + self.position
        return vertices.flatten()

    def show(self):
        """Add a VertexList to the Batch or update existing.
        :return:
        """
        super(Avatar2D, self).show()
        tex_coords = self.tex_dict[self.state_dict[self.state]]
        vertex_data = self.square_vertices()

        if not (self.vertex_lists and len(self.vertex_lists)):
            # create vertex list
            self.vertex_lists = [self.batch.add(4, GL_QUADS, self.texture_group,
                                                ('v3f', vertex_data), ('t2f', tex_coords))]
        else:
            # update vertex list
            self.vertex_lists[0].vertices = vertex_data
            self.vertex_lists[0].tex_coords = tex_coords

    def hide(self):
        self.vertex_lists[0].delete()
        self.vertex_lists = None


SQUARE_VERTICES = [[0, 0, 0],
                   [1, 0, 0],
                   [1, 1, 0],
                   [0, 1, 0]]
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
        """A Cube with a dictionary defining the surface textures in each state.
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
        vertices = np.array(CUBE_VERTICES)
        vertices = rotate_vertices((vertices - 0.5), self.rotation) * self.size + self.position
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


def rotation_matrix(rotation):
    """
    Builds three sequential rotation matrices parametrized by rotation angles about
    x, y, z axes.
    :param np.array rotation: [x, y, z] basis rotation angles
    :return dict: dictionary with x, y, z rotation matrices
    """
    x, y, z = rotation
    return {'x': np.array([[1, 0, 0],
                           [0, np.cos(x), -np.sin(x)],
                           [0, np.sin(x), np.cos(x)]]),
            'y': np.array([[np.cos(y), 0, np.sin(y)],
                           [0, 1, 0],
                           [-np.sin(y), 0, np.cos(y)]]),
            'z': np.array([[np.cos(z), -np.sin(z), 0],
                           [np.sin(z), np.cos(z), 0],
                           [0, 0, 1]])
    }


def rotate_vertices(vertices, rotation):
    """
    Rotate numpy array of vertices using [x,y,z] rotation angles provided in rotation
    :param vertices:
    :param rotation:
    :return:
    """
    r = rotation_matrix(rotation)
    return r['z'].dot(r['y'].dot(r['x'])).dot(vertices.T).T