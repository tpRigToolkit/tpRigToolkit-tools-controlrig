#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains control rig server implementation
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os

import tpDcc as tp
from tpDcc.core import server


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
        else:
            super(ControlRigServer, self)._process_command(command_name, data_dict, reply_dict)

    def update_display_state(self, data, reply):
        nodes = data.get('nodes', list())
        display_index = data.get('display_index', 0)
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

    @tp.Dcc.get_undo_decorator()
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

    @tp.Dcc.get_undo_decorator()
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

    @tp.Dcc.get_undo_decorator()
    def create_control(self, data, reply):

        from tpRigToolkit.libs.controlrig.core import controllib

        control_data = data['control_data']
        controls_file = data.get('controls_file', None)
        if not control_data:
            reply['success'] = False
            return

        controls_lib = controllib.ControlLib()
        if controls_file and os.path.isfile(controls_file):
            controls_lib.controls_file = controls_file
        ccs = controls_lib.create_control(**control_data)[0]

        reply['success'] = True
        reply['result'] = ccs
