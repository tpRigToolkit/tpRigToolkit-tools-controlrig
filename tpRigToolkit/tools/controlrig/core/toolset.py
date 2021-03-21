#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to create rig curve based controls
"""

from __future__ import print_function, division, absolute_import

from tpDcc.libs.qt.widgets import toolset


class ControlRigToolset(toolset.ToolsetWidget, object):
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

    def contents(self):

        from tpRigToolkit.tools.controlrig.core import model, view, controller

        control_rig_model = model.ControlRigModel()
        control_rig_controller = controller.ControlRigController(client=self._client, model=control_rig_model)

        if self._as_selector:
            control_rig_view = view.ControlSelector(
                model=control_rig_model, controller=control_rig_controller, parent=self._selector_parent or self)
            self._title_frame.setVisible(False)
        else:
            control_rig_view = view.ControlRigView(
                model=control_rig_model, controller=control_rig_controller, parent=self)

        if self._controls_path:
            control_rig_controller.set_controls_path(self._controls_path)
        if self._control_data:
            control_rig_controller.set_control_data(self._control_data)

        return [control_rig_view]
