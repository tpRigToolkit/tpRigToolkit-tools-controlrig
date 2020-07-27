import os
import sys

from Qt.QtWidgets import *
from shiboken2 import wrapInstance


import maya.cmds as cmds
import maya.OpenMayaUI as OpenMayaUI

server_path = r'D:\tpDcc\tpDcc-core\tpDcc\core'
if server_path not in sys.path:
    sys.path.append(server_path)

# Useful for DEV
modules_to_reload = ('tpDcc', 'tpRigToolkit')
for k in sys.modules.keys():
    if k.startswith(modules_to_reload):
        del sys.modules[k]

# We use it to have autocompletion in PyCharm
if False:
    import tpDcc as tp

import server
reload(server)


def maya_main_window():
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QWidget)


class ControlRigServer(server.DccServer, object):
    PORT = 13144

    def __init__(self):
        super(ControlRigServer, self).__init__(maya_main_window())

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


try:
    control_rig_server.deleteLater()  # pylint: disable=E0601,E0602
except Exception:
    pass
cmds.evalDeferred("control_rig_server = ControlRigServer()")