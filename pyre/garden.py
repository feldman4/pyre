import math
import random
from pyglet.gl import GL_QUADS
from agent import Agent, Avatar
import numpy as np
from pyre.ai import AI
import pyre.agent

# TODO move Worm functionality to PhysicalAgent or somesuch, same for SquareAvatar from GardenAvatar


class Worm(Agent):
    def __init__(self, initial_state='slug', position=np.array([0., 0., 0.]), rotation=np.array([0., 0., 0.]),
                 angular_velocity=np.array([0., 0., 0.]), color=(255, 0, 0), speed=0, lifetime=10,
                 *args, **kwargs):
        """
        Its lifecycle has four states.
        :param string initial_state:
        :param tuple color: an RGB tuple, e.g., (255, 0, 0)
        :param args:
        :param kwargs:
        :return:
        """
        super(Worm, self).__init__(*args, **kwargs)
        self.position = position
        self.rotation = rotation
        self.angular_velocity = angular_velocity
        self.state = initial_state
        self.lifetime = lifetime
        self.color = color
        self.avatar = self.guises[self.state]
        self.update_avatar()
        self.lifecycle = ['butterfly', 'seed', 'plant', 'slug']
        self.speed = speed

    def evolve(self):
        self.state = self.lifecycle[(self.lifecycle.index(self.state) + 1) % len(self.lifecycle)]
        self.state = 'butterfly'
        self.avatar.hide()
        self.avatar = self.guises[self.state]
        if self.state == 'butterfly':
            self.swap_ai(ButterflyAI)
            # remember butterfly rotation
            self.rotation = self.avatar.rotation
        if self.state != 'butterfly':
            self.swap_ai(WormAI)
            self.rotation = np.array([0., 0., 0.])
            self.angular_velocity = np.array([0., 0., 0.])


class GardenAvatar(Avatar):
    def __init__(self, texture_group, batch, rotation=np.array([0., 0., 0.]),
                 size=(1, 1, 1), color=(255, 0, 0), *args, **kwargs):
        """
            Parent class for garden-variety Avatars.
            :param color:
            :return:
            """
        super(GardenAvatar, self).__init__(texture_group, batch, *args, **kwargs)
        self.color = color
        self.size = size
        self.rotation = rotation
        self.SQUARE_VERTICES = [[0, 0, 0],
                                [1, 0, 0],
                                [1, 1, 0],
                                [0, 1, 0]]

    def square_vertices(self):
        vertices = np.array(self.SQUARE_VERTICES)
        vertices = np.array((vertices - 0.5) * self.size)
        vertices = pyre.agent.rotate_vertices(vertices, self.rotation) + self.position
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


class WormAI(AI):
    def __init__(self, worm, lifetime=1, *args, **kwargs):
        super(WormAI, self).__init__(worm, *args, **kwargs)
        self.last_evolved_t = self.t
        self.lifetime = lifetime

    def update(self, dt):
        super(WormAI, self).update(dt)
        if self.t - self.last_evolved_t > self.lifetime:
            self.agent.evolve()
            self.last_evolved_t = self.t


class ButterflyAI(WormAI):
    def __init__(self, worm, k_theta=0.5, noise_theta=0., sine_amp_theta=0.02,
                 sine_period_theta=2, *args, **kwargs):
        """

        :param Worm worm: agent controlled by AI
        :param float k_theta: rate of relaxation of noise-induced momentum
        :param float sine_amp_theta: amplitude of steady sinusoidal rotation
        :param float sine_T_theta: period of steady sinusoidal rotation
        :param float noise_theta: amplitude of noise changing momentum
        :return:
        """
        super(ButterflyAI, self).__init__(worm, *args, **kwargs)
        self.k_theta = k_theta
        self.noise_theta = noise_theta
        self.sine_amp_theta = sine_amp_theta
        self.sine_period_theta = sine_period_theta

    def update(self, dt):
        """
        Butterfly moves based on orientation. Orientation changes as a sum of sinusoid and
         "orientation momentum" which changes randomly but relaxes towards zero.
        :param dt:
        :return:
        """

        self.agent.angular_velocity[2] += dt * self.sine_amp_theta * math.sin(self.t / self.sine_period_theta)
        self.agent.angular_velocity[2] += self.noise_theta * dt * (random.random() - 0.5)
        self.agent.angular_velocity += -1 * self.agent.angular_velocity * dt * self.k_theta
        # depends on the direction considered forward, assume x axis
        self.agent.position += self.agent.speed * pyre.agent.rotate_vertices(np.eye(3), self.agent.rotation).sum(1)
        super(ButterflyAI, self).update(dt)
        print pyre.agent.rotate_vertices(np.eye(3), self.agent.rotation).sum(1)

