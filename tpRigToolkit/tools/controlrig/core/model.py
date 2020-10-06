#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Control Rig widget model class implementation
"""

from __future__ import print_function, division, absolute_import

import os

from Qt.QtCore import *

from tpDcc.libs.python import python


class ControlRigModel(QObject, object):

    controlsPathChanged = Signal(str)
    controlsChanged = Signal(object)
    currentControlChanged = Signal(str)
    controlNameChanged = Signal(str)
    controlSizeChanged = Signal(float)
    offsetXChanged = Signal(float)
    offsetYChanged = Signal(float)
    offsetZChanged = Signal(float)
    defaultOffsetXChanged = Signal(float)
    defaultOffsetYChanged = Signal(float)
    defaultOffsetZChanged = Signal(float)
    factorXChanged = Signal(float)
    factorYChanged = Signal(float)
    factorZChanged = Signal(float)
    defaultFactorXChanged = Signal(float)
    defaultFactorYChanged = Signal(float)
    defaultFactorZChanged = Signal(float)
    axisChanged = Signal(int)
    controlColorChanged = Signal(tuple)
    mirrorPlaneChanged = Signal(str)
    createBufferTransformsChanged = Signal(bool)
    parentShapeToTransformChanged = Signal(bool)
    bufferTransformsDepthChanged = Signal(int)
    keepAssignColorChanged = Signal(bool)

    def __init__(self, controls_path=None):
        super(ControlRigModel, self).__init__()

        self._controls_path = None
        self._controls = None
        self._current_control = None
        self._control_name = 'new'
        self._default_control_size = 1.0
        self._control_size = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0
        self._offset_z = 0.0
        self._default_offset_x = 0.0
        self._default_offset_y = 0.0
        self._default_offset_z = 0.0
        self._factor_x = 1.0
        self._factor_y = 1.0
        self._factor_z = 1.0
        self._default_factor_x = 1.0
        self._default_factor_y = 1.0
        self._default_factor_z = 1.0
        self._control_axis = 0
        self._mirror_plane = 'None'
        self._control_color = [240, 245, 255]
        self._create_buffer_transforms = False
        self._parent_shape_to_transform = False
        self._buffer_transforms_depth = 1
        self._keep_assign_color = True

        self.controls_path = controls_path

    @property
    def controls_path(self):
        return self._controls_path

    @controls_path.setter
    def controls_path(self, controls_file):
        controls_path = controls_file if controls_file and os.path.isfile(controls_file) else None
        if not controls_path:
            controls_path = self._get_default_data_file()

        self._controls_path = str(controls_path)
        self.controlsPathChanged.emit(self._controls_path)

    @property
    def controls(self):
        return self._controls

    @controls.setter
    def controls(self, controls_data):
        self._controls = controls_data
        self.controlsChanged.emit(self._controls)

    @property
    def current_control(self):
        return self._current_control

    @current_control.setter
    def current_control(self, control_name):
        self._current_control = str(control_name)
        self.currentControlChanged.emit(self._current_control)

    @property
    def control_name(self):
        return self._control_name

    @control_name.setter
    def control_name(self, value):
        self._control_name = str(value)
        self.controlNameChanged.emit(self._control_name)

    @property
    def default_control_size(self):
        return self._default_control_size

    @default_control_size.setter
    def default_control_size(self, value):
        self._default_control_size = float(value)

    @property
    def control_size(self):
        return self._control_size

    @control_size.setter
    def control_size(self, value):
        self._control_size = float(value)
        self.controlSizeChanged.emit(self._control_size)

    @property
    def offset(self):
        return [self._offset_x, self._offset_y, self._offset_z]

    @offset.setter
    def offset(self, offset_list):
        self._offset_x = float(offset_list[0])
        self._offset_y = float(offset_list[1])
        self._offset_z = float(offset_list[2])

    @property
    def offset_x(self):
        return self._offset_x

    @offset_x.setter
    def offset_x(self, value):
        self._offset_x = float(value)
        self.offsetXChanged.emit(self._offset_x)

    @property
    def offset_y(self):
        return self._offset_y

    @offset_y.setter
    def offset_y(self, value):
        self._offset_y = float(value)
        self.offsetYChanged.emit(self._offset_y)

    @property
    def offset_z(self):
        return self._offset_z

    @offset_z.setter
    def offset_z(self, value):
        self._offset_z = float(value)
        self.offsetZChanged.emit(self._offset_z)

    @property
    def default_offset_x(self):
        return self._default_offset_x

    @default_offset_x.setter
    def default_offset_x(self, value):
        self._default_offset_x = float(value)
        self.defaultOffsetXChanged.emit(self._default_offset_x)

    @property
    def default_offset_y(self):
        return self._default_offset_y

    @default_offset_y.setter
    def default_offset_y(self, value):
        self._default_offset_y = float(value)
        self.defaultOffsetXChanged.emit(self._default_offset_y)

    @property
    def default_offset_z(self):
        return self._default_offset_z

    @default_offset_z.setter
    def default_offset_z(self, value):
        self._default_offset_z = float(value)
        self.defaultOffsetZChanged.emit(self._default_offset_z)

    @property
    def factor(self):
        return [self._factor_x, self._factor_y, self._factor_z]

    @factor.setter
    def factor(self, factor_list):
        self._factor_x = float(factor_list[0])
        self._factor_y = float(factor_list[1])
        self._factor_z = float(factor_list[2])

    @property
    def factor_x(self):
        return self._factor_x

    @factor_x.setter
    def factor_x(self, value):
        self._factor_x = float(value)
        self.factorXChanged.emit(self._factor_x)

    @property
    def factor_y(self):
        return self._factor_y

    @factor_y.setter
    def factor_y(self, value):
        self._factor_y = float(value)
        self.factorYChanged.emit(self._factor_y)

    @property
    def factor_z(self):
        return self._factor_z

    @factor_z.setter
    def factor_z(self, value):
        self._factor_z = float(value)
        self.factorZChanged.emit(self._factor_z)

    @property
    def default_factor_x(self):
        return self._default_factor_x

    @default_factor_x.setter
    def default_factor_x(self, value):
        self._default_factor_x = float(value)
        self.defaultFactorXChanged.emit(self._default_factor_x)

    @property
    def default_factor_y(self):
        return self._default_factor_y

    @default_factor_y.setter
    def default_factor_y(self, value):
        self._default_factor_y = float(value)
        self.defaultFactorYChanged.emit(self._default_factor_y)

    @property
    def default_factor_z(self):
        return self._default_factor_z

    @default_factor_z.setter
    def default_factor_z(self, value):
        self._default_factor_z = float(value)
        self.defaultFactorZChanged.emit(self._default_factor_z)

    @property
    def control_axis(self):
        return self._control_axis

    @control_axis.setter
    def control_axis(self, value):
        self._control_axis = int(value)
        self.axisChanged.emit(self._control_axis)

    @property
    def control_color(self):
        return self._control_color

    @control_color.setter
    def control_color(self, color_tuple):
        self._control_color = python.force_tuple(color_tuple)
        self.controlColorChanged.emit(self._control_color)

    @property
    def mirror_plane(self):
        return self._mirror_plane

    @mirror_plane.setter
    def mirror_plane(self, value):
        self._mirror_plane = str(value)
        self.mirrorPlaneChanged.emit(self._mirror_plane)

    @property
    def create_buffer_transforms(self):
        return self._create_buffer_transforms

    @create_buffer_transforms.setter
    def create_buffer_transforms(self, flag):
        self._create_buffer_transforms = bool(flag)
        self.createBufferTransformsChanged.emit(self._create_buffer_transforms)

    @property
    def parent_shape_to_transform(self):
        return self._parent_shape_to_transform

    @parent_shape_to_transform.setter
    def parent_shape_to_transform(self, flag):
        self._parent_shape_to_transform = bool(flag)
        self.parentShapeToTransformChanged.emit(self._parent_shape_to_transform)

    @property
    def buffer_transforms_depth(self):
        return self._buffer_transforms_depth

    @buffer_transforms_depth.setter
    def buffer_transforms_depth(self, value):
        self._buffer_transforms_depth = int(value)
        self.bufferTransformsDepthChanged.emit(self._buffer_transforms_depth)

    @property
    def keep_assign_color(self):
        return self._keep_assign_color

    @keep_assign_color.setter
    def keep_assign_color(self, flag):
        self._keep_assign_color = bool(flag)
        self.keepAssignColorChanged.emit(self._keep_assign_color)

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _get_default_data_file(self):
        """
        Internal function that returns the default path to controls data file
        :return: str
        """

        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'controls_data.json')
