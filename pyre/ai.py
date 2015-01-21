# noinspection PyUnresolvedReferences
from agent import Spin, Agent


class AI(object):
    def __init__(self, agent, *args, **kwargs):
        """

        :param Agent agent:
        :return:
        """
        self.agent = agent
        self.t = agent.t
        """ AI time tracks Agent time """
        args = 0

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
