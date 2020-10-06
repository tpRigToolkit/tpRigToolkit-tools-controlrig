#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Control Rig widget controller class implementation
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp
from tpDcc.libs.python import python

from tpRigToolkit.libs.controlrig.core import controllib, controldata

LOGGER = tp.LogsMgr().get_logger('tpRigToolkit-tools-controlrig')


class ControlRigController(object):
    def __init__(self, client, model):
        super(ControlRigController, self).__init__()

        self._client = client
        self._model = model

        self._controls_lib = controllib.ControlLib()

    @property
    def client(self):
        return self._client

    @property
    def model(self):
        return self._model

    def get_joint_radius(self):
        """
        Returns the radius used to display joints
        :return: float
        """

        return self._client.get_joint_radius()

    def update_controls(self):
        """
        Updates available controls
        """

        controls_path = self.model.controls_path
        self._controls_lib.controls_file = controls_path
        controls = self._controls_lib.load_control_data() or list()
        self._model.controls = controls

        return controls

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

        rotate_orders = self._client.get_rotate_orders() or list()
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

        color_list = color.toRgb().toTuple() if hasattr(color, 'toRgb') else color
        color_list = [color_channel / 255 for color_channel in color_list]
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

        return self._controls_lib.rename_control(original_name, new_name)

    def get_current_control_data(self, control_name):
        """
        Returns dictionary that contains all the data of the current control to be created
        :return: dict
        """

        if not control_name:
            return None
        control_data = self._controls_lib.get_control_data_by_name(control_name)
        if not control_data:
            return None
        control_shapes = control_data.shapes
        if not control_shapes:
            return None
        control_shapes_data = [control_shape() for control_shape in control_shapes]
        if not control_shapes_data:
            return None

        return {
            'control_name': control_name,
            'shape_data': control_shapes_data,
            'size': self._model.control_size,
            'name': self._model.control_name,
            'offset': self._model.offset,
            'ori': self._model.factor,
            'axis_order': controldata.rot_orders[self._model.control_axis],
            'shape_parent':  self._model.parent_shape_to_transform,
            'buffer_groups': self._model.buffer_transforms_depth,
            'mirror': self._model.mirror_plane,
            'color': self._model.control_color
        }

    # def set_control_data(self, data_dict):
    #     """
    #     Function that set current control widget status taking into account the data from a dictionary
    #     :param data_dict: dict
    #     """
    #
    #     control_name = data_dict.get('control_name', None)
    #     size = data_dict.get('size', 1.0)
    #     name = data_dict.get('name', 'new_ctrl')
    #     offset = data_dict.get('offset', [0.0, 0.0, 0.0])
    #     mirror = data_dict.get('mirror', None)
    #     color = data_dict.get('color', [1.0, 0.0, 0.0, 1.0])
    #     axis_order = data_dict.get('axis_order', 'XYZ')
    #     ori = data_dict.get('ori', [1.0, 1.0, 1.0])
    #     shape_parent = data_dict.get('shape_parent', False)
    #
    #     items = self.controls_list.findItems(control_name, Qt.MatchExactly, 0)
    #     if not items:
    #         return
    #     item = items[0]
    #     self.controls_list.setCurrentItem(item)
    #     self.radius.setValue(float(size))
    #     self._name_line.setText(str(name))
    #     self.offset_x.setValue(float(offset[0]))
    #     self.offset_y.setValue(float(offset[1]))
    #     self.offset_z.setValue(float(offset[2]))
    #     self.factor_x.setValue(float(ori[0]))
    #     self.factor_y.setValue(float(ori[1]))
    #     self.factor_z.setValue(float(ori[2]))
    #     self.rotate_order.setCurrentText(axis_order[0])
    #     self.parent_shape.setChecked(bool(shape_parent))
    #     self.color_picker.set_color(QColor.fromRgbF(*color))
    #     mirror = str(mirror)
    #     for mirror_btn in self.mirror.buttons():
    #         if mirror_btn.text() == mirror:
    #             mirror_btn.setChecked(True)
    #             break

    def add_control(self, orig, name, absolute_position, absolute_rotation, degree, periodic):
        """
        Adds a new control
        """

        controls = self._controls_lib.load_control_data() or list()
        if name in controls:
            LOGGER.error(
                'Control "{}" already exists in the Control Data File. Aborting control add operation ...'.format(name))
            return False

        curve_info = self._controls_lib.get_curve_info(
            crv=orig,
            absolute_position=absolute_position,
            absolute_rotation=absolute_rotation,
            degree=degree,
            periodic=periodic
        )
        if not curve_info:
            LOGGER.error(
                'Curve Info for "{}" curve was not generated properly! Aborting control add operation ...'.format(orig))
            return False

        new_control = self._controls_lib.add_control(name, curve_info)
        if not new_control:
            LOGGER.error('Control for curve "{}" not created! Aborting control add operation ...'.format(orig))
            return False

        # We temporally block signals to avoid model to send updates during controls update
        self._model.blockSignals(True)
        try:
            self.update_controls()
        finally:
            self._model.blockSignals(False)

        self._client.select_node(orig)

        return {
            'name': name,
            'control': new_control,
            'shapes': new_control.shapes
        }

    def remove_control(self, control_name):
        """
        Removes a control
        :param control_name: str
        """

        controls = self._controls_lib.load_control_data() or list()
        if control_name not in controls:
            LOGGER.error(
                'Control "{}" does not exists in the Control Data File. Aborting control deletion operation ...'.format(
                    control_name))
            return False

        self._controls_lib.delete_control(control_name)

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

        control_data['target_object'] = self._client.selected_nodes()
        control_data.pop('control_name', None)
        if not self._model.create_buffer_transforms:
            control_data['buffer_groups'] = 0

        controls_file = self._controls_lib.controls_file
        ccs = self._client.create_control(control_data, controls_file, select_created_control=True)

        # TODO: Make this work, after creating a control combining shapes. Create buffer hierarchy
        # buffer_groups = control_data['buffer_groups']
        # if buffer_groups and self._model.create_buffer_transforms:
        #     for ctrl in controls_to_select:
        #         # shapes = tp.Dcc.list_relatives(ctrl)
        #         self._controls_lib.create_buffer_groups(ctrl, buffer_groups)

        return True

    def assign_control(self, source_control_name, target_objects):
        """
        Assigns given control to given the shapes of the given target object
        :param source_control_name: str
        :param target_objects: str or list(str)
        """

        target_objects = python.force_list(target_objects)

        controls = self._controls_lib.load_control_data() or list()
        if source_control_name not in controls:
            LOGGER.error(
                'Control "{}" does not exists in the Control Data File. '
                'Aborting control assign operation to "{}"'.format(source_control_name, source_control_name))
            return False

        control_data = self.get_current_control_data(source_control_name)
        if not control_data:
            LOGGER.error(
                'Impossible to retrieve control "{}" data from Control Data File. '
                'Aborting control assign operation to "{}"'.format(source_control_name, source_control_name))
            return False

        control_data['shape_parent'] = False
        control_data['buffer_groups'] = 0
        control_data.pop('control_name', None)

        nodes_to_select = list()
        for target_object in target_objects:
            control_data['target_object'] = target_object
            keep_color = self._model.keep_assign_color
            controls_file = self._controls_lib.controls_file
            ccs = self._client.create_control(control_data, controls_file)[0]
            new_shape = self._controls_lib.set_shape(target_object, ccs, keep_color=keep_color)
            nodes_to_select.append(new_shape)

        if nodes_to_select:
            self._client.select_node(nodes_to_select, add_to_selection=True)

        return True
