from pyglet.gl import GL_QUADS
from agent import Agent, Avatar
import numpy as np


class Worm(Agent):
    def __init__(self, initial_state='slug', color=(255, 0, 0), *args, **kwargs):
        """
        Its lifecycle has four states.
        :param string initial_state:
        :param tuple color: an RGB tuple, e.g., (255, 0, 0)
        :param args:
        :param kwargs:
        :return:
        """
        super(Worm, self).__init__(*args, **kwargs)
        self.state = initial_state
        self.lifetime = 4
        self.color = color

        self.avatar = self.guises[self.state]

        self.lifecycle = ['butterfly', 'seed', 'plant', 'slug']

    def evolve(self):
        self.state = self.lifecycle[(self.lifecycle.index(self.state) + 1) % len(self.lifecycle)]
        self.avatar.hide()
        self.avatar = self.guises[self.state]


class GardenAvatar(Avatar):
    def __init__(self, texture_group, batch,
                 size=(1, 1, 1), color=(255, 0, 0), *args, **kwargs):
        """
            Parent class for garden-variety Avatars.
            :param color:
            :return:
            """
        super(GardenAvatar, self).__init__(texture_group, batch, *args, **kwargs)
        self.color = color
        self.size = size
        self.SQUARE_VERTICES = [[0, 0, 0],
                                [1, 0, 0],
                                [1, 1, 0],
                                [0, 1, 0]]

    def square_vertices(self):
        vertices = np.array(self.SQUARE_VERTICES)
        vertices = (vertices - 0.5) * self.size + self.position
        return vertices.flatten()

    def show(self):
        super(GardenAvatar, self).show()
        """Add a VertexList to the Batch or update existing.

            :return:
            """
        tex_coords = self.tex_dict[self.state_dict[self.state]]
        vertex_data = self.square_vertices()

        # detect weird dangling reference
        if self.vertex_lists and len(self.vertex_lists):
            self.vertex_lists[0].vertices = vertex_data
            self.vertex_lists[0].tex_coords = tex_coords

        else:
            # create vertex list
            self.vertex_lists = [self.batch.add(4, GL_QUADS, self.texture_group,
                                                ('v3f', vertex_data), ('t2f', tex_coords))]

    def hide(self):
        self.vertex_lists[0].delete()
        self.vertex_lists = None


class Slug(GardenAvatar):
    def __init__(self, texture_group, batch, *args, **kwargs):
        super(Slug, self).__init__(texture_group, batch, *args, **kwargs)
        self.state_dict = {None: 'slug'}


class Seed(GardenAvatar):
    def __init__(self, texture_group, batch, *args, **kwargs):
        super(Seed, self).__init__(texture_group, batch, *args, **kwargs)
        self.state_dict = {None: 'seed'}


class Plant(GardenAvatar):
    def __init__(self, texture_group, batch, *args, **kwargs):
        super(Plant, self).__init__(texture_group, batch, *args, **kwargs)
        self.state_dict = {None: 'plant'}


class Butterfly(GardenAvatar):
    def __init__(self, texture_group, batch, *args, **kwargs):
        super(Butterfly, self).__init__(texture_group, batch, *args, **kwargs)
        self.state_dict = {None: 'butterfly'}
