import math

import numpy as np
from pyglet.gl import *
from pyglet.window import key

import pyre.world


class Engine(object):
    def __init__(self, window=None):
        self.t = 0
        self.top_world = pyre.world.World()
        self.levels = []
        self.world_mesh = {}
        self.agents_update = True
        # modifies the dt passed from Window
        self.timing_fcn = lambda x: x
        self.go = False

        self.window = window
        self.batch = pyglet.graphics.Batch()
        self.player = Player()

    def update(self, dt):
        dt = self.timing_fcn(dt)
        self.t += dt
        self.top_world.update(dt)
        self.player.update(dt)
        self.window.position = self.player.position
        self.window.rotation = self.player.rotation

    def draw(self):
        self.batch.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        self.player.on_mouse_motion(x, y, dx, dy)

    def on_key_press(self, symbol, modifiers):
        self.player.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        self.player.on_key_release(symbol, modifiers)

    def show_levels(self):
        for level in self.levels:
            level.show()


class Player(object):
    def __init__(self, position=(0., 0., 8.), rotation=(0., 0.), mouse_velocity=0.15,
                 flying_speed=15):
        """Processes key and mouse input and updates camera position and rotation accordingly.
        :param Engine engine:
        :param tuple position: (x, y, z) position of camera
        :param tuple rotation: (theta, phi) rotation of camera
        :return:
        """
        self.position = np.array(position)
        self.rotation = np.array(rotation)
        self.mouse_velocity = mouse_velocity
        self.strafe = [0, 0]
        self.flying_speed = flying_speed

    def update(self, dt):
        """ Private implementation of the `update()` method. This is where most
        of the motion logic lives, along with gravity and collision detection.
        """
        self.position += self.get_motion_vector() * dt * self.flying_speed

    def get_motion_vector(self):
        pass

    def on_mouse_motion(self, x, y, dx, dy):
        pass

    def on_key_press(self, symbol, modifiers):

        if symbol == key.W:
            self.strafe[0] -= 1
        elif symbol == key.S:
            self.strafe[0] += 1
        elif symbol == key.A:
            self.strafe[1] -= 1
        elif symbol == key.D:
            self.strafe[1] += 1

    def on_key_release(self, symbol, modifiers):

        if symbol == key.W:
            self.strafe[0] += 1
        elif symbol == key.S:
            self.strafe[0] -= 1
        elif symbol == key.A:
            self.strafe[1] += 1
        elif symbol == key.D:
            self.strafe[1] -= 1


class FreePlayer(Player):
    def __init__(self, *args, **kwargs):
        super(FreePlayer, self).__init__(*args, **kwargs)

    def get_motion_vector(self):
        """Returns the current motion vector indicating the velocity of the
        player.
        :return: Tuple containing camera velocity in x, y, z
        """
        dx, dy, dz = 0.0, 0.0, 0.0
        if any(self.strafe):
            x, y = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            y_angle = math.radians(y)
            x_angle = math.radians(x + strafe)
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

        return np.array([dx, dy, dz])

    def on_mouse_motion(self, x, y, dx, dy):
        super(FreePlayer, self).on_mouse_motion(x, y, dx, dy)
        self.rotation += np.array([dx, dy]) * self.mouse_velocity
        self.rotation[1] = max(-90, min(90, self.rotation[1]))


class RTSPlayer(Player):
    def get_motion_vector(self):
        return np.array([self.strafe[1], -self.strafe[0], 0])


class Window(pyglet.window.Window):
    def __init__(self, engine=Engine(), *args, **kwargs):

        super(Window, self).__init__(*args, **kwargs)

        self.TICKS_PER_SEC = 60

        # overwritten to refer to Player attributes
        self.position = np.array((0, 0, 0))
        self.rotation = np.array((0, 0))

        self.exclusive = False
        """ whether mouse is captured """

        self.engine = engine

        # This call schedules the `update()` method to be called
        # TICKS_PER_SEC. This is the main game event loop.
        pyglet.clock.schedule_interval(self.update, 1.0 / self.TICKS_PER_SEC)

    def update(self, dt):
        self.engine.update(dt)

    def set_exclusive_mouse(self, exclusive=True):
        """ If `exclusive` is True, the game will capture the mouse, if False
        the game will ignore the mouse.
        """
        super(Window, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive

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
        """Passes the position and motion of mouse to Engine.
        """
        if self.exclusive:
            self.engine.on_mouse_motion(x, y, dx, dy)

    def on_key_press(self, symbol, modifiers):
        """Called when the player presses a key. See pyglet docs for key mappings.
        :param int symbol: number representing the key that was pressed
        :param int modifiers: number representing any modifying keys that were pressed
        :return:
        """
        if symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
        self.engine.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        """Called when the player releases a key. See pyglet docs for key mappings.
        :param int symbol: number representing the key that was pressed
        :param int modifiers: number representing any modifying keys that were pressed
        :return:
        """
        self.engine.on_key_release(symbol, modifiers)

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

    def set_clear_color(self, color):
        glClearColor(color)

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
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # glBlendFunc(GL_SRC_ALPHA_SATURATE, GL_ONE)

        glAlphaFunc(GL_GREATER, 0.1)
        glEnable(GL_ALPHA_TEST)

    def run(self):
        pyglet.app.run()


def tex_coord(position, m=4, n=4, flip_y=False):
    """Returns the bounding vertices of a square inside Texture.
    :param tuple|list position: standard (x,y) coordinate within Texture
    :param int m: number of images along width
    :param int n: number of images along height
    :return:
    """
    tile_width = 1.0 / m
    tile_height = 1.0 / n
    dx = position[0] * tile_width
    dy = position[1] * tile_height
    if flip_y:
        dy = 1.0 - dy - tile_height
    return dx, dy, dx + tile_width, dy, dx + tile_width, dy + tile_height, dx, dy + tile_height


def main():
    window = Window(width=800, height=600, caption='Pyglet', resizable=True)
    window.run()


if __name__ == '__main__':
    main()