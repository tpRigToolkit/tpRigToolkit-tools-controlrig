#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for control selector widget
"""

from __future__ import print_function, division, absolute_import

from tpDcc.libs.qt.widgets import buttons

from tpRigToolkit.tools.controlrig.core import view


class ControlSelector(view.ControlRigView, object):

    def __init__(self, model, controller, parent=None):

        self._control_data = dict()
        self._parent = parent

        super(ControlSelector, self).__init__(model=model, controller=controller, parent=parent)

    @property
    def control_data(self):
        return self._control_data

    def ui(self):
        super(ControlSelector, self).ui()

        for widget in [self._options_expander, self._capture_btn, self._remove_btn, self._create_btn,
                       self._assign_btn, self._name_widget]:
            widget.setVisible(False)
            widget.setEnabled(False)

        self._select_btn = buttons.BaseButton('Select Control')
        self._create_layout.addWidget(self._select_btn)

    def setup_signals(self):
        super(ControlSelector, self).setup_signals()
        self._select_btn.clicked.connect(self._on_select_control)

    def _on_select_control(self):
        self._control_data = self.get_selected_control_item_data()
        parent = self._parent or self.parent()
        if parent:
            parent.close()
        else:
            self.close()
