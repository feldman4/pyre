# noinspection PyUnresolvedReferences
from agent import Spin, Agent
from garden import Worm


class AI(object):
    def __init__(self, agent):
        """

        :param Agent agent:
        :return:
        """
        self.agent = agent
        self.t = agent.t
        """ AI time tracks Agent time """
    def update(self, dt):
        self.t += dt


class GameOfLife(AI):
    def __init__(self, spin):
        """

        :param Spin spin:
        :return:
        """
        super(GameOfLife, self).__init__(spin)
        self.agent = spin
        """:type: Spin"""

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

