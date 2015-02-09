import numpy as np
from pyglet.gl import GL_QUADS
from pyglet.graphics import Batch, TextureGroup
import copy
import pyre.ai
import pyre.engine


class Agent(object):
    def __init__(self, avatar=None, visible=False, position=None, guises=None,
                 rotation=None, size=np.array([1, 1, 1]), scale=1, batch=None):
        """Represents an entity physically embodied by an Avatar and updated by an AI

        :param Avatar avatar:
        :param bool visible: whether to show
        :param numpy.ndarray position: (x,y,z)
        :param numpy.ndarray rotation: (theta, phi)
        :param float speed:
        :param dict guises: Avatars corresponding to Agent state, must be initialized when Agent is created
        :return:
        """

        self.avatar = Avatar(batch)  # nonsense to straighten out UML hierarchy
        self.avatar = avatar
        """:type: Avatar"""
        self.visible = visible
        self.position = position
        self.rotation = rotation
        self.size = size
        self.scale = scale
        self.batch = batch
        self.guises = guises
        """:type : dict:"""
        self.t = 0
        self.ai = pyre.ai.AI(self)

    def update(self, dt):
        """Updates AI, then updates avatar.

        :param float dt: Real time interval since last update.
        :return:
        """
        self.t += dt
        self.update_ai(dt)
        if self.avatar:
            self.update_avatar()

    def swap_ai(self, ai, *args, **kwargs):
        self.ai = copy.deepcopy(ai)(self, *args, **kwargs)

    def show(self):
        self.avatar.show()

    def hide(self):
        self.avatar.hide()

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
        self.avatar.coordinate.position = self.position
        self.avatar.coordinate.rotation = self.rotation
        self.avatar.coordinate.size = self.size
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

        self.position = np.array([0., 0., 0.]) if self.position is None else self.position
        self.rotation = np.array([0., 0., 0.]) if self.rotation is None else self.rotation

        self.velocity = np.array([0., 0., 0.]) if velocity is None else velocity
        self.angular_velocity = np.array([0., 0., 0.]) if angular_velocity is None else angular_velocity
        self.speed = np.array([0., 0., 0.]) if speed is None else speed


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
    def __init__(self, batch, tex_dict=None, state_dict=None,
                 position=None, rotation=None, scale=1, size=(1, 1, 1)):
        """Visual manifestation of Agent. Manipulated by the Agent's update method.
        Graphics:
            The Avatar is informed of a Batch, which it uses to track any VertexLists it creates.

        :param Batch batch: Master Batch located in Engine.
        :param dict tex_dict: Dictionary mapping state to (TextureGroup, texture coordinates). Usage depends on subclass.
        :param dict state_dict: Dictionary with self.state as key, returns tuple of keys to tex_dict
                                (exact form depends on subclass).
        :return:
        """
        self.batch = batch
        self.tex_dict = tex_dict
        self.state_dict = {None: None} if state_dict is None else state_dict
        self.coordinate = pyre.engine.Coordinate(position=position,
                                                 rotation=rotation,
                                                 scale=scale,
                                                 size=size,
                                                 center_flag=True,
                                                 translate_first=False)
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


class CompositeAvatar(Avatar):
    def __init__(self, batch, avatar_list=None, *args, **kwargs):
        super(CompositeAvatar, self).__init__(batch, *args, **kwargs)
        self.avatar_list = [] if avatar_list is None else avatar_list

    def show(self):
        for avatar in self.avatar_list:
            avatar.show()

    def hide(self):
        for avatar in self.avatar_list:
            avatar.hide()


class Avatar2D(Avatar):
    def __init__(self, batch, *args, **kwargs):
        """Parent class for 2D Avatars, handles rotation before display.
        :param color:
        :return:
        """
        super(Avatar2D, self).__init__(batch, *args, **kwargs)

    def rectangle_vertices(self):
        """Get vertices of rectangle after applying translation and rotation.
        :return:
        """
        return self.coordinate.transform(SQUARE_VERTICES).flatten()

    def show(self):
        """Add a VertexList to the Batch or update existing.
        :return:
        """
        texture_group, tex_coords = self.tex_dict[self.state_dict[self.state]]
        vertex_data = self.rectangle_vertices()

        if not (self.vertex_lists and len(self.vertex_lists)):
            # create vertex list
            self.vertex_lists = [self.batch.add(4, GL_QUADS, texture_group,
                                                ('v3f', vertex_data), ('t2f', tex_coords))]
        else:
            # update vertex list
            self.vertex_lists[0].vertices = vertex_data
            self.vertex_lists[0].tex_coords = tex_coords

    def hide(self):
        if len(self.vertex_lists) > 0:
            self.vertex_lists[0].delete()
        self.vertex_lists = None


SQUARE_VERTICES = np.array([[0., 0., 0.],
                            [1., 0., 0.],
                            [1., 1., 0.],
                            [0., 1., 0.]])
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


# class Cube(Avatar):
#     def __init__(self, texture_group, batch, size=(1, 1, 1),
#                  tex_dict=None, state_dict=None):
#         """A Cube with a dictionary defining the surface textures in each state.
#         :param TextureGroup texture_group: Contains textures for Cube faces.
#         :param Batch batch: pyglet Batch to which VertexList is added
#         :param tuple size: (x,y,z) extension of cube (more like a rectangular prism)
#         :param dict state_dict: Keys are True, False; entries are tuple of keys into tex_dict
#                                     for each face, (TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT)
#         :param dict tex_dict: contains tex_coords in texture_group corresponding to keys in faces
#         :return:
#         """
#         super(Cube, self).__init__(texture_group, batch, tex_dict=tex_dict, state_dict=state_dict)
#
#         self.size = size
#
#     # noinspection PyTypeChecker
#     def cube_vertices(self):
#         """Returns coordinates of cube after scaling, translation, rotation.
#         :return: 24 x 3 array of vertex coordinates
#         """
#         vertices = np.array(CUBE_VERTICES)
#         vertices = rotate_vertices((vertices - 0.5), self.rotation) * self.size + self.position
#         return vertices[CUBE_TOP + CUBE_BOTTOM + CUBE_FRONT + CUBE_BACK + CUBE_LEFT + CUBE_RIGHT].flatten()
#
#     def show(self):
#         """Add a VertexList to the Batch or update existing.
#         :return:
#         """
#         faces = self.state_dict[self.state]
#         vertex_data = self.cube_vertices()
#         tex_coords = [x for face in faces for x in self.tex_dict[face][1]]
#         texture_group = self.tex_dict[face][0]
#
#         if not self.vertex_lists:
#             # create vertex list
#             self.vertex_lists = [self.batch.add(24, GL_QUADS, texture_group,
#                                                 ('v3f', vertex_data), ('t2f', tex_coords))]
#         else:
#             self.vertex_lists[0].vertices = vertex_data
#             self.vertex_lists[0].tex_coords = tex_coords
#
#     def hide(self):
#         self.vertex_lists[0].delete()

