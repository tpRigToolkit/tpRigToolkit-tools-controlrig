#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to create and manage rig curve controls
"""

from __future__ import print_function, division, absolute_import

import os
import traceback
from copy import copy
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpDcc.libs.qt.core import qtutils, base
from tpDcc.libs.qt.widgets import layouts, search, lineedit, spinbox, expandables, dividers, combobox, buttons, color
from tpDcc.libs.qt.widgets import panel, tabs, sliders, checkbox

import tpRigToolkit
from tpRigToolkit.libs.controlrig.core import controldata, controllib
from tpRigToolkit.tools.controlrig.widgets import controlviewer, controlcapturer, controlslist


class ControlsWidget(base.BaseWidget, object):

    CONTROLS_LIST_CLASS = controlslist.ControlsList

    def __init__(self, controls_path=None, client=None, parent=None):
        super(ControlsWidget, self).__init__(parent=parent)
        self._client = client
        self._controls_lib = controllib.ControlLib()
        self.set_controls_file(controls_path)
        self._init_data()
        self._update_control_colors()
        self._update_fonts()

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def ui(self):
        super(ControlsWidget, self).ui()

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.main_layout.addWidget(self.main_splitter)

        controls_widget = QWidget(parent=self)
        controls_layout = QVBoxLayout()
        controls_widget.setLayout(controls_layout)
        self.main_splitter.addWidget(controls_widget)

        properties_widget = QWidget(parent=self)
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

        tool_bar = tabs.MenuLineTabWidget(alignment=Qt.AlignLeft)
        properties_layout.addWidget(tool_bar)

        creator_widget = QWidget()
        creator_layout = layouts.VerticalLayout(spacing=2, margins=(0, 0, 0, 0))
        creator_widget.setLayout(creator_layout)
        tool_bar.add_tab(creator_widget, {'text': 'Creator'})

        self.controls_viewer = controlviewer.ControlViewer(parent=self)
        creator_layout.addWidget(self.controls_viewer)

        creator_layout.addWidget(self.props_splitter)

        props_widget = QWidget(parent=self)
        props_layout = QVBoxLayout()
        props_layout.setContentsMargins(0, 0, 0, 0)
        props_layout.setSpacing(0)
        props_widget.setLayout(props_layout)

        self.props_splitter.addWidget(self.controls_viewer)
        self.props_splitter.addWidget(props_widget)

        self._name_line = lineedit.BaseLineEdit(text='new_ctrl', parent=self)
        self._name_widget = QWidget(parent=self)
        name_layout = qtutils.get_line_layout('  Name :   ', self, self._name_line)
        name_layout.setSpacing(2)
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
        self._options_expander.set_rollout_style(expandables.ExpanderStyles.Maya)
        self._options_expander.setDragDropMode(expandables.ExpanderDragDropModes.NoDragDrop)

        parenting_widget = QWidget(parent=self)
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

        props_layout.addLayout(col_layout)
        props_layout.addWidget(self._options_expander)

        self.main_layout.addLayout(dividers.DividerLayout())

        self.props_splitter.setSizes([100, 450])

        utils_widget = QWidget()
        utils_layout = layouts.VerticalLayout(spacing=2, margins=(0, 0, 0, 0))
        utils_widget.setLayout(utils_layout)
        tool_bar.add_tab(utils_widget, {'text': 'Utilities'})

        self._utils_expander = expandables.ExpanderWidget(parent=self)
        self._utils_expander.setDragDropMode(expandables.ExpanderDragDropModes.NoDragDrop)
        utils_layout.addWidget(self._utils_expander)

        display_widget = QWidget(parent=self)
        display_layout = QHBoxLayout()
        display_widget.setLayout(display_layout)
        self._normal_display_button = buttons.BaseButton('Normal')
        self._template_display_button = buttons.BaseButton('Template')
        self._reference_display_button = buttons.BaseButton('Reference')
        display_layout.addWidget(self._normal_display_button)
        display_layout.addWidget(self._template_display_button)
        display_layout.addWidget(self._reference_display_button)

        color_widget = QWidget(parent=self)
        color_layout = QVBoxLayout()
        color_layout.setAlignment(Qt.AlignTop)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.setSpacing(0)
        color_widget.setLayout(color_layout)
        self._color_combo = combobox.BaseComboBox()
        self._color_combo.addItems(['Index', 'RGB'])
        color_layout.addWidget(self._color_combo)
        color_layout.addWidget(dividers.Divider())

        self._color_index_widget = QWidget()
        color_index_layout = layouts.VerticalLayout(spacing=2, margins=(0, 0, 0, 0))
        self._color_index_widget.setLayout(color_index_layout)
        self._color_index_buttons_layout = layouts.GridLayout(spacing=0, margins=(0, 0, 0, 0))

        self._color_index_slider = sliders.HoudiniDoubleSlider(self, slider_type='int')

        color_index_layout.addLayout(self._color_index_buttons_layout)
        color_index_layout.addWidget(dividers.Divider())
        color_index_layout.addWidget(self._color_index_slider)

        self._color_rgb_widget = QWidget()
        color_rgb_layout = layouts.VerticalLayout(spacing=2, margins=(0, 0, 0, 0))
        self._color_rgb_widget.setLayout(color_rgb_layout)
        self._color_dialog_widget = color.ColorDialogWidget()
        rgb_buttons_layout = layouts.HorizontalLayout(spacing=2, margins=(0, 0, 0, 0))
        self._color_rgb_live_mode_checkbox = checkbox.BaseCheckBox('Live Update')
        self._color_rgb_live_mode_checkbox.setChecked(True)
        self._color_rgb_apply_button = buttons.BaseButton('Apply')
        self._color_rgb_apply_button.setVisible(False)
        rgb_buttons_layout.addWidget(self._color_rgb_live_mode_checkbox)
        rgb_buttons_layout.addStretch()
        rgb_buttons_layout.addWidget(self._color_rgb_apply_button)
        color_rgb_layout.addWidget(self._color_dialog_widget)
        color_rgb_layout.addWidget(dividers.Divider())
        color_rgb_layout.addLayout(rgb_buttons_layout)

        self._color_rgb_widget.setVisible(False)

        color_layout.addWidget(self._color_index_widget)
        color_layout.addWidget(self._color_rgb_widget)

        mirror_widget = QWidget(parent=self)
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
            for w in (self.mirror_color, self.from_name, self.to_name, self.mirror_reparent):
                w.setEnabled(enabled)
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
        for w in (self.mirror_color, self.from_name, self.to_name, self.mirror_reparent):
            w.setEnabled(False)
        mirror_layout.addWidget(self.mirror_reparent)

        text_widget = QWidget(parent=self)
        text_layout = QVBoxLayout()
        text_widget.setLayout(text_layout)
        self._text_line = lineedit.BaseLineEdit()
        self._text_line.setPlaceholderText('Type control text ...')
        self._fonts_combo = combobox.BaseComboBox()
        self._create_text_control_button = buttons.BaseButton('Create Text')
        self._create_text_control_button.setEnabled(False)
        text_layout.addWidget(self._text_line)
        text_layout.addWidget(self._fonts_combo)
        text_layout.addWidget(dividers.Divider())
        text_layout.addWidget(self._create_text_control_button)

        self._utils_expander.addItem(title='Mirror Controls', widget=mirror_widget, collapsed=False)
        self._utils_expander.addItem(title='Display', widget=display_widget, collapsed=False)
        self._utils_expander.addItem(title='Color', widget=color_widget, collapsed=False)
        self._utils_expander.addItem(title='Text', widget=text_widget, collapsed=False)

        self._create_layout = QHBoxLayout()
        self._create_layout.setContentsMargins(2, 2, 2, 2)
        self._create_layout.setSpacing(2)
        self._create_btn = buttons.BaseButton('Create Control', parent=self)
        self._assign_btn = buttons.BaseButton('Assign Control', parent=self)
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
        self._text_line.textChanged.connect(self._on_control_text_changed)
        self._create_text_control_button.clicked.connect(self._on_create_control_text)
        self._create_btn.clicked.connect(self._on_create_control)
        self._assign_btn.clicked.connect(self._on_assign_control)
        self._normal_display_button.clicked.connect(partial(self._set_display_state, 0))
        self._template_display_button.clicked.connect(partial(self._set_display_state, 1))
        self._reference_display_button.clicked.connect(partial(self._set_display_state, 2))
        self._color_combo.currentIndexChanged.connect(self._on_control_color_combo_changed)
        self._color_index_slider.valueChanged.connect(self._on_set_control_index_color)
        self._color_dialog_widget.colorChanged.connect(self._on_control_rgb_color_changed)
        self._color_rgb_live_mode_checkbox.toggled.connect(self._on_toggled_rgb_live_mode)
        self._color_rgb_apply_button.clicked.connect(self._on_apply_rgb_color)

    def showEvent(self, event):
        self.controls_list.setCurrentItem(self.controls_list.topLevelItem(0))
        super(ControlsWidget, self).showEvent(event)

    def resizeEvent(self, event):
        super(ControlsWidget, self).resizeEvent(event)
        self.controls_viewer.update_coords()

    # =================================================================================================================
    # BASE
    # =================================================================================================================

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
            'shape_data': [control_shape() for control_shape in item.shapes],
            'size': self.radius.value(),
            'name': self._name_line.text(),
            'offset': self.offset(),
            'ori': self.factor(),
            'axis_order': self.rotate_order.itemData(controldata.axis_eq[self.rotate_order.currentText()]),
            'shape_parent': self.parent_shape.isChecked(),
            'mirror': self.mirror.checkedButton().value,
            'color': self.color_picker.color().getRgbF()
        }

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

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
        self.controls_list.setFocus(Qt.TabFocusReason)

    def _update_control_colors(self):
        """
        Internal function that updates the DCC control colors
        """

        control_colors = self._client.get_control_colors() or list()

        qtutils.clear_layout(self._color_index_buttons_layout)

        current_index = 0
        index_buttons = []
        current_color_row = 0
        current_color_column = 0
        while True:
            if current_index >= len(control_colors):
                break

            if current_color_column > 7:
                current_color_column = 0
                current_color_row += 1

            color_index_button = buttons.BaseButton()
            color_index_button.setFixedWidth(30)
            color_index_button.setFixedHeight(30)
            color_index_button.clicked.connect(partial(self._on_set_control_index_color, current_index))
            index_buttons.append(color_index_button)
            color_index_button.setStyleSheet(
                " background-color:rgb(%s,%s,%s);" % (
                    control_colors[current_index][0] * 255,
                    control_colors[current_index][1] * 255,
                    control_colors[current_index][2] * 255)
            )
            self._color_index_buttons_layout.addWidget(color_index_button, current_color_row, current_color_column)
            current_index += 1
            current_color_column += 1

        self._color_index_slider.set_range(0, len(control_colors) - 1)

    def _update_fonts(self):
        """
        Internal function that updates fonts combo box
        """

        self._fonts_combo.clear()

        all_fonts = list()
        fonts = self._client.get_fonts() or list()
        for font_name in fonts:
            all_fonts.append(font_name.split('-')[0])
        if not all_fonts:
            return

        all_fonts = sorted(list(set(all_fonts)))

        self._fonts_combo.addItems(all_fonts)
        default_index = self._fonts_combo.findText('Times New Roman')
        if default_index is not None:
            self._fonts_combo.setCurrentIndex(default_index)

    def _set_display_state(self, display_index):
        """
        Internal function that sets the display mode of the selected controls
        :param display_index: int, 0 = Normal; 1 = Template; 2 = Reference
        """

        return self._client.update_display_state(display_index=display_index)

    def _set_index_color(self, index=0):
        """
        Internal function that sets the index color of the selected controls
        :param index: int
        """

        success = self._client.set_index_color(index)
        if not success:
            return False

        self._color_index_slider.blockSignals(True)
        try:
            self._color_index_slider.set_value(index)
        finally:
            self._color_index_slider.blockSignals(False)

        return success

    def _set_rgb_color(self, color=None):
        """
        Internal function that sets the RGB color of the selected controls
        :param color: QColor (0.0 - 1.0)
        """

        color = color or self._color_dialog_widget.color()
        color = [color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0]

        return self._client.set_rgb_color(color=color)

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

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
                r = self._client.get_joint_radius()
            except (NameError, TypeError, IndexError, AttributeError):
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

        capture_dialog = controlcapturer.CaptureControl(exec_fn=self._on_add_control, new_ctrl=sel, parent=self)
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

        v = float(self.radius.value())
        if v > 0:
            try:
                r = self._client.get_joint_radius()
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

    def _on_control_text_changed(self, text):
        self._create_text_control_button.setEnabled(bool(text))

    def _on_create_control_text(self):
        input_text = self._text_line.text()
        font_type = self._fonts_combo.currentText() or 'Times New Roman'
        if not input_text:
            return

        return controllib.create_text_control(text=input_text, font=font_type)

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
            tpRigToolkit.logger.error(
                'Control for curve "{}" not created! Aborting control add operation ...'.format(orig))
            return

        item = QTreeWidgetItem(self.controls_list, [name])
        item.control = new_ctrl
        item.shapes = new_ctrl.shapes

        self.controls_list.addTopLevelItem(item)
        self.controls_list.setCurrentItem(item)

        self._client.select_node(orig)

    def _on_create_control(self):
        """
        Function that creates a new curve based on Maya selection
        """

        control_data = self.get_selected_control_item_data()
        if not control_data:
            return

        control_data['target_object'] = self._client.selected_nodes()
        axis_order = control_data.get('axis_order', 'XYZ')
        control_data['axis_order'] = self.rotate_order.itemData(controldata.axis_eq[axis_order[0]])
        control_data.pop('control_name', None)

        controls_file = self._controls_lib.controls_file
        ccs = self._client.create_control(control_data, controls_file)[0]

        self._client.clear_selection()
        self._client.select_node(ccs, add_to_selection=True)

    def _on_assign_control(self):
        """
        Function that is called when the user press Assign Control button in UI
        Updates shape of the selected curve
        """

        sel = self._client.selected_nodes()
        if not sel:
            tpRigToolkit.logger.error('Please select a curve transform before assigning a new shape')
            return

        item = self.controls_list.currentItem()
        if item:
            self._client.enable_undo()
            ccs = self._controls_lib.create_control(
                shape_data=item.shapes,
                target_object=sel,
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

        self._client.disable_undo()

    def _on_show_color_panel(self):
        """
        Internal callback function that is called when the user wants to select a color
        :return:
        """

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
        """
        Internal callback function that is called when a control color has been changed
        :param color:
        :return:
        """

        self.controls_viewer.control_color = color
        self.controls_viewer.update_coords()

    def _on_control_color_combo_changed(self, index):
        if index == 0:
            self._color_index_widget.setVisible(True)
            self._color_rgb_widget.setVisible(False)
        else:
            self._color_index_widget.setVisible(False)
            self._color_rgb_widget.setVisible(True)

    def _on_set_control_index_color(self, index):
        """
        Internal callback function that is called when index color is selected
        :param index: int
        """

        self._set_index_color(index)

    def _on_control_rgb_color_changed(self, color):
        """
        Internal callback function that is called when RGB color wheel is updated
        :param color: QColor
        """

        if not self._color_rgb_live_mode_checkbox.isChecked():
            return

        self._set_rgb_color(color)

    def _on_toggled_rgb_live_mode(self, flag):
        """
        Internal callback function that is called when RGB live mode is toggled
        :param flag: bool
        """

        self._color_rgb_apply_button.setVisible(not flag)

    def _on_apply_rgb_color(self):
        """
        Internal callback function that is called when RGB color is applied through Apply button
        """

        self._set_rgb_color()


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
