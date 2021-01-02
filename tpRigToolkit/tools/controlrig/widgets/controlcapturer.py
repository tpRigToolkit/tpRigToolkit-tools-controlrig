#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains control capturer widget for tpRigToolkit.tools.controlrig
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QButtonGroup

from tpDcc import dcc
from tpDcc.libs.qt.core import qtutils, base
from tpDcc.libs.qt.widgets import layouts, dividers, buttons, checkbox, lineedit, spinbox


class CaptureControl(base.BaseWidget, object):
    """
    Dialog to capture new controls
    """

    closed = Signal()

    def __init__(self, exec_fn, new_ctrl, default_name='new_ctrl', degree=1, periodic=True, parent=None):

        self._exec_fn = exec_fn
        self._default_name = default_name
        self._degree = degree
        self._periodic = periodic

        self._new_ctrl = new_ctrl

        super(CaptureControl, self).__init__(parent=parent)

    def ui(self):
        super(CaptureControl, self).ui()

        has_pos_xform, has_rot_xform = True, True
        for obj in dcc.selected_nodes():
            has_pos_xform &= bool(sum([dcc.get_attribute_value(obj, 't{}'.format(axis)) for axis in 'xyz']))
            has_rot_xform &= bool(sum([dcc.get_attribute_value(obj, 'r{}'.format(axis)) for axis in 'xyz']))

        self.name_line = lineedit.BaseLineEdit(text=self._default_name, parent=self)
        self.name_line.selectAll()
        self.degree_spinner = spinbox.BaseSpinBox(parent=self)
        self.degree_spinner.setValue(self._degree)
        self.degree_spinner.setToolTip('Number of degree for the curve shape')
        self.periodic_cbx = checkbox.BaseCheckBox('Periodic/Closed', parent=self)
        self.periodic_cbx.setChecked(bool(self._periodic))
        self.periodic_cbx.setToolTip('If the shape is closed?')

        self.absolute_pos = buttons.BaseRadioButton('Absolute', parent=self)
        self.absolute_pos.setChecked(not has_pos_xform)
        self.absolute_pos.setToolTip(
            'Getting translation as absolute will bake translation of the '
            'shape in world space into the shape coordinates')
        self.relative_pos = buttons.BaseRadioButton('Relative', parent=self)
        self.relative_pos.setChecked(has_pos_xform)
        self.relative_pos.setToolTip(
            'Getting translation as relative will ignore the translation of the shape in world space')
        pos_grp = QButtonGroup(self)
        pos_grp.addButton(self.absolute_pos)
        pos_grp.addButton(self.relative_pos)

        self.absolute_rot = buttons.BaseRadioButton('Absolute', parent=self)
        self.absolute_rot.setChecked(not has_rot_xform)
        self.absolute_rot.setToolTip(
            'Getting translation as absolute will bake roation of the shape in world space into the shape coordinates')
        self.relative_rot = buttons.BaseRadioButton('Relative', parent=self)
        self.relative_rot.setChecked(has_rot_xform)
        self.relative_rot.setToolTip(
            'Getting translation as relative will ignore the rotation of the shape in world space')
        rot_grp = QButtonGroup(self)
        rot_grp.addButton(self.absolute_rot)
        rot_grp.addButton(self.relative_rot)

        self.ok_btn = buttons.BaseButton('Capture', parent=self)
        self.cancel_btn = buttons.BaseButton('Cancel', parent=self)

        self.main_layout.addLayout(qtutils.get_line_layout('Control Name : ', self, self.name_line))

        # If there is more than one shape selected we allow the user to keep the individual shape's settings
        self.keep = None
        if len(dcc.selected_nodes()) > 1:
            self.keep = checkbox.BaseCheckBox('Keep individual shape\'s setting', parent=self)
            self.keep.stateChanged.connect(self.degree_spinner.setDisabled)
            self.keep.stateChanged.connect(self.periodic_cbx.setDisabled)
            self.main_layout.addWidget(self.keep)

        self.main_layout.addLayout(
            qtutils.get_line_layout('Shape Degree : ', self, self.degree_spinner, self.periodic_cbx))
        self.main_layout.addLayout(
            qtutils.get_line_layout('Position Space : ', self, self.absolute_pos, self.relative_pos))
        self.main_layout.addLayout(
            qtutils.get_line_layout('Rotation Space : ', self, self.absolute_rot, self.relative_rot))
        self.main_layout.addLayout(
            dividers.DividerLayout())

        bottom_layout = layouts.HorizontalLayout()
        bottom_layout.addWidget(self.ok_btn)
        bottom_layout.addWidget(self.cancel_btn)
        self.main_layout.addLayout(bottom_layout)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self._on_cancel()
        elif key == Qt.Key_Return:
            self._on_create()
        super(CaptureControl, self).keyPressEvent(event)

    def setup_signals(self):
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.ok_btn.clicked.connect(self._on_create)

    def _on_cancel(self):
        self.close()
        self.closed.emit()

    def _on_create(self):
        args = [self._new_ctrl, self.name_line.text(), self.absolute_pos.isChecked(), self.absolute_rot.isChecked()]
        if self.keep and not self.keep.isChecked() or not self.keep:
            args.append(self.degree_spinner.value())
            args.append(self.periodic_cbx.isChecked())
        self._exec_fn(*args)
        self.close()
        self.closed.emit()
