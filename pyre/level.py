import json
import numpy as np
from pyglet.gl import GL_QUADS
import pyglet.resource
import pyglet.graphics
import pyre.engine
import pyre.agent

# Level could inherit directly from pyglet Group, or it could be related to World

SQUARE_VERTICES = pyre.agent.SQUARE_VERTICES


class Level(pyre.agent.PhysicalAgent):
    def __init__(self, json_name, center_level_flag=False, *args, **kwargs):
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
            :param bool center_level_flag: ignore x,y position; instead center level at origin
            :return:
            """
        super(Level, self).__init__(*args, **kwargs)
        self.json_name = json_name
        self.json = {}
        self.texture_groups = []
        self.tex_grids = []
        self.load_json()
        self.tex_info = {0: (None, None)}  # gid=0 indicates empty tile
        self.initialize_tex_info()
        if center_level_flag:
            self.position = self.center(self.position)
        self.coordinate = pyre.engine.Coordinate(position=self.position,
                                                 rotation=self.rotation,
                                                 scale=self.scale,
                                                 center_flag=False)
        self.layers = []
        """:type: list[CompositeAvatar]"""
        self.layer_types = {'tilelayer': self.make_tilelayer,
                            'objectgroup': self.make_objectgroup}
        self.make_layers()
        # top CompositeAvatar, contains CompositeAvatar for each layer
        self.avatar = pyre.agent.CompositeAvatar(self.batch, avatar_list=self.layers)
        self.avatar.coordinate = self.coordinate
        for layer in self.layers:
            layer.coordinate = self.avatar.coordinate

    def center(self, position):
        return np.array([-self.scale * self.json['width'] * self.json['tilewidth'] / 2,
                         self.scale * self.json['height'] * self.json['tileheight'] / 2,
                         position[2]])

    def load_json(self):
        with pyglet.resource.file(self.json_name, 'r') as fh:
            self.json = json.load(fh)
        # load textures
        for tileset in self.json['tilesets']:
            spacing = tileset['spacing']
            height = (tileset['imageheight'] + spacing) / (self.json['tileheight'] + spacing)
            width = (tileset['imagewidth'] + spacing) / (self.json['tilewidth'] + spacing)
            img = pyglet.resource.image(tileset['image'])
            img_grid = pyglet.image.ImageGrid(img, height, width, row_padding=spacing, column_padding=spacing)
            self.tex_grids.append(pyglet.image.TextureGrid(img_grid))
            self.texture_groups.append(pyglet.graphics.TextureGroup(self.tex_grids[-1].texture))

    def make_layers(self):
        for z, layer in enumerate(self.json['layers']):
            # json layers ordered from bottom to top
            self.layer_types[layer['type']](layer, z / 10)
            # higher level code needs to add layers (CompositeAvatar) to engine

    def make_objectgroup(self, layer, z):
        # loop through tiles, filling out layer.avatar_list
        layer_avatar = pyre.agent.CompositeAvatar(self.batch)
        for obj in layer['objects']:
            position = [obj['x'], -obj['y'], 0.]
            rotation = np.array([0., 0., obj['rotation']])
            # TODO handle scaling, currently not in json
            if 'gid' in obj.keys():
                new_tile = Tile(self.batch,
                                position=position, rotation=rotation,
                                tex_dict={None: self.tex_info[obj['gid']]},
                                layer=layer_avatar,
                                size=(self.json['tilewidth'], self.json['tileheight'], 1.))
                layer_avatar.avatar_list.append(new_tile)
        self.layers.append(layer_avatar)

    def make_tilelayer(self, layer, z):
        # loop through tiles, filling out layer.avatar_list
        layer_avatar = pyre.agent.CompositeAvatar(self.batch)
        for idx, gid in enumerate(layer['data']):
            # idx is a linear index for row-major matrix, starting from 0
            position = np.array([idx % self.json['width'], -(idx / self.json['width']), 0.]) * \
                       [self.json['tilewidth'], self.json['tileheight'], 0]
            texture_group, tex_coords = self.tex_info[gid]
            # gid=0 correspond to texture_group=None (empty tile)
            if texture_group is not None:
                new_tile = Tile(self.batch, position=position,
                                tex_dict={None: self.tex_info[gid]},
                                layer=layer_avatar,
                                translate_first=True,
                                size=(self.json['tilewidth'], self.json['tileheight'], 1.))
                layer_avatar.avatar_list.append(new_tile)
        self.layers.append(layer_avatar)

    def show(self):
        self.avatar.show()

    def hide(self):
        self.avatar.hide()

    def update_avatar(self):
        """Updates state of Avatar to reflect Agent.
            :return:
            """

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


class Tile(pyre.agent.Avatar2D):
    def __init__(self, batch, center_flag=False, translate_first=False,
                 layer=None, *args, **kwargs):
        super(Tile, self).__init__(batch, *args, **kwargs)
        self.coordinate.center_flag = center_flag
        self.coordinate.translate_first = translate_first
        self.layer = layer
        """:type: pyre.agent.CompositeAvatar"""

    def rectangle_vertices(self):
        """Applies coordinate transform with Tile Coordinate, then Layer Coordinate.
        :return:
        """
        vertices = self.coordinate.transform(SQUARE_VERTICES)
        return self.layer.coordinate.transform(vertices).flatten()

