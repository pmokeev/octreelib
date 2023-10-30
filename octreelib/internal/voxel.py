import itertools
from abc import ABC, abstractmethod
from typing import Callable, List, Optional

import numpy as np

from octreelib.internal.point import RawPoint, RawPointCloud
from octreelib.internal.interfaces import WithID, WithPoints

__all__ = ["StaticStoringVoxel", "StoringVoxel", "Voxel"]


def _point_to_hashable(point: RawPoint):
    return float(point[0]), float(point[1]), float(point[2])


_static_voxel_id_map = {}


class Voxel(WithID):
    def __init__(self, corner: RawPoint, edge_length: np.float_):
        corner_hashable = _point_to_hashable(corner)
        other_hashable = _point_to_hashable(corner + edge_length)

        if (corner_hashable, other_hashable) not in _static_voxel_id_map:
            _static_voxel_id_map[(corner_hashable, other_hashable)] = len(
                _static_voxel_id_map
            )

        WithID.__init__(self, _static_voxel_id_map[(corner_hashable, other_hashable)])
        self.corner = corner
        self.edge_length = edge_length

    @property
    def corners(self):
        return [
            self.corner + offset
            for offset in itertools.product([0, self.edge_length], repeat=3)
        ]


class StaticStoringVoxel(Voxel, WithPoints):
    def __init__(
        self, corner: RawPoint, edge_length: np.float_, points: Optional[RawPointCloud] = None
    ):
        Voxel.__init__(self, corner, edge_length)
        WithPoints.__init__(self, points)

    def get_points(self) -> RawPointCloud:
        return self.points.copy()


class StoringVoxel(Voxel, WithPoints, ABC):
    def __init__(self, corner: RawPoint, edge_length: np.float_):
        Voxel.__init__(self, corner, edge_length)
        WithPoints.__init__(self)

    @abstractmethod
    def subdivide(self, subdivision_criteria: List[Callable[[RawPointCloud], bool]]):
        pass

    @abstractmethod
    def insert_points(self, points: RawPointCloud):
        pass

    @abstractmethod
    def get_points(self) -> RawPointCloud:
        pass
