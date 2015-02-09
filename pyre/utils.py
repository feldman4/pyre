import numpy as np
import rpyc.utils.server
import threading


class Coordinate(object):
    def __init__(self, position=None, rotation=None, scale=1, size=None,
                 center_flag=True, translate_first=False):
        """
        :param position:
        :param rotation:
        :param scale: applied uniformly
        :param size: like scale, but applied to each dimension
        :param center_flag: translate centroid of vertices to (0, 0, 0) before transform
        :param translate_first: translate before rotating
            (useful if vertices are part of a larger rigid body)
        :return:
        """
        self.position = np.array([0., 0., 0.]) if position is None else position
        self.rotation = np.array([0., 0., 0.]) if rotation is None else rotation
        self.size = np.array([1., 1., 1.]) if size is None else size
        self.scale = scale
        self.center_flag = center_flag
        self.translate_first = translate_first

    def transform(self, vertices):
        """Apply scaling then translation then rotation.
        If center_flag=True, scales from centroid of vertices.
        If translate_first=True, moves to scaled position, then rotates.
        :param numpy.array vertices:
        :param bool center_flag:
        :param bool translate_first:
        :return:
        """
        vertices = np.array(vertices)
        if self.center_flag:
            vertices = vertices - vertices.sum(0) / vertices.shape[0]
        vertices *= self.scale * self.size
        if self.translate_first:
            vertices = self.rotate_vertices(vertices + self.position*self.scale, self.rotation)
        else:
            vertices = self.rotate_vertices(vertices, self.rotation) + self.position
        return vertices

    def rotate_vertices(self, vertices, rotation):
        """Rotate numpy array of vertices using [x,y,z] rotation angles provided in rotation
        :param vertices:
        :param rotation:
        :return:x
        """
        r = self.rotation_matrix(rotation)
        return r['z'].dot(r['y'].dot(r['x'])).dot(vertices.T).T

    @staticmethod
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


class IncrementSet(set):
    """set that supports +=, -= with items or lists, crappy
    """
    def __add__(self, other):
        try:
            other = set(other)
        except TypeError:
            other = {other}
        return self.union(other)

    def __sub__(self, other):
        try:
            other = set(other)
        except TypeError:
            other = {other}
        return self.difference(other)


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