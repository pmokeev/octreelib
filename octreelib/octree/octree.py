import itertools

from dataclasses import dataclass
from typing import Callable, List, Generic

import numpy as np

from octreelib.internal import RawPointCloud, T, Voxel, PointCloud
from octreelib.octree.octree_base import OctreeBase, OctreeNodeBase, OctreeConfigBase

__all__ = ["OctreeNode", "Octree", "OctreeConfig"]


@dataclass
class OctreeConfig(OctreeConfigBase):
    pass


class OctreeNode(OctreeNodeBase):
    _point_cloud_type = PointCloud

    def subdivide(self, subdivision_criteria: List[Callable[[RawPointCloud], bool]]):
        """
        Subdivide node based on the subdivision criteria.
        :param subdivision_criteria: list of criteria for subdivision
        """
        if any([criterion(self._points) for criterion in subdivision_criteria]):
            child_edge_length = self.edge_length / np.float_(2)
            children_corners_offsets = itertools.product(
                [0, child_edge_length], repeat=3
            )
            self._children = [
                OctreeNode(self.corner_min + offset, child_edge_length)
                for offset in children_corners_offsets
            ]
            self._has_children = True
            self.insert_points(self._points.copy())
            self._points = self._point_cloud_type.empty()
            for child in self._children:
                child.subdivide(subdivision_criteria)

    def get_points(self) -> RawPointCloud:
        """
        :return: Points inside the octree node.
        """
        if not self._has_children:
            return self._points.copy()

        points = self._point_cloud_type.empty()
        for child in self._children:
            points = np.vstack((points, child.get_points()))
        return points

    def insert_points(self, points: RawPointCloud):
        """
        :param points: Points to insert.
        """
        # convert to internal type
        points = self._point_cloud_type(points)
        if self._has_children:
            for point in points:
                for child in self._children:
                    if child.is_point_geometrically_inside(point):
                        child.insert_points(point)
        else:
            self._points = self._points.extend(points)

    def filter(self, filtering_criteria: List[Callable[[RawPointCloud], bool]]):
        """
        Filter nodes with points by filtering criteria
        :param filtering_criteria: List of filtering criteria functions.
        """
        if self._has_children:
            for child in self._children:
                child.filter(filtering_criteria)
            if all([child.n_points == 0 for child in self._children]):
                self._children = []
                self._has_children = False
        elif not all([criterion(self._points) for criterion in filtering_criteria]):
            self._points = self._point_cloud_type.empty()

    def map_leaf_points(self, function: Callable[[RawPointCloud], RawPointCloud]):
        """
        Transform point cloud in the node using the function.
        :param function: Transformation function RawPointCloud -> RawPointCloud.
        """
        if self._has_children:
            for child in self._children:
                child.map_leaf_points(function)
        elif self._points:
            self._points = function(self._points.copy())

    def get_leaf_points(self) -> List[Voxel]:
        """
        :return: List of voxels where each voxel represents a leaf node with points.
        """
        if self._has_children:
            return sum([child.get_leaf_points() for child in self._children], [])
        return [self] if len(self._points) else []

    @property
    def n_leaves(self):
        """
        :return: number of leaves a.k.a. number of nodes which have points
        """
        return (
            sum([child.n_leaves for child in self._children])
            if self._has_children
            else 1
        )

    @property
    def n_nodes(self):
        """
        :return: number of nodes
        """
        return (
            len(self._children) + sum([child.n_nodes for child in self._children])
            if self._has_children
            else 1
        )

    @property
    def n_points(self):
        """
        :return: number of points in the octree node
        """
        return (
            sum([child.n_points for child in self._children])
            if self._has_children
            else len(self._points)
        )


class Octree(OctreeBase, Generic[T]):
    """
    Stores points from a **single pose** in the form of an octree.

    :param octree_config: Configuration for the octree.
    :param corner: Min corner of the octree.
    :param edge_length: Edge length of the octree.
    """

    _node_type = OctreeNode

    def subdivide(self, subdivision_criteria: List[Callable[[RawPointCloud], bool]]):
        """
        Subdivide node based on the subdivision criteria.
        :param subdivision_criteria: list of criteria for subdivision
        """
        self._root.subdivide(subdivision_criteria)

    def get_points(self) -> RawPointCloud:
        """
        :return: Points, which are stored inside the Octree.
        """
        return self._root.get_points()

    def insert_points(self, points: RawPointCloud):
        """
        :param points: Points to insert
        """
        self._root.insert_points(points)

    def filter(self, filtering_criteria: List[Callable[[RawPointCloud], bool]]):
        """
        Filter nodes with points by filtering criteria
        :param filtering_criteria: List of filtering criteria functions
        """
        self._root.filter(filtering_criteria)

    def map_leaf_points(self, function: Callable[[RawPointCloud], RawPointCloud]):
        """
        transform point cloud in the node using the function
        :param function: transformation function RawPointCloud -> RawPointCloud
        """
        self._root.map_leaf_points(function)

    def get_leaf_points(self) -> List[Voxel]:
        """
        :return: List of voxels where each voxel represents a leaf node with points.
        """
        return self._root.get_leaf_points()

    @property
    def n_points(self):
        """
        :return: number of points in the octree
        """
        return self._root.n_points

    @property
    def n_leaves(self):
        """
        :return: number of leaves a.k.a. number of nodes which have points
        """
        return self._root.n_leaves

    @property
    def n_nodes(self):
        """
        :return: number of nodes
        """
        return self._root.n_nodes