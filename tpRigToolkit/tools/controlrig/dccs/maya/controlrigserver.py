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

import os

import tpDcc as tp
from tpDcc.core import server

from tpDcc.dccs.maya.core import filtertypes, shape as shape_utils

from tpRigToolkit.libs.controlrig.core import controllib


class ControlRigServer(server.DccServer, object):
    PORT = 13144

    def _process_command(self, command_name, data_dict, reply_dict):
        if command_name == 'update_display_state':
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
        elif command_name == 'mirror_control':
            self.mirror_control(data_dict, reply_dict)
        elif command_name == 'get_control_color':
            self.get_control_color(data_dict, reply_dict)
        elif command_name == 'select_controls_by_color':
            self.select_controls_by_color(data_dict, reply_dict)
        else:
            super(ControlRigServer, self)._process_command(command_name, data_dict, reply_dict)

    @tp.Dcc.undo_decorator()
    def update_display_state(self, data, reply):
        nodes = data.get('nodes', list())
        display_index = data.get('display_index', 0)        # 0 = Normal; 1 = Template; 2 = Reference

        if not nodes:
            nodes = tp.Dcc.selected_nodes()
        if nodes:
            for obj in nodes:
                tp.Dcc.clean_construction_history(obj)
                shapes = tp.Dcc.list_children_shapes(obj, all_hierarchy=True)
                for shape in shapes:
                    tp.Dcc.set_attribute_value(shape, 'overrideEnabled', True)
                    tp.Dcc.set_attribute_value(shape, 'overrideDisplayType', display_index)
                    if display_index == 0:
                        tp.Dcc.set_attribute_value(shape, 'overrideEnabled', False)

        reply['success'] = True

    @tp.Dcc.undo_decorator()
    def set_index_color(self, data, reply):
        nodes = data.get('nodes', list())
        index = data.get('index', 0)
        if not nodes:
            nodes = tp.Dcc.selected_nodes()
        if nodes:
            for obj in nodes:
                shapes = tp.Dcc.list_children_shapes(obj, all_hierarchy=True)
                if not shapes:
                    continue
                for shape in shapes:
                    if not tp.Dcc.attribute_exists(shape, 'overrideEnabled'):
                        continue
                    if not tp.Dcc.attribute_exists(shape, 'overrideColor'):
                        continue
                    if tp.Dcc.attribute_exists(shape, 'overrideRGBColors'):
                        tp.Dcc.set_attribute_value(shape, 'overrideRGBColors', False)
                    tp.Dcc.set_attribute_value(shape, 'overrideEnabled', True)
                    tp.Dcc.set_attribute_value(shape, 'overrideColor', index)
                    if index == 0:
                        tp.Dcc.set_attribute_value(shape, 'overrideEnabled', False)

        reply['success'] = True

    @tp.Dcc.undo_decorator()
    def set_rgb_color(self, data, reply):
        nodes = data.get('nodes', list())
        color = data.get('color', list())
        if not nodes:
            nodes = tp.Dcc.selected_nodes()
        if nodes:
            for obj in nodes:
                shapes = tp.Dcc.list_children_shapes(obj, all_hierarchy=True)
                if not shapes:
                    continue

                if tp.Dcc.attribute_exists(obj, 'color'):
                    tp.Dcc.set_attribute_value(obj, 'color', [color[0], color[1], color[2]])
                    for shape in shapes:
                        override_enabled = tp.Dcc.get_attribute_value(shape, 'overrideEnabled')
                        if override_enabled:
                            tp.Dcc.set_attribute_value(shape, 'overrideEnabled', False)
                            tp.Dcc.set_attribute_value(shape, 'overrideEnabled', True)
                else:
                    for shape in shapes:
                        if not tp.Dcc.attribute_exists(shape, 'overrideEnabled'):
                            continue
                        if not tp.Dcc.attribute_exists(shape, 'overrideRGBColors'):
                            continue

                        tp.Dcc.set_attribute_value(shape, 'overrideRGBColors', True)
                        tp.Dcc.set_attribute_value(shape, 'overrideEnabled', True)
                        tp.Dcc.set_attribute_value(
                            shape, 'overrideColorRGB', [color[0], color[1], color[2]])

        reply['success'] = True

    def get_joint_radius(self, data, reply):
        result = 1.0
        joint_nodes = tp.Dcc.selected_nodes_of_type('joint')
        if joint_nodes:
            result = tp.Dcc.get_attribute_value(joint_nodes[0], 'radius')

        reply['success'] = True
        reply['result'] = result

    @tp.Dcc.undo_decorator()
    def create_control(self, data, reply):

        control_data = data['control_data']
        controls_file = data.get('controls_file', None)
        select_created_control = data.get('select_created_control', False)
        if not control_data:
            reply['success'] = False
            return

        controls_lib = controllib.ControlLib()
        if controls_file and os.path.isfile(controls_file):
            controls_lib.controls_file = controls_file
        ccs = controls_lib.create_control(**control_data)

        if select_created_control:
            controls_to_select = [ctrl[0] for ctrl in ccs]
            tp.Dcc.select_node(controls_to_select, replace_selection=False)

        reply['success'] = True
        reply['result'] = ccs

    @tp.Dcc.undo_decorator()
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

    @tp.Dcc.undo_decorator()
    @tp.Dcc.suspend_refresh_decorator()
    def mirror_control(self, data, reply):
        mirror_plane = data['mirror_plane']
        mirror_color = data['mirror_color']
        from_name = data['from_name']
        to_name = data['to_name']
        mirror_mode = data['mirror_mode']
        mirror_replace = data['mirror_replace']

        mirror_axis_index = 0
        mirror_axis = mirror_plane[0]
        if mirror_axis.upper() == 'Y':
            mirror_axis_index = 1
        elif mirror_axis.upper() == 'Z':
            mirror_axis_index = 2

        nodes = data.get('nodes', list())
        if not nodes:
            nodes = tp.Dcc.selected_nodes()
        if not nodes:
            reply['msg'] = 'No nodes selected to mirror'
            reply['success'] = False
            return

        for obj in nodes:
            shapes = tp.Dcc.list_shapes(obj)
            if not tp.Dcc.check_object_type(shapes[0], 'nurbsCurve'):
                continue
            orig_pos = tp.Dcc.node_world_space_pivot(obj)
            orig_rot = tp.Dcc.node_world_space_rotation(obj)
            obj_parent = tp.Dcc.node_parent(obj)

            tp.Dcc.move_node(obj, 0, 0, 0, world_space=True)
            # tp.Dcc.rotate_node(obj, 0, 0, 0, world_space=True)

            curve_target = tp.Dcc.duplicate_object(obj, return_roots_only=True)[0]

            new_curve = False
            curve_target_name = obj.replace(from_name, to_name)
            if tp.Dcc.object_exists(curve_target_name) and mirror_replace:
                mirror_target = curve_target_name
                tp.Dcc.match_transform(mirror_target, curve_target)
                curve_target = controllib.ControlLib.set_shape(mirror_target, [curve_target], keep_color=True)
            else:
                empty_group = tp.Dcc.create_empty_group()
                tp.Dcc.set_parent(curve_target, empty_group)
                tp.Dcc.set_attribute_value(empty_group, 'scale{}'.format(mirror_axis.upper()), -1)
                tp.Dcc.set_parent_to_world(curve_target)
                tp.Dcc.freeze_transforms(curve_target, translate=False, rotate=False, scale=True, clean_history=False)
                tp.Dcc.delete_object(empty_group)
                new_curve = True

            # This is a method for mirror shapes without using the transform. Not fully working because
            # not all CVs are moved properly
            # for crv_shape in shapes:
            #     for i in range(tp.Dcc.get_attribute_value(crv_shape, 'spans')):
            #         cv_pos = tp.Dcc.node_world_space_translation('{}.cv[{}]'.format(obj, i))
            #         cv_pos[mirror_axis_index] *= -1
            #         tp.Dcc.move_node(
            #             '{}.cv[{}]'.format(curve_target, i), cv_pos[0], cv_pos[1], cv_pos[2], world_space=True)

            if mirror_color:
                curve_target_shapes = tp.Dcc.list_shapes(curve_target)
                for curve_target_shape in curve_target_shapes:
                    tp.Dcc.set_node_color(curve_target_shape, mirror_color)

            tp.Dcc.move_node(obj, orig_pos[0], orig_pos[1], orig_pos[2], world_space=True)
            tp.Dcc.rotate_node(obj, orig_rot[0], orig_rot[1], orig_rot[2], world_space=True)
            if obj_parent:
                tp.Dcc.set_parent_to_world(curve_target)

            if not new_curve and mirror_mode == 0:
                tp.Dcc.move_node(curve_target, 0, 0, 0, world_space=True)
            elif mirror_mode == 1:
                # original
                tp.Dcc.move_node(curve_target, orig_pos[0], orig_pos[1], orig_pos[2], world_space=True)
            #     tp.Dcc.rotate_node(curve_target, orig_rot[0], orig_rot[1], orig_rot[2], world_space=True)
            elif mirror_mode == 2 and new_curve:
                # mirrored
                mirrored_pos = orig_pos[:]
                mirrored_pos[mirror_axis_index] *= -1
                tp.Dcc.move_node(curve_target, mirrored_pos[0], mirrored_pos[1], mirrored_pos[2], world_space=True)

            if new_curve:
                tp.Dcc.rename_node(curve_target, obj.replace(from_name, to_name))

        reply['result'] = list()
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
        control_color = tp.Dcc.node_rgb_color(first_shape_node, linear=True)

        # We return the color in 0 to 255 range
        if control_color and isinstance(control_color, (list, tuple)):
            control_color = [color_channel * 255 for color_channel in control_color]

        reply['result'] = control_color
        reply['success'] = True

    @tp.Dcc.undo_decorator()
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
            control_color = tp.Dcc.node_rgb_color(first_shape_node, linear=True)
            if not control_color:
                reply['msg'] = 'No color given to select objects based in its value'
                reply['success'] = False
                return

        nodes = tp.Dcc.select_nodes_by_rgb_color(node_rgb_color=control_color)

        reply['result'] = nodes
        reply['success'] = True
