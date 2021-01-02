#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains control rig server implementation for 3ds Max
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from tpDcc import dcc
from tpDcc.core import server

from tpDcc.dccs.maya.core import filtertypes


class ControlRigServer(server.DccServer, object):
    PORT = 13144

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
        elif command_name == 'mirror_control':
            self.mirror_control(data_dict, reply_dict)
        elif command_name == 'get_control_color':
            self.get_control_color(data_dict, reply_dict)
        elif command_name == 'select_controls_by_color':
            self.select_controls_by_color(data_dict, reply_dict)
        else:
            super(ControlRigServer, self)._process_command(command_name, data_dict, reply_dict)

    def update_selected_nodes(self, data, reply):
        nodes = data.get('nodes', list())
        deselect = data.get('deselect', True)

        valid_nodes = list()

        reply['success'] = True
        reply['result'] = valid_nodes

    def filter_transforms_with_shapes(self, data, reply):
        nodes = data.get('nodes', list())
        children = data.get('hierarchy', False)

        transforms_with_shapes = list()

        reply['success'] = True
        reply['result'] = transforms_with_shapes

    @dcc.undo_decorator()
    def update_display_state(self, data, reply):
        nodes = data.get('nodes', list())
        display_index = data.get('display_index', 0)        # 0 = Normal; 1 = Template; 2 = Reference

        reply['success'] = True

    @dcc.undo_decorator()
    def set_index_color(self, data, reply):
        nodes = data.get('nodes', list())
        index = data.get('index', 0)

        reply['success'] = True

    @dcc.undo_decorator()
    def set_rgb_color(self, data, reply):
        nodes = data.get('nodes', list())
        color = data.get('color', list())

        reply['success'] = True

    def get_joint_radius(self, data, reply):
        result = 1.0

        reply['success'] = True
        reply['result'] = result

    @dcc.undo_decorator()
    def create_control(self, data, reply):

        ccs = list()

        reply['success'] = True
        reply['result'] = ccs

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

        ccs = list()

        reply['success'] = True
        reply['result'] = ccs

    @dcc.undo_decorator()
    @dcc.suspend_refresh_decorator()
    def mirror_control(self, data, reply):
        mirror_plane = data['mirror_plane']
        mirror_color = data['mirror_color']
        from_name = data['from_name']
        to_name = data['to_name']
        mirror_mode = data['mirror_mode']
        mirror_replace = data['mirror_replace']

        reply['result'] = list()
        reply['success'] = True

    def get_control_color(self, data, reply):

        filter_type = data['filter_type'] or filtertypes.CURVE_FILTER_TYPE

        control_color = [0.0, 0.0, 0.0]

        reply['result'] = control_color
        reply['success'] = True

    @dcc.undo_decorator()
    def select_controls_by_color(self, data, reply):
        filter_type = data['filter_type'] or filtertypes.CURVE_FILTER_TYPE
        control_color = data['rgb_color']

        nodes = list()

        reply['result'] = nodes
        reply['success'] = True
