#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to create and manage rig curve controls
"""

from __future__ import print_function, division, absolute_import

import os
from copy import copy
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc as tp
from tpDcc.libs.qt.core import qtutils, base
from tpDcc.libs.qt.widgets import search, lineedit, spinbox, expandables, dividers, combobox, buttons, color, panel

import tpRigToolkit
from tpRigToolkit.libs.controlrig.core import controldata, controllib
from tpRigToolkit.tools.controlrig.widgets import controlviewer, controlcapturer, controlslist

if tp.is_maya():
    import tpDcc.dccs.maya as maya


class ControlsWidget(base.BaseWidget, object):

    CONTROLS_LIST_CLASS = controlslist.ControlsList

    def __init__(self, controls_path=None, parent=None):
        super(ControlsWidget, self).__init__(parent=parent)
        self._controls_lib = controllib.ControlLib()
        self.set_controls_file(controls_path)
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
        self._capture_btn = buttons.BaseToolButton().image('camera').icon_only()
        self._remove_btn = buttons.BaseToolButton().image('delete').icon_only()
        buttons_layout.addWidget(self._capture_btn)
        buttons_layout.addWidget(self._remove_btn)
        buttons_layout.setStretchFactor(self._capture_btn, 4)

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

        self._name_line = lineedit.BaseLineEdit(text='new_ctrl', parent=self)
        self._name_widget = QWidget()
        name_layout = qtutils.get_line_layout('  Name :   ', self, self._name_line)
        name_layout.setSpacing(0)
        name_layout.setContentsMargins(0, 0, 0, 0)
        self._name_widget.setLayout(name_layout)

        self.radius = spinbox.DragDoubleSpinBoxLine(start=1.0, max=100, positive=True, parent=self)
        self.radius_reset_btn = buttons.BaseToolButton(parent=self).image('reset').icon_only()
        self.offset_x = spinbox.DragDoubleSpinBoxLineAxis(axis='x', min=-25, max=25, parent=self)
        self.offset_y = spinbox.DragDoubleSpinBoxLineAxis(axis='y', min=-25, max=25, parent=self)
        self.offset_z = spinbox.DragDoubleSpinBoxLineAxis(axis='z', min=-25, max=25, parent=self)
        self.offset = lambda: [self.offset_x.value(), self.offset_y.value(), self.offset_z.value()]

        self.factor_x = spinbox.DragDoubleSpinBoxLineAxis(axis='x', start=1.0, min=-50, max=50, parent=self)
        self.factor_y = spinbox.DragDoubleSpinBoxLineAxis(axis='y', start=1.0, min=-50, max=50, parent=self)
        self.factor_z = spinbox.DragDoubleSpinBoxLineAxis(axis='z', start=1.0, min=-50, max=50, parent=self)
        self.factor = lambda: [self.factor_x.value(), self.factor_y.value(), self.factor_z.value()]

        for offset in (self.offset_x, self.offset_y, self.offset_z):
            offset.setToolTip('Set the position offset of the shape(s)')
        for factor in (self.factor_x, self.factor_y, self.factor_z):
            factor.setToolTip('Set the scale factor of the shape(s)')

        self.rotate_order = combobox.BaseComboBox(parent=self)
        self.rotate_order.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        for x in ['XYZ', 'YXZ', 'ZYX']:
            it = QStandardItem(x[0])
            self.rotate_order.addItem(x[0], it)
            self.rotate_order.setItemData(controldata.axis_eq[x[0]], x)

        self.color_picker = color.ColorSelector(parent=self)
        self.color_picker.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.color_picker.set_display_mode(color.ColorSelector.DisplayMode.NO_ALPHA)
        self.color_picker.set_color(QColor(240, 245, 255))
        self.color_picker.set_panel_parent(self.parent())

        col_layout = qtutils.get_column_layout(
            self._name_widget,
            qtutils.get_line_layout('Radius : ', self, self.radius, self.radius_reset_btn),
            qtutils.get_line_layout('Offset : ', self, self.offset_x, self.offset_y, self.offset_z),
            qtutils.get_line_layout('Factor : ', self, self.factor_x, self.factor_y, self.factor_z),
            qtutils.get_line_layout('Axis : ', self, self.rotate_order),
            qtutils.get_line_layout('Color : ', self, self.color_picker)
        )
        col_layout.setContentsMargins(5, 10, 0, 5)

        self._options_expander = expandables.ExpanderWidget(parent=self)
        self._options_expander.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self._options_expander.setRolloutStyle(expandables.ExpanderStyles.Maya)
        self._options_expander.setDragDropMode(expandables.ExpanderDragDropModes.NoDragDrop)

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
        self._options_expander.addItem(title='Parenting', widget=parenting_widget, collapsed=False)

        mirror_widget = QWidget()
        mirror_layout = QVBoxLayout()
        mirror_widget.setLayout(mirror_layout)
        self.mirror = QButtonGroup(parent=self)
        self.none = buttons.BaseButton('None', parent=self)
        self.none.setCheckable(True)
        self.none.setChecked(True)
        self.none.value = None
        self.mirror.addButton(self.none)

        self.xy = buttons.BaseButton('XY', parent=self)
        self.yz = buttons.BaseButton('YZ', parent=self)
        self.zx = buttons.BaseButton('ZX', parent=self)

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

        self.mirror_color = color.ColorSelector()
        self.mirror_color.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.mirror_color.set_display_mode(color.ColorSelector.DisplayMode.NO_ALPHA)
        self.mirror_color.set_panel_parent(self.parent())

        mirror_layout.addLayout(qtutils.get_line_layout('Mirror Color : ', self, self.mirror_color))
        self.from_name = lineedit.BaseLineEdit(text='from', parent=self)
        self.to_name = lineedit.BaseLineEdit(text='to', parent=self)
        mirror_layout.addLayout(
            qtutils.get_line_layout('Name Pattern : ', self, self.from_name, QLabel(u'\u25ba', self), self.to_name))

        self.mirror_reparent = QPushButton('Mirror Shape(s)', self)
        # for w in (self.mirror_color, self.from_name, self.to_name, self.mirror_reparent):
        #     w.setEnabled(False)
        mirror_layout.addWidget(self.mirror_reparent)

        self._options_expander.addItem(title='Mirroring', widget=mirror_widget, collapsed=False)

        props_layout.setAlignment(Qt.AlignTop)
        props_layout.addLayout(col_layout)
        props_layout.addWidget(self._options_expander)
        props_layout.addStretch()

        self.props_splitter.setStretchFactor(0, 2)

        self.main_layout.addLayout(dividers.DividerLayout())

        self._create_layout = QHBoxLayout()
        self._create_layout.setContentsMargins(2, 2, 2, 2)
        self._create_layout.setSpacing(2)
        self._create_btn = buttons.BaseButton('Create Control')
        self._assign_btn = buttons.BaseButton('Assign Control')
        self._create_layout.addWidget(self._create_btn)
        self._create_layout.addWidget(self._assign_btn)

        self.main_layout.addLayout(self._create_layout)

    def setup_signals(self):
        self.color_picker.colorChanged.connect(self._on_control_color_changed)
        self.main_splitter.splitterMoved.connect(self._on_splitter_moved)
        self.props_splitter.splitterMoved.connect(self._on_splitter_moved)
        self.controls_filter.textChanged.connect(self._on_filter_controls_list)
        self.controls_list.itemUpdated.connect(self._on_update_controls_list)
        self.controls_list.itemSelectionChanged.connect(self._on_display_control)
        self._capture_btn.clicked.connect(self._on_capture_control)
        self._remove_btn.clicked.connect(self._on_remove_control)
        self.radius.textChanged.connect(self._on_rescale_viewer)
        self.radius.textChanged.connect(self._on_display_control)
        self.radius_reset_btn.clicked.connect(partial(self.radius.setText, '1.0'))
        for offset in (self.offset_x, self.offset_y, self.offset_z):
            offset.textChanged.connect(self._on_display_control)
        for factor in (self.factor_x, self.factor_y, self.factor_z):
            factor.textChanged.connect(self._on_display_control)
        self.rotate_order.currentIndexChanged.connect(self._on_display_control)
        self.parent_shape.stateChanged.connect(self._on_toggle_zero)
        self.zero_control.stateChanged.connect(self._on_toggle_shape)
        self.mirror.buttonClicked.connect(self._on_display_control)
        self.mirror_reparent.clicked.connect(self._on_mirror_shapes)
        self._create_btn.clicked.connect(self._on_create_control)
        self._assign_btn.clicked.connect(self._on_assign_control)

    def resizeEvent(self, event):
        super(ControlsWidget, self).resizeEvent(event)
        self.controls_viewer.update_coords()

    def set_controls_file(self, controls_file=None):
        """
        Sets the naming file used by the controls library
        :param controls_file: str
        """

        controls_file = controls_file if controls_file and os.path.isfile(controls_file) else None
        if not controls_file:
            controls_file = self._get_default_data_file()

        self._controls_lib.controls_file = controls_file
        self._init_data()

    def set_control_data(self, data_dict):
        """
        Function that set current control widget status taking into account the data from a dictionary
        :param data_dict: dict
        """

        control_name = data_dict.get('control_name', None)
        size = data_dict.get('size', 1.0)
        name = data_dict.get('name', 'new_ctrl')
        offset = data_dict.get('offset', [0.0, 0.0, 0.0])
        mirror = data_dict.get('mirror', None)
        color = data_dict.get('color', [1.0, 0.0, 0.0, 1.0])
        axis_order = data_dict.get('axis_order', 'XYZ')
        ori = data_dict.get('ori', [1.0, 1.0, 1.0])
        shape_parent = data_dict.get('shape_parent', False)

        items = self.controls_list.findItems(control_name, Qt.MatchExactly, 0)
        if not items:
            return
        item = items[0]
        self.controls_list.setCurrentItem(item)
        self.radius.setValue(float(size))
        self._name_line.setText(str(name))
        self.offset_x.setValue(float(offset[0]))
        self.offset_y.setValue(float(offset[1]))
        self.offset_z.setValue(float(offset[2]))
        self.factor_x.setValue(float(ori[0]))
        self.factor_y.setValue(float(ori[1]))
        self.factor_z.setValue(float(ori[2]))
        self.rotate_order.setCurrentText(axis_order[0])
        self.parent_shape.setChecked(bool(shape_parent))
        self.color_picker.set_color(QColor.fromRgbF(*color))
        mirror = str(mirror)
        for mirror_btn in self.mirror.buttons():
            if mirror_btn.text() == mirror:
                mirror_btn.setChecked(True)
                break

    def get_selected_control_item_data(self):
        """
        Returns dictionary containing all the data of the selected item
        :return: dict
        """

        item = self.controls_list.currentItem()
        if not item:
            return dict()

        return {
            'control_name': item.control.name,
            'shape_data': item.shapes,
            'size': self.radius.value(),
            'name': self._name_line.text(),
            'offset': self.offset(),
            'ori': self.factor(),
            'axis_order': self.rotate_order.itemData(controldata.axis_eq[self.rotate_order.currentText()]),
            'shape_parent': self.parent_shape.isChecked(),
            'mirror': self.mirror.checkedButton().value,
            'color': self.color_picker.color().getRgbF()
        }

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

        self.controls_list.clear()

        controls = self._controls_lib.load_control_data() or list()
        for control in controls:
            item = QTreeWidgetItem(self.controls_list, [control.name])
            item.control = control
            item.shapes = control.shapes
            self.controls_list.addTopLevelItem(item)

        self.controls_list.controls_path = self._controls_lib.controls_file
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

        valid_rename = self._controls_lib.rename_control(original_text, new_text)
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

            r = None
            try:
                r = maya.cmds.getAttr('{}.radius'.format(maya.cmds.ls(sl=True, type='joint')[0]) * self.jds)
            except (TypeError, IndexError, AttributeError):
                r = 1
            finally:
                if r:
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
            tpRigToolkit.logger.warning('Cannot capture an empty selection')
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
        self._controls_lib.delete_control(selected_item.text(0))

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

        controls = self._controls_lib.load_control_data() or list()
        if name in controls:
            tpRigToolkit.logger.error(
                'Control "{}" already exists in the Control Data File. Aborting control add operation ...'.format(name))
            return

        curve_info = self._controls_lib.get_curve_info(
            crv=orig,
            absolute_position=absolute_position,
            absolute_rotation=absolute_rotation,
            degree=degree,
            periodic=periodic
        )
        if not curve_info:
            tpRigToolkit.logger.error(
                'Curve Info for "{}" curve was not generated properly! Aborting control add operation ...'.format(orig))
            return

        new_ctrl = self._controls_lib.add_control(name, curve_info)
        if not new_ctrl:
            tpRigToolkit.logger.error('Control for curve "{}" not created! Aborting control add operation ...'.format(orig))
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

        control_data = self.get_selected_control_item_data()
        if not control_data:
            return

        maya.cmds.undoInfo(openChunk=True)
        try:
            control_data['target_object'] = maya.cmds.ls(sl=True)
            axis_order = control_data.get('axis_order', 'XYZ')
            control_data['axis_order'] = self.rotate_order.itemData(controldata.axis_eq[axis_order[0]])
            control_data.pop('control_name', None)
            ccs = self._controls_lib.create_control(**control_data)
            maya.cmds.select(clear=True)
            for ctrls in ccs:
                maya.cmds.select(ctrls, add=True)
        finally:
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
            tpRigToolkit.logger.error('Please select a curve transform before assigning a new shape')
            return

        item = self.controls_list.currentItem()
        if item:
            maya.cmds.undoInfo(openChunk=True)
            ccs = self._controls_lib.create_control(
                shape_data=item.shapes,
                target_object=maya.cmds.ls(sl=True),
                size=self.radius.value(),
                name=self._name_line.text() + '_temp',
                offset=self.offset(),
                ori=self.factor(),
                axis_order=self.rotate_order.itemData(self.rotate_order.currentIndex()),
                shape_parent=self.parent_shape.isChecked(),
                mirror=self.mirror.checkedButton().value,
                color=self.color_picker.color().getRgbF()
            )
            self._controls_lib.set_shape(sel[0], ccs)

        maya.cmds.undoInfo(closeChunk=True)

    def _on_show_color_panel(self):
        w = QWidget()
        lyt = QVBoxLayout()
        w.setLayout(lyt)
        color_slider = color.Color2DSlider()
        color_line = color.ColorLineEdit()
        lyt.addWidget(color_slider)
        lyt.addWidget(color_line)

        new_panel = panel.SliderPanel('Select Color', parent=self)
        new_panel.set_widget(w)
        new_panel.show()

    def _on_control_color_changed(self, color):
        self.controls_viewer.control_color = color
        self.controls_viewer.update_coords()


class ControlSelector(ControlsWidget, object):

    def __init__(self, controls_path=None, parent=None):

        self._control_data = dict()

        super(ControlSelector, self).__init__(controls_path=controls_path, parent=parent)

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
        parent = self.parent()
        if parent:
            parent.close()
        else:
            self.close()
