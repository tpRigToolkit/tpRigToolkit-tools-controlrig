#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Control Rig widget view class implementation
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import logging
from copy import copy
from functools import partial

from Qt.QtCore import Qt
from Qt.QtWidgets import QSizePolicy, QWidget, QSplitter, QButtonGroup, QPushButton, QTreeWidgetItem
from Qt.QtGui import QStandardItem

from tpDcc import dcc
from tpDcc.dcc import dialog
from tpDcc.libs.qt.core import base, qtutils, contexts as qt_contexts
from tpDcc.libs.qt.widgets import layouts, search, lineedit, spinbox, expandables, dividers, combobox, buttons, color
from tpDcc.libs.qt.widgets import label, tabs, checkbox

from tpRigToolkit.tools.controlrig.core import controldata
from tpRigToolkit.tools.controlrig.widgets import controlviewer, controlslist, controlcapturer, controlutils

LOGGER = logging.getLogger('tpRigToolkit-tools-controlrig')


class ControlRigView(base.BaseWidget, object):

    CONTROLS_LIST_CLASS = controlslist.ControlsList

    def __init__(self, model, controller, parent=None):

        self._model = model
        self._controller = controller

        super(ControlRigView, self).__init__(parent=parent)

        self.refresh()

        self._setup_tooltips()

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def ui(self):
        super(ControlRigView, self).ui()

        self._main_splitter = QSplitter(Qt.Horizontal)
        self._main_splitter.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        controls_widget = QWidget(parent=self)
        controls_layout = layouts.VerticalLayout()
        controls_widget.setLayout(controls_layout)
        self._main_splitter.addWidget(controls_widget)

        properties_widget = QWidget(parent=self)
        properties_layout = layouts.VerticalLayout()
        properties_widget.setLayout(properties_layout)
        self._main_splitter.addWidget(properties_widget)

        self._controls_filter = search.SearchFindWidget(parent=self)
        controls_layout.addWidget(self._controls_filter)

        self._controls_list = self.CONTROLS_LIST_CLASS(parent=self)
        self._controls_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        buttons_layout = layouts.HorizontalLayout(spacing=2, margins=(0, 0, 0, 0))
        self._capture_btn = buttons.BaseToolButton(parent=self).image('camera').small()
        self._remove_btn = buttons.BaseToolButton(parent=self).image('delete').small()

        buttons_layout.addWidget(self._capture_btn)
        buttons_layout.addWidget(self._remove_btn)

        controls_layout.addWidget(self._controls_list)
        controls_layout.addLayout(buttons_layout)

        self._props_splitter = QSplitter(Qt.Vertical)
        self._props_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        tool_bar = tabs.MenuLineTabWidget(alignment=Qt.AlignLeft)
        properties_layout.addWidget(tool_bar)

        creator_widget = QWidget(parent=self)
        creator_layout = layouts.VerticalLayout(spacing=2, margins=(0, 0, 0, 0))
        creator_widget.setLayout(creator_layout)

        self._controls_viewer = controlviewer.ControlViewer(parent=self)
        creator_layout.addWidget(self._controls_viewer)

        creator_layout.addWidget(self._props_splitter)

        props_widget = QWidget(parent=self)
        props_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        props_widget.setLayout(props_layout)

        self._props_splitter.addWidget(self._controls_viewer)
        self._props_splitter.addWidget(props_widget)

        self._name_line = lineedit.BaseLineEdit(parent=self)
        self._name_widget = QWidget(parent=self)
        name_layout = qtutils.get_line_layout('  Name :   ', self, self._name_line)
        name_layout.setSpacing(2)
        name_layout.setContentsMargins(0, 0, 0, 0)
        self._name_widget.setLayout(name_layout)

        self._size_spn = spinbox.DragDoubleSpinBoxLine(max=100, positive=True, parent=self)
        self._size_reset_btn = buttons.BaseToolButton(parent=self).image('reset').icon_only()
        self._offset_x_spn = spinbox.DragDoubleSpinBoxLineAxis(axis='x', min=-25, max=25, parent=self)
        self._offset_y_spn = spinbox.DragDoubleSpinBoxLineAxis(axis='y', min=-25, max=25, parent=self)
        self._offset_z_spn = spinbox.DragDoubleSpinBoxLineAxis(axis='z', min=-25, max=25, parent=self)

        self._factor_x_spn = spinbox.DragDoubleSpinBoxLineAxis(axis='x', start=1.0, min=-50, max=50, parent=self)
        self._factor_y_spn = spinbox.DragDoubleSpinBoxLineAxis(axis='y', start=1.0, min=-50, max=50, parent=self)
        self._factor_z_spn = spinbox.DragDoubleSpinBoxLineAxis(axis='z', start=1.0, min=-50, max=50, parent=self)

        self._axis_combo = combobox.BaseComboBox(parent=self)

        self._color_picker = color.ColorSelector(parent=self)
        self._color_picker.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._color_picker.set_display_mode(color.ColorSelector.DisplayMode.NO_ALPHA)
        self._color_picker.set_reset_on_close(False)
        self._color_picker.set_panel_parent(self.parent())

        col_layout = qtutils.get_column_layout(
            self._name_widget,
            qtutils.get_line_layout('Radius : ', self, self._size_spn, self._size_reset_btn),
            qtutils.get_line_layout('Offset : ', self, self._offset_x_spn, self._offset_y_spn, self._offset_z_spn),
            qtutils.get_line_layout('Factor : ', self, self._factor_x_spn, self._factor_y_spn, self._factor_z_spn),
            qtutils.get_line_layout('Axis : ', self, self._axis_combo),
            qtutils.get_line_layout('Color : ', self, self._color_picker)
        )
        col_layout.setContentsMargins(5, 10, 0, 5)

        self._options_expander = expandables.ExpanderWidget(parent=self)
        self._options_expander.setDragDropMode(expandables.ExpanderDragDropModes.NoDragDrop)

        mirror_widget = QWidget(parent=self)
        mirror_layout = layouts.VerticalLayout()
        mirror_widget.setLayout(mirror_layout)
        self._mirror_button_group = QButtonGroup(parent=self)
        self._none_btn = buttons.BaseButton('None', parent=self)
        self._none_btn.setCheckable(True)
        self._none_btn.setChecked(True)
        self._none_btn.value = None
        self._mirror_button_group.addButton(self._none_btn)

        self._xy_btn = buttons.BaseButton('XY', parent=self)
        self._yz_btn = buttons.BaseButton('YZ', parent=self)
        self._zx_btn = buttons.BaseButton('ZX', parent=self)

        def mirror_click(button, event):
            if button.isChecked():
                self._none_btn.setChecked(True)
                self._mirror_button_group.buttonClicked.emit(self._none_btn)
            else:
                QPushButton.mousePressEvent(button, event)

        self._none_btn.mousePressEvent = partial(mirror_click, self._none_btn)
        for btn in (self._xy_btn, self._yz_btn, self._zx_btn):
            self._mirror_button_group.addButton(btn)
            btn.setStyleSheet(self._none_btn.styleSheet())
            btn.setToolTip('Set mirror mode on {}plane'.format(btn.text()))
            btn.setCheckable(True)
            btn.value = btn.text()
            btn.mousePressEvent = partial(mirror_click, btn)

        mirror_layout.addLayout(
            qtutils.get_line_layout('Mirror Plane : ', self, self._none_btn, self._xy_btn, self._yz_btn, self._zx_btn))

        parenting_widget = QWidget(parent=self)
        parenting_layout = layouts.VerticalLayout()
        parenting_widget.setLayout(parenting_layout)
        self._create_buffers_cbx = checkbox.BaseCheckBox('Create Buffer Transform(s)', parent=self)
        self._parent_shape_cbx = checkbox.BaseCheckBox('Parent Shape to Transform', parent=self)
        depth_layout = layouts.HorizontalLayout()
        depth_layout.addWidget(self._create_buffers_cbx)
        self._buffers_depth_spn = spinbox.BaseSpinBox(parent=self)
        self._buffers_depth_spn.setMinimum(1)
        self._buffers_depth_spn.setMaximum(5)
        zero_depth_lbl = label.BaseLabel('depth', parent=self)
        depth_layout.addWidget(self._buffers_depth_spn)
        depth_layout.addWidget(zero_depth_lbl)
        parenting_layout.addLayout(depth_layout)
        parenting_layout.addWidget(self._parent_shape_cbx)

        self._options_expander.addItem(title='Parenting', widget=parenting_widget, collapsed=False)
        self._options_expander.addItem(title='Mirror', widget=mirror_widget, collapsed=False)

        props_layout.addLayout(col_layout)
        props_layout.addWidget(self._options_expander)
        props_layout.addStretch()

        self._props_splitter.setSizes([100, 450])

        self._create_layout = layouts.HorizontalLayout(spacing=2, margins=(2, 2, 2, 2))
        self._create_btn = buttons.BaseButton('Create Control', parent=self)
        self._create_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        assign_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        self._assign_btn = buttons.BaseButton('Assign Control', parent=self)
        self._assign_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._assign_btn.setStyleSheet(
            'border-top-right-radius: 0px; border-bottom-right-radius: 0px; border-right: 0px;')
        self._keep_assign_color_btn = buttons.BaseButton('Keep Color', parent=self)
        self._keep_assign_color_btn.setStyleSheet('border-top-left-radius: 0px; border-bottom-left-radius: 0px;')
        self._keep_assign_color_btn.setCheckable(True)
        assign_layout.addWidget(self._assign_btn)
        assign_layout.addWidget(self._keep_assign_color_btn)

        self._create_layout.addWidget(self._create_btn)
        self._create_layout.addLayout(assign_layout)

        utils_widget = controlutils.ControlRigUtilsView(client=self._controller.client)

        tool_bar.add_tab(creator_widget, {'text': 'Creator', 'image': 'circle'})
        tool_bar.add_tab(utils_widget, {'text': 'Utils', 'image': 'tool'})

        self.main_layout.addWidget(self._main_splitter)
        self.main_layout.addLayout(dividers.DividerLayout())
        self.main_layout.addLayout(self._create_layout)

    def setup_signals(self):
        self._main_splitter.splitterMoved.connect(self._on_splitter_moved)
        self._props_splitter.splitterMoved.connect(self._on_splitter_moved)
        self._controls_filter.textChanged.connect(self._on_filter_controls_list)
        self._controls_list.currentItemChanged.connect(self._on_control_selected)
        self._controls_list.itemUpdated.connect(self._on_rename_control)
        self._name_line.textChanged.connect(self._controller.set_control_name)
        self._size_spn.valueChanged.connect(self._on_control_size_changed)
        self._size_reset_btn.clicked.connect(self._controller.reset_to_default_control_size)
        self._offset_x_spn.valueChanged.connect(self._on_offset_x_changed)
        self._offset_y_spn.valueChanged.connect(self._on_offset_y_changed)
        self._offset_z_spn.valueChanged.connect(self._on_offset_z_changed)
        self._factor_x_spn.valueChanged.connect(self._on_factor_x_changed)
        self._factor_y_spn.valueChanged.connect(self._on_factor_y_changed)
        self._factor_z_spn.valueChanged.connect(self._on_factor_z_changed)
        self._axis_combo.currentIndexChanged.connect(self._on_axis_changed)
        self._color_picker.closedColor.connect(self._controller.set_color)
        self._color_picker.colorChanged.connect(self._on_color_changed)
        self._mirror_button_group.buttonClicked.connect(self._on_mirror_button_clicked)
        self._create_buffers_cbx.toggled.connect(self._on_toggle_create_buffers)
        self._parent_shape_cbx.toggled.connect(self._on_toggle_parent_shape)
        self._buffers_depth_spn.valueChanged.connect(self._controller.set_buffer_transforms_depth)
        self._capture_btn.clicked.connect(self._on_capture_control)
        self._remove_btn.clicked.connect(self._on_remove_control)
        self._create_btn.clicked.connect(self._controller.create_control)
        self._assign_btn.clicked.connect(self._on_assign_control)
        self._keep_assign_color_btn.toggled.connect(self._controller.set_keep_assign_color)

        # TODO: Block signals before calling the setter functions
        self._model.controlsChanged.connect(self._update_controls_list)
        self._model.currentControlChanged.connect(self._update_controls_viewer)
        # self._model.controlNameChanged.connect(self._name_line.setText)
        # self._model.controlSizeChanged.connect(self._size_spn.setValue)
        # self._model.offsetXChanged.connect(self._offset_x_spn.setValue)
        # self._model.offsetYChanged.connect(self._offset_y_spn.setValue)
        # self._model.offsetZChanged.connect(self._offset_z_spn.setValue)
        # self._model.defaultOffsetXChanged.connect(self._offset_x_spn.set_default)
        # self._model.defaultOffsetYChanged.connect(self._offset_y_spn.set_default)
        # self._model.defaultOffsetZChanged.connect(self._offset_z_spn.set_default)
        # self._model.factorXChanged.connect(self._factor_x_spn.setValue)
        # self._model.factorYChanged.connect(self._factor_y_spn.setValue)
        # self._model.factorZChanged.connect(self._factor_z_spn.setValue)
        # self._model.defaultFactorXChanged.connect(self._factor_x_spn.set_default)
        # self._model.defaultFactorYChanged.connect(self._factor_y_spn.set_default)
        # self._model.defaultFactorZChanged.connect(self._factor_z_spn.set_default)
        # self._model.axisChanged.connect(self._axis_combo.setCurrentIndex)
        # self._model.controlColorChanged.connect(self._on_set_color_picker)
        # self._model.mirrorPlaneChanged.connect(self._on_mirror_plane_changed)
        # self._model.createBufferTransformsChanged.connect(self._create_buffers_cbx.setChecked)
        # self._model.parentShapeToTransformChanged.connect(self._parent_shape_cbx.setChecked)
        # self._model.bufferTransformsDepthChanged.connect(self._buffers_depth_spn.setValue)
        # self._model.keepAssignColorChanged.connect(self._keep_assign_color_btn.setChecked)

    def showEvent(self, event):
        if not self._model.current_control:
            self._controls_list.setCurrentItem(self._controls_list.topLevelItem(0))
        else:
            control_item = self._controls_list.findItems(
                self._model.current_control, Qt.MatchExactly | Qt.MatchRecursive, 0)
            if control_item:
                self._controls_list.setCurrentItem(control_item[0])
            else:
                self._controls_list.setCurrentItem(self._controls_list.topLevelItem(0))

        super(ControlRigView, self).showEvent(event)

    def resizeEvent(self, event):
        super(ControlRigView, self).resizeEvent(event)
        self._controls_viewer.update_coords()

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def refresh(self):
        controls = self._controller.update_controls()
        if controls:
            self._controller.set_current_control(controls[0].name)

        self._update_rotate_orders()

        with qt_contexts.block_signals(self._model):
            self._name_line.setText(self._model.control_name)
            self._offset_x_spn.setValue(self._model.offset_x)
            self._offset_y_spn.setValue(self._model.offset_y)
            self._offset_z_spn.setValue(self._model.offset_z)
            self._factor_x_spn.setValue(self._model.factor_x)
            self._factor_y_spn.setValue(self._model.factor_y)
            self._factor_z_spn.setValue(self._model.factor_z)
            self._axis_combo.setCurrentIndex(self._model.control_axis)
            self._color_picker.set_color(self._model.control_color)
            self._size_spn.setValue(self._model.control_size)
            self._on_mirror_plane_changed(self._model.mirror_plane)
            self._create_buffers_cbx.setChecked(self._model.create_buffer_transforms)
            self._parent_shape_cbx.setChecked(self._model.parent_shape_to_transform)
            self._buffers_depth_spn.setValue(self._model.buffer_transforms_depth)
            self._keep_assign_color_btn.setChecked(self._model.keep_assign_color)

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _setup_tooltips(self):
        """
        Internal function that setup tooltips
        :return:
        """

        for offset in (self._offset_x_spn, self._offset_y_spn, self._offset_z_spn):
            offset.setToolTip('Set the position offset of the shape(s)')
        for factor in (self._factor_x_spn, self._factor_y_spn, self._factor_z_spn):
            factor.setToolTip('Set the scale factor of the shape(s)')

    def _update_controls_list(self, controls):
        """
        Internal function that updates control list data
        """

        self._controls_list.clear()

        for control in controls:
            item = QTreeWidgetItem(self._controls_list, [control.name])
            item.control = control
            item.shapes = control.shapes
            self._controls_list.addTopLevelItem(item)

        self._controls_list.controls_path = self._model.controls_path
        self._controls_list.setFocus(Qt.TabFocusReason)

    def _update_rotate_orders(self):
        """
        Internal callback function that updates available rotate orders
        """

        self._axis_combo.clear()

        for x in controldata.rot_orders:
            self._axis_combo.setItemData(controldata.axis_eq[x[0]], x)
            self._axis_combo.addItem(x[0])

        self._controller.set_current_axis(self._model.control_axis)

    def _update_controls_viewer(self, control_name=None):
        """
        Internal function that updates the controls viewer with the data of the current control
        :param control_name: str
        """

        control_name = control_name or self._model.current_control
        control_item = self._controls_list.findItems(control_name, Qt.MatchExactly | Qt.MatchRecursive, 0)
        control_item = control_item[0] if control_item else None
        if not control_item:
            self._controls_viewer.control = None
            self._controls_viewer.update_coords()
            return

        offset = self._model.offset
        factor = self._model.factor
        axis = self._axis_combo.itemData(self._model.control_axis) or 'XYZ'
        mirror_plane = self._model.mirror_plane

        if self._controls_viewer.control != control_name:
            self._controls_viewer.control = control_name
            self._controls_viewer.load(copy(control_item.shapes))
            joint_radius = None
            try:
                joint_radius = self._controller.get_joint_radius()
            except (NameError, TypeError, IndexError, AttributeError):
                joint_radius = 1
            finally:
                if joint_radius:
                    self._controls_viewer.ref = joint_radius

        for i, shape in enumerate(self._controls_viewer.shapes):
            shape.transform(offset=offset, scale=factor, axis=axis, mirror=mirror_plane)

        self._controls_viewer.update_coords()

    def _rescale_viewer(self):
        """
        Internal function that updates viewer in case the joint's selection have
        a different radius we update the viewport
        """

        v = float(self._model.control_size)
        if v > 0:
            try:
                joint_radius = self._controller.get_joint_radius()
            except TypeError:
                joint_radius = 1
            except IndexError:
                joint_radius = self.controls_viewer.ref * v
            finally:
                self._controls_viewer.ref = joint_radius / v

        self._controls_viewer.update_coords()

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

    def _on_splitter_moved(self, *args):
        """
        Internal function that is called each time the user moves a splitter in the GUI
        Updates the ControlViewer widget
        """

        self._controls_viewer.update_coords()

    def _on_filter_controls_list(self, filter_text):
        """
        This function is called each time the user enters text in the search line widget
        Shows or hides elements in the list taking in account the filter_text
        :param filter_text: str, current text
        """

        for i in range(self._controls_list.topLevelItemCount()):
            item = self._controls_list.topLevelItem(i)
            item.setHidden(filter_text not in item.text(0))

    def _on_control_selected(self, control_item):
        """
        Internal function that is called when the user selects a control item from the controls list
        :param control_item: QTreeWidgetItem
        """

        if not control_item:
            return

        control_name = control_item.text(0)
        self._controller.set_current_control(control_name)

    def _on_rename_control(self, original_name, new_name):
        """
        Internal callback function that is called when the user renames a control using the controls list
        :param original_name: str
        :param new_name: str
        """

        # TODO: Check if we should emit some king of signal so other apps using ControlRig functionality
        # TODO: can update properly its contents

        valid_rename = self._controller.rename_control(original_name, new_name)
        if not valid_rename:
            selected_item = self._controls_list.currentItem()
            selected_item.setText(0, original_name)

    def _on_control_size_changed(self, control_size):
        """
        Internal callback function that is called each time the user updates the control size
        :param control_size: float
        """

        self._controller.set_control_size(control_size)
        self._rescale_viewer()
        self._update_controls_viewer()

    def _on_offset_x_changed(self, offset_x):
        """
        Internal callback function that is called when offset X values is changed by the user
        :param offset_x: float
        """

        self._controller.set_offset_x(offset_x)
        self._update_controls_viewer()

    def _on_offset_y_changed(self, offset_y):
        """
        Internal callback function that is called when offset Y values is changed by the user
        :param offset_y: float
        """

        self._controller.set_offset_y(offset_y)
        self._update_controls_viewer()

    def _on_offset_z_changed(self, offset_z):
        """
        Internal callback function that is called when offset Z values is changed by the user
        :param offset_z: float
        """

        self._controller.set_offset_z(offset_z)
        self._update_controls_viewer()
        
    def _on_factor_x_changed(self, factor_x):
        """
        Internal callback function that is called when factor X values is changed by the user
        :param factor_x: float
        """

        self._controller.set_factor_x(factor_x)
        self._update_controls_viewer()

    def _on_factor_y_changed(self, factor_y):
        """
        Internal callback function that is called when factor Y values is changed by the user
        :param factor_y: float
        """

        self._controller.set_factor_y(factor_y)
        self._update_controls_viewer()

    def _on_factor_z_changed(self, factor_z):
        """
        Internal callback function that is called when factor Z values is changed by the user
        :param factor_z: float
        """

        self._controller.set_factor_z(factor_z)
        self._update_controls_viewer()

    def _on_axis_changed(self, axis_index):
        """
        Internal callback function that is called when axis is changed by the user
        :param axis_index: int
        """

        self._controller.set_current_axis(axis_index)
        self._update_controls_viewer()

    def _on_color_changed(self, color):
        """
        Internal callback function that is called in real time while the user changes the color in the picker
        Useful to update elements of the UI when necessary
        :param color: QColor
        """

        self._controls_viewer.control_color = color
        self._controls_viewer.update_coords()

    def _on_set_color_picker(self, color_list):
        new_color = [channel_color * 255 for channel_color in color_list]
        self._color_picker.set_color(new_color)

    def _on_mirror_button_clicked(self, mirror_button_clicked):
        """
        Internal function that is called when the user clicks on a mirror button
        :param mirror_button_clicked: BaseButton
        """

        mirror_plane = mirror_button_clicked.value
        self._controller.set_mirror_plane(mirror_plane)

        self._update_controls_viewer()

    def _on_mirror_plane_changed(self, mirror_plane):
        """
        Internal function that is called when mirror plane button is changed
        :param mirror_plane: str
        """

        for mirror_axis_button in self._mirror_button_group.buttons():
            if mirror_axis_button.value == mirror_plane:
                mirror_axis_button.setChecked(True)
                break

    def _on_toggle_create_buffers(self, flag):
        self._controller.set_create_buffer_transforms(flag)
        # if flag and self._create_buffers_cbx.isChecked():
        #     self._create_buffers_cbx.setChecked(False)

    def _on_toggle_parent_shape(self, flag):
        self._controller.set_parent_shape_to_transform(flag)
        # if flag and self._parent_shape_cbx.isChecked():
        #     self._parent_shape_cbx.setChecked(False)
        # self._buffers_depth_spn.setEnabled(flag)

    def _on_capture_control(self):
        """
        This function is called when the user presses capture control button
        Opens CaptureControl dialog
        """

        sel = dcc.selected_nodes()
        if not sel:
            LOGGER.warning('Cannot capture an empty selection!')
            return False

        degree = 0
        periodic = -1
        for crv in sel:
            shapes = dcc.list_shapes(crv, intermediate_shapes=False, full_path=True)
            for shape in shapes:
                degree = max(degree, dcc.get_attribute_value(shape, 'd'))
                periodic = max(periodic, dcc.get_attribute_value(shape, 'f'))

        # TODO: For now we only support the storage of only one shape
        if len(sel) > 1:
            LOGGER.warning('Only first selected control will be saved: "{}"'.format(sel[0]))
        sel = sel[0]

        capture_widget = controlcapturer.CaptureControl(exec_fn=self._on_add_control, new_ctrl=sel, parent=self)
        with dialog.exec_dialog(
                capture_widget, name='CaptureControlDialog', width=150, height=255, fixed_size=True, frame_less=True,
                show_on_initialize=False,  parent=self, force_close_signal=capture_widget.closed):
            return capture_widget

    def _on_add_control(self, *args):
        """
        Function that is called by CaptureControl dialog after valid closing
        :param args:
        :return:
        """

        try:
            orig, name, absolute_position, absolute_rotation, degree, periodic = args
        except Exception:
            orig, name, absolute_position, absolute_rotation = args
            degree, periodic = None, None

        new_control_data = self._controller.add_control(
            orig, name, absolute_position, absolute_rotation, degree, periodic)
        if not new_control_data:
            return False

        control_name = new_control_data.get('name', None)
        control = new_control_data.get('control', None)
        if not control_name or not control:
            return False

        control_item = QTreeWidgetItem(self._controls_list, [control_name])
        control_item.control = control
        control_item.shapes = control.shapes

        self._controls_list.addTopLevelItem(control_item)
        self._controls_list.setCurrentItem(control_item)

        return True

    def _on_remove_control(self, control_name=None):
        """
        This function is called when the user presses the delete button
        Deletes the selected control and updates control data
        """

        control_name = control_name or self._model.current_control
        if not control_name:
            return False

        result = qtutils.get_permission(
            message='Are you sure you want to delete "{}" control?'.format(control_name),
            cancel=False, title='Deleting Control', parent=self)
        if not result:
            return False

        control_item = self._controls_list.findItems(control_name, Qt.MatchExactly | Qt.MatchRecursive, 0)
        control_item = control_item[0] if control_item else None
        if not control_item:
            return False

        self._controls_list.takeTopLevelItem(self._controls_list.indexOfTopLevelItem(control_item))

        self._controller.remove_control(control_item.text(0))

        return True

    def _on_assign_control(self, control_name=None):
        """
        Function that is called when the user press Assign Control button in UI
        Updates shape of the selected curve
        """

        sel = dcc.selected_nodes()
        if not sel:
            LOGGER.error('Please select a curve transform before assigning a new shape')
            return False

        control_name = control_name or self._model.current_control
        control_item = self._controls_list.findItems(control_name, Qt.MatchExactly | Qt.MatchRecursive, 0)
        control_item = control_item[0] if control_item else None
        if not control_item:
            return False

        self._controller.assign_control(control_name, sel)

        return True


class ControlSelector(ControlRigView, object):

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
                       self._assign_btn, self._name_widget, self._keep_assign_color_btn]:
            widget.setVisible(False)
            widget.setEnabled(False)

        self._select_btn = buttons.BaseButton('Select Control')
        self._create_layout.addWidget(self._select_btn)

    def setup_signals(self):
        super(ControlSelector, self).setup_signals()
        self._select_btn.clicked.connect(self._on_select_control)

    def _on_select_control(self):
        self._control_data = self._controller.get_current_control_data()
        parent = self._parent or self.parent()
        if parent:
            if hasattr(parent, 'attacher'):
                try:
                    parent.attacher.fade_close()
                except Exception:
                    parent.attacher.close()
            else:
                parent.close()
        else:
            self.close()
