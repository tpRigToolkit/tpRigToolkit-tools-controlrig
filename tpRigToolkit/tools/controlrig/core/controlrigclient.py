#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains control rig client implementation
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os

from tpDcc.core import client
from tpDcc.libs.python import python, path as path_utils
import tpRigToolkit.libs.controlrig


class ControlRigClient(client.DccClient, object):

    PORT = 13144

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def _get_paths_to_update(self):
        paths_to_update = super(ControlRigClient, self)._get_paths_to_update()

        paths_to_update['tpRigToolkit.libs.controlrig'] = path_utils.clean_path(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(tpRigToolkit.libs.controlrig.__file__)))))

        return paths_to_update

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def update_display_state(self, nodes=None, display_index=0):
        cmd = {
            'cmd': 'update_display_state',
            'nodes': python.force_list(nodes),
            'display_index': display_index
        }

        reply_dict = self.send(cmd)

        if not self.is_valid_reply(reply_dict):
            return list()

        return reply_dict['success']

    def set_index_color(self, index):
        cmd = {
            'cmd': 'set_index_color',
            'index': index
        }

        reply_dict = self.send(cmd)

        if not self.is_valid_reply(reply_dict):
            return list()

        return reply_dict['success']

    def set_rgb_color(self, color):
        cmd = {
            'cmd': 'set_rgb_color',
            'color': color
        }

        reply_dict = self.send(cmd)

        if not self.is_valid_reply(reply_dict):
            return list()

        return reply_dict['success']

    def get_joint_radius(self):
        cmd = {
            'cmd': 'get_joint_radius'
        }

        reply_dict = self.send(cmd)

        if not self.is_valid_reply(reply_dict):
            return list()

        return reply_dict['result']

    def create_control(self, control_data, control_file=None, select_created_control=False):

        cmd = {
            'cmd': 'create_control',
            'control_data': control_data,
            'controls_file': control_file,
            'select_created_control': select_created_control
        }

        reply_dict = self.send(cmd)

        if not self.is_valid_reply(reply_dict):
            return list()

        return reply_dict['result']

    def create_control_text(self, control_text, control_font):

        cmd = {
            'cmd': 'create_control_text',
            'text': control_text,
            'font': control_font
        }

        reply_dict = self.send(cmd)

        if not self.is_valid_reply(reply_dict):
            return list()

        return reply_dict['result']

    def mirror_control(self, mirror_plane, mirror_color_list, from_name, to_name, mirror_mode_index, mirror_replace):

        cmd = {
            'cmd': 'mirror_control',
            'mirror_plane': mirror_plane,
            'mirror_color': mirror_color_list,
            'from_name': from_name,
            'to_name': to_name,
            'mirror_mode': mirror_mode_index,
            'mirror_replace': mirror_replace
        }

        reply_dict = self.send(cmd)

        if not self.is_valid_reply(reply_dict):
            return list()

        return reply_dict['result']

    def get_control_color(self, filter_type=None):
        cmd = {
            'cmd': 'get_control_color',
            'filter_type': filter_type
        }

        reply_dict = self.send(cmd)

        if not self.is_valid_reply(reply_dict):
            return list()

        return reply_dict['result']

    def select_controls_by_color(self, rgb_color=None, filter_type=None):
        cmd = {
            'cmd': 'select_controls_by_color',
            'rgb_color': rgb_color,
            'filter_type': filter_type
        }

        reply_dict = self.send(cmd)

        if not self.is_valid_reply(reply_dict):
            return list()

        return reply_dict['result']
