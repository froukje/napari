"""OctreeIntersection class.
"""
from typing import List, Tuple

import numpy as np

from .octree_level import OctreeLevel
from .octree_util import ChunkData

# TODO_OCTREE: These types might be a horrible idea but trying it for now.
Float2 = np.ndarray  # [x, y] dtype=float64 (default type)


class OctreeIntersection:
    # TODO_OCTREE: this class needs a lot of work

    def __init__(self, level: OctreeLevel, corners_2d):
        self.level = level
        self.corners_2d = corners_2d

        info = self.level.info

        # TODO_OCTREE: don't split rows/cols so all these pairs of variables
        # are just one variable each?
        self.rows: Float2 = corners_2d[:, 0]
        self.cols: Float2 = corners_2d[:, 1]

        base = info.octree_info.base_shape

        self.normalized_rows = np.clip(self.rows / base[0], 0, 1)
        self.normalized_cols = np.clip(self.cols / base[1], 0, 1)

        self.rows /= info.scale
        self.cols /= info.scale

        self.row_range = self.row_range(self.rows)
        self.col_range = self.column_range(self.cols)

    def tile_range(self, span, num_tiles):
        """Return tiles indices needed to draw the span."""

        def _clamp(val, min_val, max_val):
            return max(min(val, max_val), min_val)

        tile_size = self.level.info.octree_info.tile_size

        span_tiles = [span[0] / tile_size, span[1] / tile_size]
        clamped = [
            _clamp(span_tiles[0], 0, num_tiles - 1),
            _clamp(span_tiles[1], 0, num_tiles - 1) + 1,
        ]

        # int() truncates which is what we want
        span_int = [int(x) for x in clamped]
        return range(*span_int)

    def row_range(self, span: Tuple[float, float]) -> range:
        """Return row indices which span image coordinates [y0..y1]."""
        tile_rows = self.level.info.tile_shape[0]
        return self.tile_range(span, tile_rows)

    def column_range(self, span: Tuple[float, float]) -> range:
        """Return column indices which span image coordinates [x0..x1]."""
        tile_cols = self.level.info.tile_shape[1]
        return self.tile_range(span, tile_cols)

    def is_visible(self, row: int, col: int) -> bool:
        """Return True if the tile [row, col] is in the intersection.

        row : int
            The row of the tile.
        col : int
            The col of the tile.
        """

        def _inside(value, value_range):
            return value >= value_range.start and value < value_range.stop

        return _inside(row, self.row_range) and _inside(col, self.col_range)

    def get_chunks(self) -> List[ChunkData]:
        """Return chunks inside this intersection.

        Parameters
        ----------
        intersection : OctreeIntersection
            Describes some subset of one octree level.
        """
        chunks = []

        level_info = self.level.info
        level_index = level_info.level_index

        scale = level_info.scale
        scale_vec = [scale, scale]

        tile_size = level_info.octree_info.tile_size
        scaled_size = tile_size * scale

        # Iterate over every tile in the rectangular region.
        data = None
        y = self.row_range.start * scaled_size
        for row in self.row_range:
            x = self.col_range.start * scaled_size
            for col in self.col_range:

                data = self.level.tiles[row][col]
                pos = [x, y]

                # Only include chunks that have non-zero area. Not sure why
                # some chunks are zero sized. But this will be a harmless
                # check if we get rid of them.
                if 0 not in data.shape:
                    chunks.append(ChunkData(level_index, data, pos, scale_vec))

                x += scaled_size
            y += scaled_size

        return chunks
