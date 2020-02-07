#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to create and manage rig curve controls
"""

from __future__ import print_function, division, absolute_import

import os
import logging
from copy import copy
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpQtLib
import tpDccLib as tp
from tpPyUtils import decorators
from tpQtLib.core import qtutils, base, color
from tpQtLib.widgets import search, lineedit, spinbox, expandables, splitters

import tpRigToolkit
from tpRigToolkit.core import resource
from tpRigToolkit.tools.controlrig.core import controldata, controllib
from tpRigToolkit.tools.controlrig.widgets import controlviewer, controlcapturer, controlslist

if tp.is_maya():
    import tpMayaLib as maya

LOGGER = logging.getLogger('tpRigToolkit')


class ControlRigTool(tpRigToolkit.Tool, object):
    """
    Manager UI class
    """

    def __init__(self, config):
        super(ControlRigTool, self).__init__(config=config)

    def ui(self):
        super(ControlRigTool, self).ui()

        self._controls_widget = ControlsWidget()
        self.main_layout.addWidget(self._controls_widget)


@decorators.Singleton
class ControlLib(controllib.ControlLib, object):
    pass


class ControlsWidget(base.BaseWidget, object):

    CONTROLS_LIB = ControlLib
    CONTROLS_LIST_CLASS = controlslist.ControlsList

    def __init__(self, controls_path=None, parent=None):
        super(ControlsWidget, self).__init__(parent=parent)
        if controls_path:
            self.set_controls_file(controls_path)
        else:
            self._init_data()

    def ui(self):
        super(ControlsWidget, self).ui()

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.main_layout.addWidget(self.main_splitter)

        controls_widget = QWidget()
        controls_layout = QVBoxLayout()
        controls_widget.setLayout(controls_layout)
        self.main_splitter.addWidget(controls_widget)

        properties_widget = QWidget()
        properties_layout = QVBoxLayout()
        properties_widget.setLayout(properties_layout)
        self.main_splitter.addWidget(properties_widget)

        self.controls_filter = search.SearchFindWidget(parent=self)
        controls_layout.addWidget(self.controls_filter)

        self.controls_list = self.CONTROLS_LIST_CLASS(parent=self)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(2)
        self.capture_btn = QPushButton('')
        self.capture_btn.setIcon(resource.ResourceManager().icon(name='camera', theme='color'))
        self.remove_btn = QPushButton('')
        self.remove_btn.setIcon(resource.ResourceManager().icon(name='delete', theme='color'))
        buttons_layout.addWidget(self.capture_btn)
        buttons_layout.addWidget(self.remove_btn)
        buttons_layout.setStretchFactor(self.capture_btn, 4)

        controls_layout.addWidget(self.controls_list)
        controls_layout.addLayout(buttons_layout)

        self.props_splitter = QSplitter(Qt.Vertical)
        properties_layout.addWidget(self.props_splitter)

        self.controls_viewer = controlviewer.ControlViewer(parent=self)
        self.props_splitter.addWidget(self.controls_viewer)

        props_widget = QWidget()
        props_layout = QVBoxLayout()
        props_widget.setLayout(props_layout)
        self.props_splitter.addWidget(props_widget)

        self.name_line = lineedit.BaseLineEdit(default='new_ctrl', parent=self)
        name_layout = qtutils.get_line_layout('  Name :   ', self, self.name_line)
        name_layout.setSpacing(0)
        name_layout.setContentsMargins(0, 0, 0, 0)

        self.radius = spinbox.DragDoubleSpinBoxLine(start=1.0, max=100, positive=True, parent=self)
        self.offset_x = spinbox.DragDoubleSpinBoxLine(min=-1000, max=1000, parent=self)
        self.offset_y = spinbox.DragDoubleSpinBoxLine(min=-1000, max=1000, parent=self)
        self.offset_z = spinbox.DragDoubleSpinBoxLine(min=-1000, max=1000, parent=self)
        self.offset = lambda: [self.offset_x.value(), self.offset_y.value(), self.offset_z.value()]

        self.factor_x = spinbox.DragDoubleSpinBoxLine(start=1.0, min=-1000, max=1000, parent=self)
        self.factor_y = spinbox.DragDoubleSpinBoxLine(start=1.0, min=-1000, max=1000, parent=self)
        self.factor_z = spinbox.DragDoubleSpinBoxLine(start=1.0, min=-1000, max=1000, parent=self)
        self.factor = lambda: [self.factor_x.value(), self.factor_y.value(), self.factor_z.value()]

        for offset in (self.offset_x, self.offset_y, self.offset_z):
            offset.setToolTip('Set the position offset of the shape(s)')
        for factor in (self.factor_x, self.factor_y, self.factor_z):
            factor.setToolTip('Set the scale factor of the shape(s)')

        self.rotate_order = QComboBox(parent=self)
        self.rotate_order.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        for x in ['XYZ', 'YXZ', 'ZYX']:
            it = QStandardItem(x[0])
            self.rotate_order.addItem(x[0], it)
            self.rotate_order.setItemData(controldata.axis_eq[x[0]], x)

        self.color_picker = color.ColorSwatch()
        self.color_picker.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        col_layout = qtutils.get_column_layout(
            name_layout,
            qtutils.get_line_layout('Radius : ', self, self.radius),
            qtutils.get_line_layout('Offset : ', self, self.offset_x, self.offset_y, self.offset_z),
            qtutils.get_line_layout('Factor : ', self, self.factor_x, self.factor_y, self.factor_z),
            qtutils.get_line_layout('Axis : ', self, self.rotate_order),
            qtutils.get_line_layout('Color : ', self, self.color_picker)
        )
        col_layout.setContentsMargins(5, 10, 0, 5)

        parenting_expander = expandables.ExpanderWidget(parent=self)
        parenting_expander.setRolloutStyle(expandables.ExpanderStyles.Maya)
        parenting_expander.setDragDropMode(expandables.ExpanderDragDropModes.NoDragDrop)

        parenting_widget = QWidget()
        parenting_layout = QVBoxLayout()
        parenting_widget.setLayout(parenting_layout)
        self.zero_control = QCheckBox('Zero Control', parent=self)
        self.parent_shape = QCheckBox('Parent Shape to Transform', parent=self)
        depth_layout = QHBoxLayout()
        depth_layout.addWidget(self.zero_control)
        self.zero_iter = QSpinBox(parent=self)
        self.zero_iter.setMinimum(1)
        self.zero_iter.setMaximum(5)
        self.zero_iter.setEnabled(False)
        zero_depth_lbl = QLabel('depth', parent=self)
        depth_layout.addWidget(self.zero_iter)
        depth_layout.addWidget(zero_depth_lbl)
        parenting_layout.addLayout(depth_layout)
        parenting_layout.addWidget(self.parent_shape)
        parenting_expander.addItem(title='Parenting', widget=parenting_widget, collapsed=False)

        mirror_expander = expandables.ExpanderWidget(parent=self)
        mirror_expander.setRolloutStyle(expandables.ExpanderStyles.Maya)
        mirror_expander.setDragDropMode(expandables.ExpanderDragDropModes.NoDragDrop)

        mirror_widget = QWidget()
        mirror_layout = QVBoxLayout()
        mirror_widget.setLayout(mirror_layout)
        self.mirror = QButtonGroup(parent=self)
        self.none = QPushButton('None', parent=self)
        self.none.setStyleSheet("QPushButton:checked{background:#6a485c;}")
        self.none.setCheckable(True)
        self.none.setChecked(True)
        self.none.value = None
        self.mirror.addButton(self.none)

        self.xy = QPushButton('XY', self)
        self.yz = QPushButton('YZ', self)
        self.zx = QPushButton('ZX', self)

        def mirror_click(button, event):
            enabled = not button.isChecked() and button is not self.none
            # for w in (self.mirror_color, self.from_name, self.to_name, self.mirror_reparent):
            #     w.setEnabled(enabled)
            if button.isChecked():
                self.none.setChecked(True)
                self.mirror.buttonClicked.emit(self.none)
            else:
                QPushButton.mousePressEvent(button, event)

        self.none.mousePressEvent = partial(mirror_click, self.none)
        for btn in (self.xy, self.yz, self.zx):
            self.mirror.addButton(btn)
            btn.setStyleSheet(self.none.styleSheet())
            btn.setToolTip('Set mirror mode on {}plane'.format(btn.text()))
            btn.setCheckable(True)
            btn.value = btn.text()
            btn.mousePressEvent = partial(mirror_click, btn)

        mirror_layout.addLayout(qtutils.get_line_layout('Axis : ', self, self.none, self.xy, self.yz, self.zx))

        self.mirror_color = color.ColorSwatch(parent=self)
        self.mirror_color.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        mirror_layout.addLayout(qtutils.get_line_layout('Mirror Color : ', self, self.mirror_color))
        self.from_name = lineedit.BaseLineEdit(default='from', parent=self)
        self.to_name = lineedit.BaseLineEdit(default='to', parent=self)
        mirror_layout.addLayout(
            qtutils.get_line_layout('Name Pattern : ', self, self.from_name, QLabel(u'\u25ba', self), self.to_name))

        self.mirror_reparent = QPushButton('Mirror Shape(s)', self)
        for w in (self.mirror_color, self.from_name, self.to_name, self.mirror_reparent):
            w.setEnabled(False)
        mirror_layout.addWidget(self.mirror_reparent)

        expander_item = mirror_expander.addItem(title='Mirroring', widget=mirror_widget, collapsed=False)

        props_layout.addLayout(col_layout)
        props_layout.addWidget(parenting_expander)
        props_layout.addWidget(mirror_expander)

        self.props_splitter.setStretchFactor(0, 2)

        self.main_layout.addLayout(splitters.SplitterLayout())

        create_layout = QHBoxLayout()
        create_layout.setContentsMargins(2, 2, 2, 2)
        create_layout.setSpacing(2)
        self.create_btn = QPushButton('Create Control')
        self.assign_btn = QPushButton('Assign Control')
        create_layout.addWidget(self.create_btn)
        create_layout.addWidget(self.assign_btn)

        self.main_layout.addLayout(create_layout)

    def setup_signals(self):
        self.main_splitter.splitterMoved.connect(self._on_splitter_moved)
        self.props_splitter.splitterMoved.connect(self._on_splitter_moved)
        self.controls_filter.textChanged.connect(self._on_filter_controls_list)
        self.controls_list.itemUpdated.connect(self._on_update_controls_list)
        self.controls_list.itemSelectionChanged.connect(self._on_display_control)
        self.capture_btn.clicked.connect(self._on_capture_control)
        self.remove_btn.clicked.connect(self._on_remove_control)
        self.radius.textChanged.connect(self._on_rescale_viewer)
        self.radius.textChanged.connect(self._on_display_control)
        for offset in (self.offset_x, self.offset_y, self.offset_z):
            offset.textChanged.connect(self._on_display_control)
        for factor in (self.factor_x, self.factor_y, self.factor_z):
            factor.textChanged.connect(self._on_display_control)
        self.rotate_order.currentIndexChanged.connect(self._on_display_control)
        self.parent_shape.stateChanged.connect(self._on_toggle_zero)
        self.zero_control.stateChanged.connect(self._on_toggle_shape)
        self.mirror.buttonClicked.connect(self._on_display_control)
        self.mirror_reparent.clicked.connect(self._on_mirror_shapes)
        self.create_btn.clicked.connect(self._on_create_control)
        self.assign_btn.clicked.connect(self._on_assign_control)

    def resizeEvent(self, event):
        self.controls_viewer.update_coords()
        super(ControlsWidget, self).resizeEvent(event)

    def set_controls_file(self, naming_file):
        """
        Sets the naming file used by the controls library
        :param naming_file: str
        """

        controls_file = naming_file if naming_file and os.path.isfile(naming_file) else self._get_default_data_file()
        self.CONTROLS_LIB().controls_file = controls_file
        self._init_data()

    def _get_default_data_file(self):
        """
        Internal function that returns the default path to controls data file
        :return: str
        """

        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'controls_data.json')

    def _init_data(self):
        """
        Internal functional function that initializes controls data
        """

        controls = self.CONTROLS_LIB().load_control_data() or list()
        for control in controls:
            item = QTreeWidgetItem(self.controls_list, [control.name])
            item.control = control
            item.shapes = control.shapes
            self.controls_list.addTopLevelItem(item)

        self.controls_list.controls_path = self.CONTROLS_LIB().controls_file
        self.controls_list.setCurrentItem(self.controls_list.topLevelItem(0))
        self.controls_list.setFocus(Qt.TabFocusReason)

    def _on_splitter_moved(self, *args):
        """
        This functions is called each time the user moves a splitter in the GUI
        Updates the ControlViewer widget
        """

        self.controls_viewer.update_coords()

    def _on_filter_controls_list(self, filter_text):
        """
        This function is called each time the user enters text in the search line widget
        Shows or hides elements in the list taking in account the filter_text
        :param filter_text: str, current text
        """

        for i in range(self.controls_list.topLevelItemCount()):
            item = self.controls_list.topLevelItem(i)
            item.setHidden(filter_text not in item.text(0))

    def _on_update_controls_list(self, original_text, new_text):
        """
        This function is called each time the user renames a control of the list by double clicking on it
        :param original_text: str, original name of the control
        :param new_text: str, new name of the control
        """

        # TODO: Check if we should emit some king of signal so other apps using ControlRig functinality
        # TODO: can update properly its contents

        # TODO: Here we should update the name of the control and resave the controls data

        valid_rename = self.CONTROLS_LIB().rename_control(original_text, new_text)
        if not valid_rename:
            selected_item = self.controls_list.currentItem()
            selected_item.setText(original_text)

    def _on_display_control(self):
        """
        This function is called any time the user selects a control in the list
        Updates the ControlView to show the control in it
        """

        if not tp.is_maya():
            return

        item = self.controls_list.currentItem()
        if not item:
            return

        cc = item.text(0)
        offset = self.offset()
        factor = self.factor()
        axis = self.rotate_order.itemData(self.rotate_order.currentIndex())
        mirror = self.mirror.checkedButton().value

        if self.controls_viewer.control != cc:
            self.controls_viewer.control = cc
            self.controls_viewer.load(copy(item.shapes))

            try:
                r = maya.cmds.getAttr('{}.radius'.format(maya.cmds.ls(sl=True, type='joint')[0]) * self.jds)
            except (TypeError, IndexError):
                r = 1
            finally:
                self.controls_viewer.ref = r

        for i, shape in enumerate(self.controls_viewer.shapes):
            shape.transform(offset=offset, scale=factor, axis=axis, mirror=mirror)

        self.controls_viewer.update_coords()

    def _on_capture_control(self):
        """
        This function is called when the user presses capture control button
        Opens CaptureControl dialog
        """

        if not tp.is_maya():
            return

        sel = maya.cmds.ls(sl=True)
        if not len(sel):
            LOGGER.warning('Cannot capture an empty selection')
            return

        degree = 0
        periodic = -1
        for crv in sel:
            shapes = maya.cmds.listRelatives(crv, s=True, ni=True, f=True)
            for shape in shapes:
                degree = max(degree, maya.cmds.getAttr('{}.d'.format(shape)))
                periodic = max(periodic, maya.cmds.getAttr('{}.f'.format(shape)))

        capture_dialog = controlcapturer.CaptureControl(exec_fn=self._on_add_control, new_ctrl=sel)
        capture_dialog.exec_()

    def _on_remove_control(self):
        """
        This function is called when the user presses the delete button
        Deletes the selected control and updates control data
        :return:
        """
        result = qtutils.get_permission(message='Are you sure you want to delete control?', cancel=False,
                                        title='Deleting Control', parent=self)
        if not result:
            return
        selected_item = self.controls_list.currentItem()
        self.controls_list.takeTopLevelItem(self.controls_list.indexOfTopLevelItem(selected_item))
        self.CONTROLS_LIB().delete_control(selected_item.text(0))

    def _on_rescale_viewer(self, v=None):
        """
        In case the joint's selection have a different radius we update the viewport
        :param v: float, joint radius value
        """

        if not tp.is_maya():
            return

        v = float(self.radius.value())
        if v > 0:
            try:
                r = maya.cmds.getAttr('{}.radius'.format(maya.cmds.ls(sl=True, type='joint')[0]) * self.jds)
            except TypeError:
                r = 1
            except IndexError:
                r = self.controls_viewer.ref * v
            finally:
                self.controls_viewer.ref = r / v

        self.controls_viewer.update_coords()

    def _on_toggle_zero(self, state):
        if state and self.zero_control.isChecked():
            self.zero_control.setChecked(False)

    def _on_toggle_shape(self, state):
        if state and self.parent_shape.isChecked():
            self.parent_shape.setChecked(False)
        self.zero_iter.setEnabled(state)

    def _on_mirror_shapes(self):
        print('Mirroring shapes')

    def _on_add_control(self, *args):
        """
        Function that is called by CaptureControl dialog after valid closing
        :param args:
        :return:
        """

        if not tp.is_maya():
            return

        try:
            orig, name, absolute_position, absolute_rotation, degree, periodic = args
        except Exception:
            orig, name, absolute_position, absolute_rotation = args
            degree, periodic = None, None

        controls = self.CONTROLS_LIB().load_control_data() or list()
        if name in controls:
            LOGGER.error(
                'Control "{}" already exists in the Control Data File. Aborting control add operation ...'.format(name))
            return

        curve_info = self.CONTROLS_LIB().get_curve_info(
            crv=orig,
            absolute_position=absolute_position,
            absolute_rotation=absolute_rotation,
            degree=degree,
            periodic=periodic
        )
        if not curve_info:
            LOGGER.error(
                'Curve Info for "{}" curve was not generated properly! Aborting control add operation ...'.format(orig))
            return

        new_ctrl = self.CONTROLS_LIB().add_control(name, curve_info)
        if not new_ctrl:
            LOGGER.error('Control for curve "{}" not created! Aborting control add operation ...'.format(orig))
            return

        item = QTreeWidgetItem(self.controls_list, [name])
        item.control = new_ctrl
        item.shapes = new_ctrl.shapes

        self.controls_list.addTopLevelItem(item)
        self.controls_list.setCurrentItem(item)

        maya.cmds.select(orig)

    def _on_create_control(self):
        """
        Function that creates a new curve based on Maya selection
        """

        if not tp.is_maya():
            return

        item = self.controls_list.currentItem()
        if item:
            maya.cmds.undoInfo(openChunk=True)
            ccs = self.CONTROLS_LIB().create_control(
                shape_data=item.shapes,
                target_object=maya.cmds.ls(sl=True),
                size=self.radius.value(),
                name=self.name_line.value,
                offset=self.offset(),
                ori=self.factor(),
                axis_order=self.rotate_order.itemData(self.rotate_order.currentIndex()),
                shape_parent=self.parent_shape.isChecked(),
                mirror=self.mirror.checkedButton().value
            )
            maya.cmds.select(clear=True)
            for ctrls in ccs:
                maya.cmds.select(ctrls, add=True)
            maya.cmds.undoInfo(closeChunk=True)

    def _on_assign_control(self):
        """
        Function that is called when the user press Assign Control button in UI
        Updates shape of the selected curve
        """

        if not tp.is_maya():
            return

        sel = maya.cmds.ls(sl=True)
        if not sel:
            LOGGER.error('Please select a curve transform before assigning a new shape')
            return

        item = self.controls_list.currentItem()
        if item:
            maya.cmds.undoInfo(openChunk=True)
            ccs = self.CONTROLS_LIB().create_control(
                shape_data=item.shapes,
                target_object=maya.cmds.ls(sl=True),
                size=self.radius.value(),
                name=self.name_line.value + '_temp',
                offset=self.offset(),
                ori=self.factor(),
                axis_order=self.rotate_order.itemData(self.rotate_order.currentIndex()),
                shape_parent=self.parent_shape.isChecked(),
                mirror=self.mirror.checkedButton().value
            )
            self.CONTROLS_LIB().set_shape(sel[0], ccs)

        maya.cmds.undoInfo(closeChunk=True)


def run():
    win = ControlsManager()
    win.show()
    return win
