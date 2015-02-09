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
        self.first_gids = []
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
        """Load .json file containing Level information, typically composed of multiple tile and object layers.
            Build dictionary relating graphic object id ("gid" in .json) to TextureGroup and tex_coords.
        :return:
        """
        with pyglet.resource.file(self.json_name, 'r') as fh:
            self.json = json.load(fh)
        # load textures
        for tileset in self.json['tilesets']:
            self.first_gids.append(tileset['firstgid'])
            spacing = tileset['spacing']
            rows = (tileset['imageheight'] + spacing) / (self.json['tileheight'] + spacing)
            columns = (tileset['imagewidth'] + spacing) / (self.json['tilewidth'] + spacing)
            img = pyglet.resource.image(tileset['image'])
            # use padding specified by "spacing" property of tileset in .json
            img_grid = pyglet.image.ImageGrid(img, rows, columns, row_padding=spacing, column_padding=spacing)
            self.tex_grids.append(pyglet.image.TextureGrid(img_grid))
            self.texture_groups.append(pyglet.graphics.TextureGroup(self.tex_grids[-1].texture))

    def make_layers(self):
        """Create layers (CompositeAvatar) and populate with Tiles (Avatar2D). Layers are ordered along the z-axis from
            bottom to top.
        :return:
        """
        for z, layer in enumerate(self.json['layers']):
            # json layers ordered from bottom to top
            self.layer_types[layer['type']](layer, z / 10.)
            # higher level code needs to add layers (CompositeAvatar) to engine

    def make_objectgroup(self, layer, z):
        """Creates Tiles from elements in object layer, which can be rotated and positioned arbitrarily.
        :param layer: .json node corresponding to object layer
        :param z: height at which to position Tiles
        :return:
        """
        # loop through tiles, filling out layer.avatar_list
        layer_avatar = pyre.agent.CompositeAvatar(self.batch)
        for obj in layer['objects']:
            position = [obj['x'], -obj['y'], z]
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
        """Create Tiles (subclass of Avatar2D) and attach to CompositeAvatar representing layer. Tile vertex
            transformation is cached, so Tile.pre_calc_flag needs to be set to False for Tile update position properly.
        :param layer: .json node corresponding to tile layer
        :param z: height at which to position Tiles
        :return:
        """
        position, vertices = self.pre_calc_tile_vertices(z=z)
        # loop through tiles, filling out layer.avatar_list
        layer_avatar = pyre.agent.CompositeAvatar(self.batch)
        for idx, gid in enumerate(layer['data']):
            texture_group, tex_coords = self.tex_info[gid]
            # gid=0 correspond to texture_group=None (empty tile)
            if texture_group is not None:
                new_tile = Tile(self.batch, position=position[idx, :],
                                tex_dict={None: self.tex_info[gid]},
                                layer=layer_avatar,
                                translate_first=True,
                                size=(self.json['tilewidth'], self.json['tileheight'], 1.),
                                rectangle_vertices_pre_calc=vertices[idx * 4:(idx + 1) * 4, :])
                layer_avatar.avatar_list.append(new_tile)
        self.layers.append(layer_avatar)

    def pre_calc_tile_vertices(self, z=0):
        """When creating Tiles for layer, transform vertices using efficient matrix operations
            rather than one at a time. For ~10,000 tiles per layer, saves several seconds of loading time.
        :return tuple: position and
        """
        num_tiles = self.json['width'] * self.json['height']
        vertices = np.tile(SQUARE_VERTICES, (num_tiles, 1))
        # apply tile transformation first, then layer
        idx = np.matrix(np.repeat(range(num_tiles), 4, 0))
        position = np.concatenate((idx % self.json['width'], -idx / self.json['width'], np.zeros(idx.shape) + z),
                                  axis=0).T
        position = np.multiply(position, (np.array([self.json['tilewidth'], self.json['tileheight'], 1.])))
        dummy_coordinate = pyre.engine.Coordinate(position=position,
                                                  size=(self.json['tilewidth'], self.json['tileheight'], 1.),
                                                  translate_first=True,
                                                  center_flag=False)
        vertices = dummy_coordinate.transform(vertices)
        vertices = self.coordinate.transform(vertices)

        return position[::4, :], vertices

    def update_avatar(self):
        """Updates state of Avatar to reflect Agent. Not implemented for Level.
            :return:
            """

    def initialize_tex_info(self):
        """Tiled Editor indexes tiles from top left across rows, starting from 0.
            :return tuple:
            """
        # gid is a unique identifier for tile in one of the level's textures, indexed from 1
        # gid=0 indicates empty tile
        for texture_group, tex_grid, first_gid in zip(self.texture_groups, self.tex_grids, self.first_gids):
            gid = first_gid
            for row in range(tex_grid.rows):
                for col in range(tex_grid.columns):
                    flipped_row = tex_grid.rows - row - 1
                    tex_coords = tex_grid[flipped_row, col].tex_coords
                    tex_coords = np.delete(np.array(tex_coords), np.s_[2::3])
                    self.tex_info[gid] = (texture_group, tex_coords)
                    gid += 1


class Tile(pyre.agent.Avatar2D):
    def __init__(self, batch, center_flag=False, translate_first=False,
                 layer=None, rectangle_vertices_pre_calc=None, *args, **kwargs):
        """Subclass of Avatar2D representing Tile within layer. Location determined by composition of layer and self
            Coordinate (transforming layer moves contained Tiles together).
        :param pyglet.graphics.Batch batch:
        :param bool center_flag: passed to self Coordinate
        :param translate_first: passed to self Coordinate
        :param layer: parent layer (CompositeAvatar)
        :param rectangle_vertices_pre_calc: pre-cached transformed vertices, disable with pre_calc_flag
        :return:
        """
        super(Tile, self).__init__(batch, *args, **kwargs)
        self.coordinate.center_flag = center_flag
        self.coordinate.translate_first = translate_first
        self.layer = layer
        self.rectangle_vertices_pre_calc = rectangle_vertices_pre_calc
        self.pre_calc_flag = False if rectangle_vertices_pre_calc is None else True
        """:type: pyre.agent.CompositeAvatar"""

    def rectangle_vertices(self):
        """Applies coordinate transform with Tile Coordinate, then Layer Coordinate.
        :return:
        """
        if self.pre_calc_flag:
            return self.rectangle_vertices_pre_calc.flatten()
        vertices = self.coordinate.transform(SQUARE_VERTICES)
        return self.layer.coordinate.transform(vertices).flatten()
