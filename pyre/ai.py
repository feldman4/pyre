# noinspection PyUnresolvedReferences
import pyre.agent
import pyre.engine
import numpy as np
from pyre.utils import Coordinate


class AI(object):
    def __init__(self, agent, *args, **kwargs):
        """An AI evolves an Agent in time.
        :param pyre.agent.Agent agent:
        :return:
        """
        self.agent = agent
        self.t = agent.t
        """ AI time tracks Agent time """

    def update(self, dt):
        self.update_position(dt)
        self.t += dt

    def remove(self):
        """Called when Agent is deleted.
        :return:
        """
        pass

    def update_position(self, dt):
        """Applies velocity and angular velocity of Agent to its position and rotation.
        :param dt:
        :return:
        """
        if self.agent.position is not None and self.agent.velocity is not None:
            self.agent.position += dt * self.agent.velocity
        if self.agent.rotation is not None and self.agent.angular_velocity is not None:
            self.agent.rotation += dt * self.agent.angular_velocity


coordinate = Coordinate()


class PhysicalAI(AI):
    def update_position(self, dt):
        coordinate.center_flag = False
        self.agent.position += dt * coordinate.rotate_vertices(self.agent.speed, self.agent.rotation)
        super(PhysicalAI, self).update_position(dt)
        self.agent.speed = np.array([0., 0., 0.])


class GameOfLife(AI):
    def __init__(self, spin):
        """Controls a Spin with neighbors according to the Game of Life rules.
        :param pyre.agent.Spin spin:
        :return:
        """
        super(GameOfLife, self).__init__(spin)
        self.agent = spin
        """:type: pyre.agent.Spin"""

        self.lifetime = 1
        self.last_flip_t = self.t

    def update(self, dt):
        super(GameOfLife, self).update(dt)

        if self.t - self.last_flip_t > self.lifetime:
            self.decide()
            self.last_flip_t = self.t

    def decide(self):
        """ Implements B2/S/23 update rule.
        :return:
        """
        score = self.agent.neighbor_sum()

        if self.agent.spin & (score < 2 or score > 3):
            self.agent.spin = False
        elif not self.agent.spin & score == 3:
            self.agent.spin = True

        return self.agent.spin
