#! /usr/bin/env python

"""
Module that contains data definition for CV based controls
"""

from __future__ import print_function, division, absolute_import, unicode_literals

from copy import copy

axis_eq = {'X': 0, 'Y': 1, 'Z': 2}
rot_orders = ['XYZ', 'YXZ', 'ZYX']


class ControlPool(set):
    """
    Set object that contains all controls loaded by the ControlManager
    """

    def __init__(self, *args, **kwargs):
        super(ControlPool, self).__init__(*args, **kwargs)

    # region Override Functions
    def __contains__(self, item):
        """
        Returns whether the given control already exists or not in the ControlPool
        :param item:
        :return: bool
        """

        return self._find(item)

    def __call__(self, *args, **kwargs):
        """
        Returns a formatted version of the list
        """

        return {name()[0]: name()[1] for name in self}

    def __getitem__(self, item):
        return self._find(item)

    def __setitem__(self, key, value):
        self.add(value)

    def remove(self, target):
        super(ControlPool, self).remove(self._find(target))
    # endregion

    # region Private Functions
    def _find(self, ctrl_name):
        for item in self:
            if item.name == ctrl_name:
                return item
    # endregion


class ControlV(list):
    """
    Base class used to represent curve CVs
    """

    def ControlVWrapper(self):
        def wrapper(*args, **kwargs):
            f = self(*[a if isinstance(a, ControlV) else ControlV([a, a, a]) for a in args], **kwargs)
            return f
        return wrapper

    @ControlVWrapper
    def __mul__(self, other):
        return ControlV([self[i] * other[i] for i in range(3)])

    @ControlVWrapper
    def __sub__(self, other):
        return ControlV([self[i] - other[i] for i in range(3)])

    @ControlVWrapper
    def __add__(self, other):
        return ControlV([self[i] + other[i] for i in range(3)])

    def __imul__(self, other):
        return self * other

    def __rmul__(self, other):
        return self * other

    def __isub__(self, other):
        return self - other

    def __rsub__(self, other):
        return self - other

    def __iadd__(self, other):
        return self + other

    def __radd__(self, other):
        return self + other

    @staticmethod
    def mirror_vector():
        return {
            None: ControlV([1, 1, 1]),
            'None': ControlV([1, 1, 1]),
            'XY': ControlV([1, 1, -1]),
            'YZ': ControlV([-1, 1, 1]),
            'ZX': ControlV([1, -1, 1])
        }

    def reorder(self, order):
        """
        With a given order sequence CVs will be reordered (for axis order purposes)
        :param order: list(int)
        """

        return ControlV([self[i] for i in order])


class ControlShape(object):
    """
    Base class that handles control shapes as a sequences of points in space
    """

    def __init__(self, cvs=None, degree=1, periodic=False):
        super(ControlShape, self).__init__()

        self.__cvs__ = [ControlV(pt) for pt in copy(cvs)]       # Original coordinates
        self._cvs = cvs                                         # Common coordinates, if the shape is smoothed
        self._transformed_cvs = cvs                             # Last coordinates, the ones with the transforms
        self._degree = degree
        self._periodic = periodic
        self._smooth = False

        self._transform_offset = ControlV([0, 0, 0])
        self._transform_factor = ControlV([-1, -1, -1])
        self._transform_axis = range(3)
        self._transform_mirror = ControlV.mirror_vector()[None]

    def get_cvs(self):
        return self._cvs

    def set_cvs(self, cvs):
        self._cvs = cvs

    def get_transformed_cvs(self):
        return self._transformed_cvs

    def set_transformed_cvs(self, cvs):
        self._transformed_cvs = cvs

    def get_degree(self):
        return self._degree

    def get_periodic(self):
        return self._periodic

    def get_smooth(self):
        return self._smooth

    def set_smooth(self, smooth):
        self._smooth = smooth

    cvs = property(get_cvs, set_cvs)
    transformed_cvs = property(get_transformed_cvs, set_transformed_cvs)
    degree = property(get_degree)
    periodic = property(get_periodic)
    smooth = property(get_smooth, set_smooth)

    def __call__(self):
        """
        Returns a formated version of the shape for saving purpose
        :return: dict
        """

        shape_dict = {
            'cvs': self.__cvs__,
            'degree': self._degree,
            'periodic': self._periodic
        }

        return shape_dict

    def __getitem__(self, item):
        return self()[item]

    def apply_transform(self):
        """
        Apply the transforms to the current shape
        """

        points = copy(self._cvs)
        for i, point in enumerate(points):
            point = ControlV(point) * self._transform_factor
            point -= self._transform_offset
            point *= self._transform_mirror
            points[i] = point.reorder(self._transform_axis)

        self._transformed_cvs = points

    def transform(self, offset, scale, axis, mirror):
        """
        Stores the new transform of the curve shape
        :param offset: position offset
        :param scale:  scale factor
        :param axis:  axis order
        :param mirror:
        """

        order = [axis_eq[x] for x in axis]
        self._transform_offset = -1 * ControlV(offset).reorder(order)
        self._transform_factor = ControlV(scale).reorder(order)
        self._transform_axis = order
        self._transform_mirror = ControlV.mirror_vector()[mirror]

        self.apply_transform()


class ControlData(object):
    """
    Basic storage class for controls
    """

    def __init__(self, name='', control_data=None, parent=None):
        super(ControlData, self).__init__()

        self._name = name
        self._shapes = list()
        self._parent = parent
        self._data = control_data

        if isinstance(control_data, (list, tuple)):
            for ctrl in control_data:
                if 'periodic' not in ctrl:
                    if 'form' in ctrl:
                        ctrl['periodic'] = 1 if ctrl['form'] == 3 else 0
                    else:
                        ctrl['periodic'] = 1

                self._shapes.append(ControlShape(
                    cvs=ctrl['cvs'],
                    degree=ctrl['degree'],
                    periodic=ctrl['periodic']
                ))
        else:
            for shape_name, shape_data in control_data.items():
                if 'periodic' not in shape_data:
                    if 'form' in shape_data:
                        shape_data['periodic'] = 1 if shape_data['form'] == 3 else 0
                    else:
                        shape_data['periodic'] = 1

                self._shapes.append(ControlShape(
                    cvs=shape_data['cvs'],
                    degree=shape_data['degree'],
                    periodic=shape_data['periodic']
                ))

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        self._name = new_name

    @property
    def data(self):
        return self._data

    @property
    def shapes(self):
        return self._shapes

    @property
    def parent(self):
        return self._parent

    def __call__(self):
        return self.name, [shape() for shape in self._shapes]
