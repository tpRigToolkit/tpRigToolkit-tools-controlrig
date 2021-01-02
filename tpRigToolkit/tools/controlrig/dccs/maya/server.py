#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains control rig server implementation for Maya
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from tpDcc import dcc
from tpDcc.core import server

from tpDcc.libs.curves.core import curveslib
from tpDcc.dccs.maya.core import filtertypes, shape as shape_utils

from tpRigToolkit.libs.controlrig.core import controllib


class ControlRigServer(server.DccServer, object):
    PORT = 13144

    def __init__(self, *args, **kwargs):
        super(ControlRigServer, self).__init__(*args, **kwargs)

        # Force register DCC commands
        curveslib.CurvesLib.load()

    def _process_command(self, command_name, data_dict, reply_dict):
        if command_name == 'update_selected_nodes':
            self.update_selected_nodes(data_dict, reply_dict)
        elif command_name == 'filter_transforms_with_shapes':
            self.filter_transforms_with_shapes(data_dict, reply_dict)
        elif command_name == 'update_display_state':
            self.update_display_state(data_dict, reply_dict)
        elif command_name == 'set_index_color':
            self.set_index_color(data_dict, reply_dict)
        elif command_name == 'set_rgb_color':
            self.set_rgb_color(data_dict, reply_dict)
        elif command_name == 'get_joint_radius':
            self.get_joint_radius(data_dict, reply_dict)
        elif command_name == 'create_control':
            self.create_control(data_dict, reply_dict)
        elif command_name == 'create_control_text':
            self.create_control_text(data_dict, reply_dict)
        elif command_name == 'replace_control_curves':
            self.replace_control_curves(data_dict, reply_dict)
        elif command_name == 'mirror_control':
            self.mirror_control(data_dict, reply_dict)
        elif command_name == 'get_control_color':
            self.get_control_color(data_dict, reply_dict)
        elif command_name == 'select_controls_by_color':
            self.select_controls_by_color(data_dict, reply_dict)
        elif command_name == 'scale_control':
            self.scale_control(data_dict, reply_dict)
        else:
            super(ControlRigServer, self)._process_command(command_name, data_dict, reply_dict)

    def update_selected_nodes(self, data, reply):
        nodes = data.get('nodes', list())
        deselect = data.get('deselect', True)

        selected_nodes = dcc.selected_nodes(full_path=True) or list()
        if selected_nodes:
            valid_nodes = selected_nodes
        else:
            valid_nodes = list()
            for node in nodes:
                if not node or not dcc.node_exists(node):
                    continue
                valid_nodes.append(node)

        if selected_nodes and deselect:
            dcc.clear_selection()

        reply['success'] = True
        reply['result'] = valid_nodes

    def filter_transforms_with_shapes(self, data, reply):
        nodes = data.get('nodes', list())
        children = data.get('hierarchy', False)

        valid_nodes = list()
        if not nodes:
            reply['success'] = True
            return valid_nodes

        for node in nodes:
            if not node or not dcc.node_exists(node):
                continue
            valid_nodes.append(node)
        if not valid_nodes:
            reply['success'] = True
            return valid_nodes

        transforms_with_shapes = filtertypes.filter_transforms_with_shapes(
            valid_nodes, children=children, shape_type='nurbsCurve') or list()

        reply['success'] = True
        reply['result'] = transforms_with_shapes

    @dcc.undo_decorator()
    def update_display_state(self, data, reply):
        nodes = data.get('nodes', list())
        display_index = data.get('display_index', 0)        # 0 = Normal; 1 = Template; 2 = Reference

        nodes = nodes or dcc.selected_nodes(full_path=True)
        if nodes:
            for obj in nodes:
                dcc.clean_construction_history(obj)
                shapes = dcc.list_children_shapes(obj, all_hierarchy=True)
                for shape in shapes:
                    dcc.set_attribute_value(shape, 'overrideEnabled', True)
                    dcc.set_attribute_value(shape, 'overrideDisplayType', display_index)
                    if display_index == 0:
                        dcc.set_attribute_value(shape, 'overrideEnabled', False)

        reply['success'] = True

    @dcc.undo_decorator()
    def set_index_color(self, data, reply):
        nodes = data.get('nodes', list())
        index = data.get('index', 0)

        nodes = nodes or dcc.selected_nodes()
        if nodes:
            for obj in nodes:
                shapes = dcc.list_children_shapes(obj, all_hierarchy=True)
                if not shapes:
                    continue
                for shape in shapes:
                    if not dcc.attribute_exists(shape, 'overrideEnabled'):
                        continue
                    if not dcc.attribute_exists(shape, 'overrideColor'):
                        continue
                    if dcc.attribute_exists(shape, 'overrideRGBColors'):
                        dcc.set_attribute_value(shape, 'overrideRGBColors', False)
                    dcc.set_attribute_value(shape, 'overrideEnabled', True)
                    dcc.set_attribute_value(shape, 'overrideColor', index)
                    if index == 0:
                        dcc.set_attribute_value(shape, 'overrideEnabled', False)

        reply['success'] = True

    @dcc.undo_decorator()
    def set_rgb_color(self, data, reply):
        nodes = data.get('nodes', list())
        color = data.get('color', list())
        if not nodes:
            nodes = dcc.selected_nodes()
        if nodes:
            for obj in nodes:
                shapes = dcc.list_children_shapes(obj, all_hierarchy=True)
                if not shapes:
                    continue

                if dcc.attribute_exists(obj, 'color'):
                    dcc.set_attribute_value(obj, 'color', [color[0], color[1], color[2]])
                    for shape in shapes:
                        override_enabled = dcc.get_attribute_value(shape, 'overrideEnabled')
                        if override_enabled:
                            dcc.set_attribute_value(shape, 'overrideEnabled', False)
                            dcc.set_attribute_value(shape, 'overrideEnabled', True)
                            try:
                                dcc.set_attribute_value(
                                    shape, 'overrideColorRGB', [color[0], color[1], color[2]])
                            except Exception:
                                pass
                else:
                    for shape in shapes:
                        if not dcc.attribute_exists(shape, 'overrideEnabled'):
                            continue
                        if not dcc.attribute_exists(shape, 'overrideRGBColors'):
                            continue

                        dcc.set_attribute_value(shape, 'overrideRGBColors', True)
                        dcc.set_attribute_value(shape, 'overrideEnabled', True)
                        dcc.set_attribute_value(
                            shape, 'overrideColorRGB', [color[0], color[1], color[2]])

        reply['success'] = True

    def get_joint_radius(self, data, reply):
        result = 1.0
        joint_nodes = dcc.selected_nodes_of_type('joint')
        if joint_nodes:
            result = dcc.get_attribute_value(joint_nodes[0], 'radius')

        reply['success'] = True
        reply['result'] = result

    @dcc.undo_decorator()
    def create_control(self, data, reply):

        control_data = data['control_data']
        select_created_control = data.get('select_created_control', False)
        if not control_data:
            reply['success'] = False
            return

        curves = controllib.create_control_curve(**control_data)
        if not curves:
            reply['success'] = False
            return

        if select_created_control:
            dcc.select_node(curves[0], replace_selection=False)

        reply['success'] = True
        reply['result'] = curves

    @dcc.undo_decorator()
    def create_control_text(self, data, reply):
        text = data['text']
        font = data['font']

        if not text:
            reply['msg'] = 'Impossible to create control text because no text defined'
            reply['success'] = False
            return
        if not font:
            reply['msg'] = 'Impossible to create control text because no font defined'
            reply['success'] = False
            return

        ccs = controllib.create_text_control(text=text, font=font)

        reply['success'] = True
        reply['result'] = ccs

    @dcc.undo_decorator()
    def replace_control_curves(self, data, reply):
        target_objects = data['target_objects']
        control_type = data['control_type']
        controls_path = data['controls_path']
        keep_color = data['keep_color']

        new_controls = list()
        for control_name in target_objects:
            new_control = controllib.replace_control_curves(
                control_name, control_type=control_type, controls_path=controls_path, keep_color=keep_color)
            new_controls.append(new_control)

        reply['result'] = new_controls
        reply['success'] = True

    @dcc.undo_decorator()
    @dcc.suspend_refresh_decorator()
    def mirror_control(self, data, reply):
        mirror_plane = data['mirror_plane']
        mirror_color = data['mirror_color']
        from_name = data['from_name']
        to_name = data['to_name']
        mirror_mode = data['mirror_mode']
        mirror_replace = data['mirror_replace']
        keep_mirror_color = data['keep_mirror_color']
        mirror_axis = mirror_plane[0]

        nodes = data.get('nodes', list())
        if not nodes:
            nodes = dcc.selected_nodes()
        if not nodes:
            reply['msg'] = 'No nodes selected to mirror'
            reply['success'] = False
            return

        mirrored_controls = controllib.mirror_controls(
            nodes, mirror_axis=mirror_axis, mirror_mode=mirror_mode, mirror_color=mirror_color,
            mirror_replace=mirror_replace, from_name=from_name, to_name=to_name, keep_color=keep_mirror_color)

        reply['result'] = mirrored_controls
        reply['success'] = True

    def get_control_color(self, data, reply):

        filter_type = data['filter_type'] or filtertypes.CURVE_FILTER_TYPE

        curve_transforms = filtertypes.filter_by_type(
            filter_type, search_hierarchy=False, selection_only=True, dag=False, remove_maya_defaults=False,
            transforms_only=True, keep_order=True)
        if not curve_transforms:
            reply['msg'] = 'Impossible to get control color. Please select at least one curve object (transform)'
            reply['success'] = False
            return

        first_shape_node = shape_utils.filter_shapes_in_list(curve_transforms)[0]
        control_color = dcc.node_rgb_color(first_shape_node, linear=True)

        # We return the color in 0 to 255 range
        convert = True
        for color_channel in control_color:
            if color_channel > 1.0:
                convert = False
                break

        if convert:
            if control_color and isinstance(control_color, (list, tuple)):
                control_color = [color_channel * 255 for color_channel in control_color]

        reply['result'] = control_color
        reply['success'] = True

    @dcc.undo_decorator()
    def select_controls_by_color(self, data, reply):
        filter_type = data['filter_type'] or filtertypes.CURVE_FILTER_TYPE
        control_color = data['rgb_color']

        curve_transforms = None
        if not control_color:
            curve_transforms = filtertypes.filter_by_type(
                filter_type, search_hierarchy=False, selection_only=True, dag=False, remove_maya_defaults=False,
                transforms_only=True, keep_order=True)
        if not curve_transforms:
            curve_transforms = filtertypes.filter_by_type(
                filter_type, search_hierarchy=False, selection_only=False, dag=False, remove_maya_defaults=False,
                transforms_only=True, keep_order=True)
        if not curve_transforms:
            reply['msg'] = 'No curve objects found in the scene with the given color'
            reply['success'] = False
            return

        if not control_color:
            first_shape_node = shape_utils.filter_shapes_in_list(curve_transforms)[0]
            control_color = dcc.node_rgb_color(first_shape_node, linear=True)
            if not control_color:
                reply['msg'] = 'No color given to select objects based in its value'
                reply['success'] = False
                return

        nodes = dcc.select_nodes_by_rgb_color(node_rgb_color=control_color)

        reply['result'] = nodes
        reply['success'] = True

    def scale_control(self, data, reply):
        nodes = data.get('nodes', list())
        if not nodes:
            nodes = dcc.selected_nodes()
        if not nodes:
            reply['msg'] = 'No controls selected to scale'
            reply['success'] = False
            return
        value = data.get('value', 1.0)
        undo = data.get('undo', True)

        if undo:
            controllib.scale_controls(value, controls=nodes)
        else:
            for node in nodes:
                dcc.scale_transform_shapes(node, value)

        reply['success'] = True
