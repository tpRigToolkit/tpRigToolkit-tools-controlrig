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
import importlib

import tpDcc as tp
from tpDcc.core import tool
from tpDcc.libs.qt.widgets import toolset

# Defines ID of the tool
TOOL_ID = 'tpRigToolkit-tools-controlrig'


class ControlRigTool(tool.DccTool, object):
    def __init__(self, *args, **kwargs):
        super(ControlRigTool, self).__init__(*args, **kwargs)

    @classmethod
    def config_dict(cls, file_name=None):
        base_tool_config = tool.DccTool.config_dict(file_name=file_name)
        tool_config = {
            'name': 'Control Rig',
            'id': TOOL_ID,
            'supported_dccs': {'maya': ['2017', '2018', '2019', '2020']},
            'logo': 'controlrig',
            'icon': 'controlrig',
            'tooltip': 'Tool to create rig curve based controls',
            'tags': ['tpRigToolkit', 'rig', 'control', 'rig'],
            'logger_dir': os.path.join(os.path.expanduser('~'), 'tpRigToolkit', 'logs', 'tools'),
            'logger_level': 'INFO',
            'is_checkable': False,
            'is_checked': False,
            'menu_ui': {'label': 'Control Rig', 'load_on_startup': False, 'color': '', 'background_color': ''}
        }
        base_tool_config.update(tool_config)

        return base_tool_config

    def launch(self, *args, **kwargs):
        return self.launch_frameless(*args, **kwargs)


class ControlRigToolset(toolset.ToolsetWidget, object):

    ID = TOOL_ID

    def __init__(self, *args, **kwargs):

        self._as_selector = kwargs.pop('as_selector', False)
        self._selector_parent = kwargs.pop('selector_parent', None)
        self._controls_path = kwargs.pop('controls_path', None)
        self._control_data = kwargs.pop('control_data', None)

        super(ControlRigToolset, self).__init__(*args, **kwargs)

    @property
    def control_data(self):
        widget = self._widgets[0]
        return widget.control_data

    def setup_client(self):

        from tpRigToolkit.tools.controlrig.core import controlrigclient

        self._client = controlrigclient.ControlRigClient()
        self._client.signals.dccDisconnected.connect(self._on_dcc_disconnected)

        if not tp.is_standalone():
            dcc_mod_name = '{}.dccs.{}.controlrigserver'.format(TOOL_ID.replace('-', '.'), tp.Dcc.get_name())
            try:
                mod = importlib.import_module(dcc_mod_name)
                if hasattr(mod, 'ControlRigServer'):
                    server = mod.ControlRigServer(self, client=self._client, update_paths=False)
                    self._client.set_server(server)
                    self._update_client()
            except Exception as exc:
                tp.logger.warning(
                    'Impossible to launch ControlRig server! Error while importing: {} >> {}'.format(dcc_mod_name, exc))
                return
        else:
            self._update_client()

    def contents(self):

        from tpRigToolkit.tools.controlrig.widgets import controlrig

        if self._as_selector:
            joint_orient = controlrig.ControlSelector(
                client=self._client, controls_path=self._controls_path, parent=self._selector_parent or self)
        else:
            joint_orient = controlrig.ControlsWidget(
                client=self._client, controls_path=self._controls_path, parent=self)

        if self._control_data:
            joint_orient.set_control_data(self._control_data)

        return [joint_orient]


if __name__ == '__main__':
    import tpDcc
    import tpRigToolkit.loader
    tpRigToolkit.loader.init(dev=False)

    tpDcc.ToolsMgr().launch_tool_by_id('tpRigToolkit-tools-controlrig')
