import json
import numpy as np
from pyglet.gl import GL_QUADS
import pyglet.resource
import pyglet.graphics
import pyre.engine
import pyre.agent

# Level could inherit directly from pyglet Group, or it could be related to World

SQUARE_VERTICES = pyre.agent.SQUARE_VERTICES


class Level(object):
    def __init__(self, json_name, position=None, rotation=None, batch=None,
                 scale=0.03, center_flag=False):
        """Loads information contained in .json exported by Tiled Editor. Creates TextureGroups for referenced tilesets,
            as well as dict mapping .json gid (graphic id) to (TextureGroup, tex_coords).
            Creates a Layer for each layer in .json file, preserving draw order via z-coordinate. The entire Level can
            be positioned, rotated and scaled. Assumes 1 pixel padding in tileset. Supports freely located tiles from
            Tiled Editor object layers.
        :param str json_name: Level data filename, uses pyglet.resource so path need not be specified
        :param numpy.array position: (x, y, z), applied to all Layers in Level
        :param numpy.array rotation: applied to Layer from top left corner, before translating by position
        :param pyglet.graphics.Batch batch: all Layers add VertexLists to this Batch
        :param float scale: uniform, scale=1 means 1 px in texture:1 OpenGL unit
        :param bool center_flag: ignore x,y position; instead center level at origin
        :return:
        """
        self.json_name = json_name
        self.position = np.array([0., 0., 0.]) if position is None else position
        self.rotation = np.array([0., 0., 0.]) if rotation is None else rotation
        self.scale = scale
        self.textures = []
        self.texture_groups = []
        self.tex_grids = []
        self.layers = []
        """:type: list[Layer]"""
        self.top_layer = Layer({}, {}, {})
        # 0 indicates empty tile
        self.tex_info = {0: (None, None)}
        self.json = None
        self.batch = batch
        self.layer_types = {'tilelayer': TileLayer,
                            'objectgroup': ObjectLayer}

        self.center_flag = center_flag
        self.load_json()
        self.initialize_tex_info()

    def center(self):
        self.position = np.array([-self.scale * self.json['width'] * self.json['tilewidth'] / 2,
                                  self.scale * self.json['height'] * self.json['tileheight'] / 2,
                                  self.position[2]])

    def load_json(self):
        self.textures = []
        self.texture_groups = []
        with pyglet.resource.file(self.json_name, 'r') as fh:
            self.json = json.load(fh)
        if self.center_flag:
            self.center()
        # load textures
        for tileset in self.json['tilesets']:
            height = tileset['imageheight'] / self.json['tileheight']
            width = tileset['imagewidth'] / self.json['tilewidth']
            img = pyglet.resource.image(tileset['image'])
            img_grid = pyglet.image.ImageGrid(img, height, width, row_padding=1, column_padding=1)
            self.tex_grids.append(pyglet.image.TextureGrid(img_grid))
            self.texture_groups.append(pyglet.graphics.TextureGroup(self.tex_grids[-1].texture))

        for z, layer in enumerate(self.json['layers']):
            # json layers ordered from bottom to top
            layer_make = self.layer_types[layer['type']]
            self.layers.append(layer_make(layer, self.json, self.tex_info,
                                          position=np.array([0., 0., z/10]) + self.position,
                                          scale=self.scale,
                                          batch=self.batch))

    def show(self):
        for layer in self.layers:
            layer.show()

    def hide(self):
        for layer in self.layers:
            layer.hide()

    def initialize_tex_info(self):
        """Tiled Editor indexes tiles from top left across rows, starting from 0.
        :return tuple:
        """
        # gid is a unique identifier for tile in one of the level's textures, indexed from 1
        # gid=0 indicates empty tile
        gid = 0
        for texture_group, tex_grid in zip(self.texture_groups, self.tex_grids):
            for row in range(tex_grid.rows):
                for col in range(tex_grid.columns):
                    gid += 1
                    flipped_row = tex_grid.rows - row - 1
                    tex_coords = tex_grid[flipped_row, col].tex_coords
                    tex_coords = np.delete(np.array(tex_coords), np.s_[2::3])
                    self.tex_info[gid] = (texture_group, tex_coords)


class Layer(dict):
    def __init__(self, layer_json, map_json, tex_info, scale=1.,
                 position=None, rotation=None, batch=None, **kwargs):
        """Represents a layer drawn at a single height. Combines information from map and layer in .json into dict
            structure. Can be individually shown and hidden. Inherits position, rotation and scale from parent Level.
        :param dict layer_json: layer dict loaded from .json
        :param dict map_json: map dict (top level) from .json
        :param dict tex_info: dict assembled by Level, maps .json gid (graphic id) to (TextureGroup, tex_coords)
        :param float scale:
        :param numpy.array position:
        :param numpy.array rotation:
        :param pyglet.graphics.Batch batch:
        :param kwargs:
        :return:
        """
        super(Layer, self).__init__(**kwargs)

        json_keys = ['tilewidth', 'tileheight']
        layer_keys = ['height', 'width', 'x', 'y', 'name', 'opacity', 'type', 'data', 'objects']
        # gratuitous if statement so Layer({}, {}, {}) works for UML hierarchy
        self.update({key: map_json[key] for key in json_keys if key in map_json})
        for key in layer_keys:
            try:
                self.update({key: layer_json[key]})
            except KeyError:
                pass

        self.tex_info = tex_info
        self.batch = batch
        self.position = np.array([0., 0., 0.]) if position is None else position
        self.rotation = np.array([0., 0., 0.]) if rotation is None else rotation
        self.scale = scale

        self.vertex_lists = []

    def show(self):
        pass

    def tile_vertices(self, offset, tile_rotation=None):
        """Applies tile offset and scaling, then rotates, then translates by
            Layer position
        :param offset:
        :return:
        """
        vertices = np.array(SQUARE_VERTICES * [self['tilewidth'], self['tileheight'], 1])
        if tile_rotation is not None:
            vertices = pyre.agent.rotate_vertices(vertices, tile_rotation)
        return np.array(pyre.agent.rotate_vertices(
            (vertices + offset) * self.scale + self.position, self.rotation)).flatten()

    def hide(self):
        for entry in self.vertex_lists:
            entry.delete()


class TileLayer(Layer):
    def __init__(self, layer_json, map_json, tex_info, batch=None, **kwargs):
        super(TileLayer, self).__init__(layer_json, map_json, tex_info, batch=batch, **kwargs)

    def show(self):
        for idx, gid in enumerate(self['data']):
            # idx is a linear index for row-major matrix, starting from 0
            offset = np.array([idx % self['width'], -(idx / self['width']), 0.]) * \
                     [self['tilewidth'], self['tileheight'], 0]
            texture_group, tex_coords = self.tex_info[gid]
            if texture_group is not None:
                vertex_data = self.tile_vertices(offset)
                self.vertex_lists.append(self.batch.add(4, GL_QUADS, texture_group,
                                                        ('v3f', vertex_data), ('t2f', tex_coords)))


class ObjectLayer(Layer):
    def __init__(self, layer_json, map_json, tex_info, batch=None, **kwargs):
        super(ObjectLayer, self).__init__(layer_json, map_json, tex_info, batch=batch, **kwargs)

    def show(self):
        for obj in self['objects']:
            # idx is a linear index for row-major matrix, starting from 0
            offset = [obj['x'], -obj['y'], 0.]
            rotation = np.array([0., 0., obj['rotation']])
            # TODO handle scaling, currently not in json
            if 'gid' in obj.keys():
                texture_group, tex_coords = self.tex_info[obj['gid']]
                vertex_data = self.tile_vertices(offset, tile_rotation=rotation)
                self.vertex_lists.append(self.batch.add(4, GL_QUADS, texture_group,
                                                        ('v3f', vertex_data), ('t2f', tex_coords)))