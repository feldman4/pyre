import math
import random
import numpy as np
import pyre.ai
import pyre.agent


class Worm(pyre.agent.PhysicalAgent):
    def __init__(self, initial_state='slug', color=(255, 0, 0), butterfly_speed=None,
                 lifecycle={'butterfly', 'seed', 'plant', 'slug'}, lifetimes=None,
                 lifetime_noise=0, *args, **kwargs):
        """An Agent that evolves through lifecycle states with given lifetimes.
        :param string initial_state:
        :param tuple color: an RGB tuple, e.g., (255, 0, 0)
        :param tuple lifecycle: a tuple of states through which the Agent evolves
        :param dict lifetimes: a dictionary mapping lifetimes to lifecycle states
        :param args:
        :param kwargs:
        :return:
        """
        super(Worm, self).__init__(*args, **kwargs)
        self.state = initial_state
        self.color = color
        self.avatar = self.guises[self.state]
        # self.update_avatar()
        self.lifecycle = lifecycle
        self.lifetimes = dict(zip(self.lifecycle), [1] * 4) if lifetimes is None else lifetimes
        self.lifetime = self.lifetimes[self.state]
        self.butterfly_speed = np.array([0., 1., 0.]) if butterfly_speed is None else butterfly_speed
        self.lifetime_noise = lifetime_noise

    def evolve(self):
        self.state = self.lifecycle[(self.lifecycle.index(self.state) + 1) % len(self.lifecycle)]
        self.lifetime = self.lifetimes[self.state]
        self.avatar.hide()
        self.avatar = self.guises[self.state]
        # print id(self.avatar.rotation)
        if self.state == 'butterfly':
            self.swap_ai(ButterflyAI)
            self.ai.lifetime = self.lifetime + random.random() * self.lifetime_noise
        if self.state != 'butterfly':
            self.swap_ai(WormAI)
            self.rotation = np.array([0., 0., 0.])
            self.velocity = np.array([0., 0., 0.])
            self.angular_velocity = np.array([0., 0., 0.])
            self.ai.lifetime = self.lifetime


class GardenAvatar(pyre.agent.Avatar2D):
    pass


class Slug(GardenAvatar):
    def __init__(self, batch, *args, **kwargs):
        super(Slug, self).__init__( batch, *args, **kwargs)
        self.state_dict = {None: 'slug'}


class Seed(GardenAvatar):
    def __init__(self, batch, *args, **kwargs):
        super(Seed, self).__init__(batch, *args, **kwargs)
        self.state_dict = {None: 'seed'}


class Plant(GardenAvatar):
    def __init__(self, batch, *args, **kwargs):
        super(Plant, self).__init__(batch, *args, **kwargs)
        self.state_dict = {None: 'plant'}


class Butterfly(GardenAvatar):
    def __init__(self, batch, *args, **kwargs):
        super(Butterfly, self).__init__(batch, *args, **kwargs)
        self.state_dict = {None: 'butterfly'}


class WormAI(pyre.ai.PhysicalAI):
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
    def __init__(self, worm, k_theta=0.2, noise_theta=0, sine_amp_theta=3,
                 sine_period_theta=1, sine_phase=0, *args, **kwargs):
        """

        :param Worm worm: agent controlled by AI
        :param float k_theta: rate of relaxation of noise-induced momentum
        :param float sine_amp_theta: 1/2 peak-to-peak amplitude of steady sinusoidal rotation, in radians
        :param float sine_T_theta: period of steady sinusoidal rotation
        :param float noise_theta: amplitude of noise changing momentum, in radians
        :param float sine_phase: phase offset of steady sinusoidal rotation, in radians
        :return:
        """
        super(ButterflyAI, self).__init__(worm, *args, **kwargs)
        self.k_theta = k_theta
        self.noise_theta = noise_theta
        self.sine_amp_theta = sine_amp_theta
        self.sine_period_theta = sine_period_theta
        self.sine_phase = sine_phase

    def update(self, dt):
        """
        Butterfly moves based on orientation. Orientation changes as a sum of sinusoid and
         "orientation momentum" which changes randomly but relaxes towards zero.
        :param dt:
        :return:
        """
        # directly rotate without involving angular velocity, easier than keeping track
        self.agent.rotation[2] += dt * self.sine_amp_theta * math.sin(
            2 * math.pi * self.t / self.sine_period_theta + self.sine_phase)
        self.agent.angular_velocity[2] += self.noise_theta * dt * (random.random() - 0.5)
        self.agent.speed = self.agent.butterfly_speed
        super(ButterflyAI, self).update(dt)
        self.agent.position = (self.agent.position + 4) % 8 - 4

