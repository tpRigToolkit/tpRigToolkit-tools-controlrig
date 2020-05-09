#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to create rig curve based controls
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os

from tpDcc.core import tool
from tpDcc.libs.qt.widgets import toolset

# Defines ID of the tool
TOOL_ID = 'tpRigToolkit-tools-controlrig'

# We skip the reloading of this module when launching the tool
no_reload = True


class ControlRigTool(tool.DccTool, object):
    def __init__(self, *args, **kwargs):
        super(ControlRigTool, self).__init__(*args, **kwargs)

    @classmethod
    def config_dict(cls, file_name=None):
        base_tool_config = tool.DccTool.config_dict(file_name=file_name)
        tool_config = {
            'name': 'Control Rig',
            'id': 'tpRigToolkit-tools-controlrig',
            'logo': 'controlrig',
            'icon': 'controlrig',
            'tooltip': 'Tool to create rig curve based controls',
            'tags': ['tpRigToolkit', 'rig', 'control', 'rig'],
            'logger_dir': os.path.join(os.path.expanduser('~'), 'tpRigToolkit', 'logs', 'tools'),
            'logger_level': 'INFO',
            'is_checkable': False,
            'is_checked': False,
            'import_order': ['widgets', 'core'],
            'menu_ui': {'label': 'Control Rig', 'load_on_startup': False, 'color': '', 'background_color': ''},
            'menu': [
                {'label': 'Control Rig',
                 'type': 'menu', 'children': [{'id': 'tpRigToolkit-tools-controlrig', 'type': 'tool'}]}],
            'shelf': [
                {'name': 'Control Rig',
                 'children': [{'id': 'tpRigToolkit-tools-controlrig', 'display_label': False, 'type': 'tool'}]}
            ]
        }
        base_tool_config.update(tool_config)

        return base_tool_config

    def launch(self, *args, **kwargs):
        return self.launch_frameless(*args, **kwargs)


class ControlRigToolset(toolset.ToolsetWidget, object):

    ID = TOOL_ID

    def __init__(self, *args, **kwargs):
        super(ControlRigToolset, self).__init__(*args, **kwargs)

    def contents(self):

        from tpRigToolkit.tools.controlrig.widgets import controlrig
        joint_orient = controlrig.ControlsWidget(parent=self)

        return [joint_orient]
