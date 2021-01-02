#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Control Rig widget controller class implementation
"""

from __future__ import print_function, division, absolute_import

import logging

from tpDcc.libs.python import python
from tpDcc.libs.curves.core import curveslib

from tpRigToolkit.tools.controlrig.core import controldata

LOGGER = logging.getLogger('tpRigToolkit-tools-controlrig')


class ControlRigController(object):
    def __init__(self, client, model):
        super(ControlRigController, self).__init__()

        self._client = client
        self._model = model

    @property
    def client(self):
        return self._client()

    @property
    def model(self):
        return self._model

    def get_joint_radius(self):
        """
        Returns the radius used to display joints
        :return: float
        """

        return self.client.get_joint_radius()

    def update_controls(self):
        """
        Updates available controls
        """

        controls_path = self.model.controls_path
        control_names = curveslib.get_curve_names(controls_path) or list()
        controls_data = list()
        for control_name in control_names:
            try:
                control_data = curveslib.load_curve_from_name(control_name, controls_path)
                new_control_data = controldata.ControlData(control_name, control_data)

                # TODO: We should not add ControlData to the model, instead we should pass the dictionary there
                controls_data.append(new_control_data)
            except Exception as exc:
                LOGGER.warning('Impossible to load control "{}" : {}'.format(control_name, exc))
                continue

        self._model.controls = controls_data

        return controls_data

    def set_current_control(self, control_name):
        """
        Sets the current control
        :param control_name: QTreeWidgetItem
        """

        self._model.current_control = control_name

    def set_control_name(self, control_name):
        """
        Sets the name of the control to be created
        :param control_name: str
        """

        self._model.control_name = control_name

    def set_default_control_size(self, default_control_size):
        """
        Sets the default size for controls
        :param default_control_size: float
        """

        self._model.default_control_size = default_control_size

    def set_control_size(self, control_size):
        """
        Sets the size of the control to be created
        :param control_size: float
        """

        self._model.control_size = control_size

    def reset_to_default_control_size(self):
        """
        Resets current control size to its default value
        """

        default_size = self._model.default_control_size
        self._model.control_size = default_size

    def set_offset_x(self, value):
        """
        Sets the offset X value
        :param value: float
        """

        self._model.offset_x = value

    def set_offset_y(self, value):
        """
        Sets the offset Y value
        :param value: float
        """

        self._model.offset_y = value

    def set_offset_z(self, value):
        """
        Sets the offset Z value
        :param value: float
        """

        self._model.offset_z = value

    def set_default_offset_x(self, value):
        """
        Sets the default X offset value
        :param value: float
        """

        self._model.default_offset_x = value

    def set_default_offset_y(self, value):
        """
        Sets the default Y offset value
        :param value: float
        """

        self._model.default_offset_y = value

    def set_default_offset_z(self, value):
        """
        Sets the default Z offset value
        :param value: float
        """

        self._model.default_offset_z = value

    def set_factor_x(self, value):
        """
        Sets the factor X value
        :param value: float
        """

        self._model.factor_x = value

    def set_factor_y(self, value):
        """
        Sets the factor Y value
        :param value: float
        """

        self._model.factor_y = value

    def set_factor_z(self, value):
        """
        Sets the factor Z value
        :param value: float
        """

        self._model.factor_z = value
    
    def set_default_factor_x(self, value):
        """
        Sets the default X factor value
        :param value: float
        """

        self._model.default_factor_x = value

    def set_default_factor_y(self, value):
        """
        Sets the default Y factor value
        :param value: float
        """

        self._model.default_factor_y = value

    def set_default_factor_z(self, value):
        """
        Sets the default Z factor value
        :param value: float
        """

        self._model.default_factor_z = value

    def update_fonts(self):
        """
        Updates available fonts
        :return: list
        """

        rotate_orders = self.client.get_rotate_orders() or list()
        self._model.rotate_orders = rotate_orders

    def set_current_axis(self, axis_index):
        """
        Sets the current control axis
        :param axis_index: int
        """

        self._model.control_axis = axis_index

    def set_color(self, color):
        """
        Sets the current control color
        :param color: QColor, Qt color in 0-1 range
        """

        if hasattr(color, 'toRgb'):
            color_list = color.toRgb().toTuple()
            color_list = [color_channel / 255 for color_channel in color_list]
        else:
            color_list = color
        self._model.control_color = color_list

    def set_mirror_plane(self, mirror_plane_index):
        """
        Sets the mirror plane used to create the control
        :param mirror_plane_index: int
        """

        self._model.mirror_plane = mirror_plane_index

    def set_create_buffer_transforms(self, flag):
        """
        Sets whether or not buffer transform(s) for the new control need to be created
        :param flag: flag
        """

        self._model.create_buffer_transforms = flag

    def set_parent_shape_to_transform(self, flag):
        """
        Sets whether or not control shape should be parented to the transform
        :param flag: bool
        """

        self._model.parent_shape_to_transform = flag

    def set_buffer_transforms_depth(self, value):
        """
        Sets the number of buffer transforms that should be created
        :param value: int
        """

        self._model.buffer_transforms_depth = value

    def set_keep_assign_color(self, flag):
        """
        Sets whether or not assigned control should keep original shapes color or not
        :param flag: bool
        """

        self._model.keep_assign_color = flag

    def rename_control(self, original_name, new_name):
        """
        Renames the given control from the new name
        :param original_name:
        :param new_name:
        :return:
        """

        return curveslib.rename_curve(original_name, new_name, curves_path=self._model.controls_path)

    def get_current_control_data(self, control_name=None):
        """
        Returns dictionary that contains all the data of the current control to be created
        :return: dict
        """

        control_name = control_name or self._model.current_control
        if not control_name:
            return None
        control_data = curveslib.load_curve_from_name(control_name, self._model.controls_path)
        if not control_data:
            return None

        return {
            'control_name': self._model.control_name,
            'control_type': control_name,
            'controls_path': self._model.controls_path,
            'control_size': self._model.control_size,
            'translate_offset': self._model.offset,
            'scale': self._model.factor,
            'axis_order': controldata.rot_orders[self._model.control_axis],
            'mirror': self._model.mirror_plane,
            'color': self._model.control_color,
            'create_buffers': self._model.create_buffer_transforms,
            'buffers_depth': self._model.buffer_transforms_depth
        }

    def set_control_data(self, data_dict):
        """
        Function that set current control widget status taking into account the data from a dictionary
        :param data_dict: dict
        """

        control_type = data_dict.get('control_type', 'circle')
        control_size = data_dict.get('control_size', 1.0)
        control_name = data_dict.get('control_name', 'new_ctrl')
        translate_offset = data_dict.get('translate_offset', (0.0, 0.0, 0.0))
        mirror = data_dict.get('mirror', None)
        color = data_dict.get('color', (1.0, 1.0, 1.0))
        axis_order = data_dict.get('axis_order', 'XYZ')
        scale = data_dict.get('scale', (1.0, 1.0, 1.0))
        shape_parent = data_dict.get('shape_parent', False)

        self.set_current_control(control_type)
        self.set_control_size(control_size)
        self.set_control_name(control_name)
        self.set_offset_x(translate_offset[0])
        self.set_offset_y(translate_offset[1])
        self.set_offset_z(translate_offset[2])
        self.set_factor_x(scale[0])
        self.set_factor_y(scale[1])
        self.set_factor_z(scale[2])
        self.set_color(color)
        self.set_current_axis(controldata.axis_eq.get(axis_order[0], 'X'))

    #     self.parent_shape.setChecked(bool(shape_parent))
    #     mirror = str(mirror)
    #     for mirror_btn in self.mirror.buttons():
    #         if mirror_btn.text() == mirror:
    #             mirror_btn.setChecked(True)
    #             break

    def add_control(self, orig, name, absolute_position, absolute_rotation, degree, periodic):
        """
        Adds a new control
        """

        control_names = curveslib.get_curve_names(self._model.controls_path)
        if name in control_names:
            LOGGER.error(
                'Control "{}" already exists in the Control Data File. Aborting control add operation ...'.format(name))
            return False

        control_data, control_path = curveslib.save_curve(orig, name)
        if not control_data:
            LOGGER.error('Control for curve "{}" not created! Aborting control add operation ...'.format(orig))
            return False

        # We temporally block signals to avoid model to send updates during controls update
        self._model.blockSignals(True)
        try:
            self.update_controls()
        finally:
            self._model.blockSignals(False)

        self.client.select_node(orig)

        new_control = controldata.ControlData(name, control_data)
        return {
            'name': name,
            'control': new_control
        }

    def remove_control(self, control_name):
        """
        Removes a control
        :param control_name: str
        """

        curveslib.delete_curve(control_name, curves_path=self._model.controls_path)

        # We temporally block signals to avoid model to send updates during controls update
        self._model.blockSignals(True)
        try:
            self.update_controls()
        finally:
            self._model.blockSignals(False)

        return True

    def create_control(self, control_name=None):

        control_name = control_name or self._model.current_control
        if not control_name:
            return False
        control_data = self.get_current_control_data(control_name)
        if not control_data:
            return

        shape_parent = self._model.parent_shape_to_transform
        if shape_parent and self.client.node_exists(shape_parent):
            selected_nodes = self.client.selected_nodes()
            if selected_nodes:
                control_data['parent'] = selected_nodes[0]

        self.client.create_control(control_data, select_created_control=True)

        # TODO: Make this work, after creating a control combining shapes. Create buffer hierarchy
        # buffer_groups = control_data['buffer_groups_count']
        # if buffer_groups and self._model.create_buffer_transforms:
        #     print('Creating buffer group ....')

        #     for ctrl in controls_to_select:
        #         # shapes = dcc.list_relatives(ctrl)
        #         self._controls_lib.create_buffer_groups(ctrl, buffer_groups)

        return True

    def assign_control(self, source_control_name, target_objects):
        """
        Assigns given control to given the shapes of the given target object
        :param source_control_name: str
        :param target_objects: str or list(str)
        """

        target_objects = python.force_list(target_objects)
        keep_color = self._model.keep_assign_color
        controls_path = self._model.controls_path
        nodes_to_select = self.client.replace_control_curves(
            target_objects, control_type=source_control_name, controls_path=controls_path, keep_color=keep_color)

        if nodes_to_select:
            self.client.select_node(nodes_to_select, add_to_selection=True)

        return True
