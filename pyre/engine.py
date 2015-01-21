import math
import threading
import numpy as np
import rpyc.utils.server
from agent import Agent
from pyglet.gl import *
from pyglet.window import key


class Engine(object):
    def __init__(self):
        self.t = 0
        self.junk = None
        self.agents = []
        """:type: list[Agent]"""
        self.world_mesh = {}
        self.agents_update = True
        # modifies the dt passed from Window
        self.timing_fcn = lambda x: x
        self.go = False

        self.batch = pyglet.graphics.Batch()

    def add_agent(self, agent):
        """This adds agents.

        :param Agent agent: this is an agent
        """
        self.agents.append(agent)

    def step(self):
        self.go = True

    def latch_timer(self, dt):
        if self.go:
            self.go = False
            return dt
        return 0

    def update(self, dt):
        dt = self.timing_fcn(dt)
        self.t += dt
        if self.agents_update:
            for agent in self.agents:
                agent.update(dt)
            # print "time: {}, position: {}, w: {}".format(self.agents[0].t,self.agents[0].rotation, self.agents[0].angular_velocity)

    def draw(self):
        self.batch.draw()


class Window(pyglet.window.Window):
    def __init__(self, engine=Engine(), *args, **kwargs):

        super(Window, self).__init__(*args, **kwargs)

        self.TICKS_PER_SEC = 60
        self.FLYING_SPEED = 15

        self.exclusive = False
        """ whether mouse is captured """

        self.flying = True

        self.position = (0, 0, 0)
        """ (x,y,z) position of camera """

        self.rotation = (0, 0)
        """ (theta, phi) rotation of camera """

        self.strafe = [0, 0]

        self.engine = engine

        # This call schedules the `update()` method to be called
        # TICKS_PER_SEC. This is the main game event loop.
        pyglet.clock.schedule_interval(self.update, 1.0 / self.TICKS_PER_SEC)

    def update(self, dt):
        self.engine.update(dt)
        self._update(dt)

    def _update(self, dt):
        """ Private implementation of the `update()` method. This is where most
        of the motion logic lives, along with gravity and collision detection.

        Parameters
        ----------
        dt : float
            The change in time since the last call.

        """
        # walking
        speed = self.FLYING_SPEED
        d = dt * speed  # distance covered this tick.
        dx, dy, dz = self.get_motion_vector()
        # New position in space, before accounting for gravity.
        dx, dy, dz = dx * d, dy * d, dz * d
        self.position = tuple(np.array(self.position) + [dx, dy, dz])

    def set_exclusive_mouse(self, exclusive=True):
        """ If `exclusive` is True, the game will capture the mouse, if False
        the game will ignore the mouse.

        """
        super(Window, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive

    def get_motion_vector(self):
        """ Returns the current motion vector indicating the velocity of the
        player.

        Returns
        -------
        vector : tuple of len 3
            Tuple containing the velocity in x, y, and z respectively.

        """
        dx, dy, dz = 0.0, 0.0, 0.0
        if any(self.strafe):
            x, y = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            y_angle = math.radians(y)
            x_angle = math.radians(x + strafe)
            if self.flying:
                m = math.cos(y_angle)
                dy = math.sin(y_angle)
                if self.strafe[1]:
                    # Moving left or right.
                    dy = 0.0
                    m = 1
                if self.strafe[0] > 0:
                    # Moving backwards.
                    dy *= -1
                # When you are flying up or down, you have less left and right
                # motion.
                dx = math.cos(x_angle) * m
                dz = math.sin(x_angle) * m

        return dx, dy, dz

    def on_mouse_press(self, x, y, button, modifiers):
        """Called when a mouse button is pressed.

        :param x:
        :param y:
        :param button:
        :param modifiers:
        :return:
        """
        if not self.exclusive:
            self.set_exclusive_mouse(True)

    def on_mouse_motion(self, x, y, dx, dy):
        """

        :param x:
        :param y:
        :param dx:
        :param dy:
        :return:
        """
        if self.exclusive:
            m = 0.15
            x, y = self.rotation
            x, y = x + dx * m, y + dy * m
            y = max(-90, min(90, y))
            self.rotation = (x, y)

    def on_key_press(self, symbol, modifiers):
        """ Called when the player presses a key. See pyglet docs for key
        mappings.

        Parameters
        ----------
        symbol : int
            Number representing the key that was pressed.
        modifiers : int
            Number representing any modifying keys that were pressed.

        """
        if symbol == key.W:
            self.strafe[0] -= 1
        elif symbol == key.S:
            self.strafe[0] += 1
        elif symbol == key.A:
            self.strafe[1] -= 1
        elif symbol == key.D:
            self.strafe[1] += 1
        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
        elif symbol == key.TAB:
            self.flying = not self.flying

    def on_key_release(self, symbol, modifiers):
        """ Called when the player releases a key. See pyglet docs for key
        mappings.

        Parameters
        ----------
        symbol : int
            Number representing the key that was pressed.
        modifiers : int
            Number representing any modifying keys that were pressed.

        """
        if symbol == key.W:
            self.strafe[0] += 1
        elif symbol == key.S:
            self.strafe[0] -= 1
        elif symbol == key.A:
            self.strafe[1] += 1
        elif symbol == key.D:
            self.strafe[1] -= 1

    def set_3d(self):
        """ Configure OpenGL to draw in 3d.

        """
        width, height = self.get_size()
        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65.0, width / float(height), 0.1, 60.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y = self.rotation
        glRotatef(x, 0, 1, 0)
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))
        x, y, z = self.position
        glTranslatef(-x, -y, -z)

    def on_draw(self):
        """ Called by pyglet to draw the canvas.

        """
        self.clear()
        self.set_3d()
        glColor3d(1, 1, 1)
        self.engine.draw()

    def setup(self):
        """ Basic OpenGL configuration.

        """
        # Set the color of "clear", i.e. the sky, in rgba.
        glClearColor(0.5, 0.69, 1.0, 1)
        # Enable culling (not rendering) of back-facing facets -- facets that aren't
        # visible to you.
        # glEnable(GL_CULL_FACE)
        # Set the texture magnification function to GL_NEAREST (nearest
        # in Manhattan distance) to the specified texture coordinates. GL_NEAREST
        # "is generally faster than GL_LINEAR, but it can produce textured images
        # with sharper edges because the transition between texture elements is not
        # as smooth."
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        # setup_fog()

    def run(self):
        pyglet.app.run()


def tex_coord(position, n=4):
    """Returns the bounding vertices of a square inside Texture.

    :param tuple|list position: standard (x,y) coordinate within Texture
    :param n: number of images along one side
    :return:
    """
    m = 1.0 / n
    dx = position[0] * m
    dy = position[1] * m
    return dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m

# functions to set up rpyc connection

PORT = 12345
PROTOCOL_CONFIG = {"allow_all_attrs": True,
                   "allow_setattr": True,
                   "allow_pickle": True}


def start_server(window):
    class ServerService(rpyc.Service):
        def exposed_get_window(self):
            return window
    # start the rpyc server
    server = rpyc.utils.server.ThreadedServer(ServerService, port=12345, protocol_config=PROTOCOL_CONFIG)
    t = threading.Thread(target=server.start)
    t.daemon = True
    t.start()


def start_client():
    class ServerService(rpyc.Service):
        pass

    conn = rpyc.connect("localhost", 12345, service=ServerService, config=PROTOCOL_CONFIG)
    rpyc.BgServingThread(conn)
    return conn


def main():
    window = Window(width=800, height=600, caption='Pyglet', resizable=True)
    window.run()

if __name__ == '__main__':
    main()