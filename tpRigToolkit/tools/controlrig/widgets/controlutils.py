#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Control Rig utils widget view class implementation
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDcc as tp
from tpDcc.libs.python import python
from tpDcc.libs.qt.core import base, qtutils
from tpDcc.libs.qt.widgets import layouts, buttons, checkbox, dividers, combobox, lineedit, expandables, sliders, color


class ControlRigUtilsView(base.BaseWidget, object):
    def __init__(self, client, parent=None):

        self._model = ControlRigUtilsModel()
        self._controller = ControlRigUtilsController(client=client, model=self._model)

        super(ControlRigUtilsView, self).__init__(parent=parent)

        self.refresh()

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def ui(self):
        super(ControlRigUtilsView, self).ui()

        paint_icon = tp.ResourcesMgr().icon('paint')
        cursor_icon = tp.ResourcesMgr().icon('cursor')

        self._utils_expander = expandables.ExpanderWidget(parent=self)
        self._utils_expander.setDragDropMode(expandables.ExpanderDragDropModes.NoDragDrop)

        display_widget = QWidget(parent=self)
        display_layout = layouts.HorizontalLayout()
        display_widget.setLayout(display_layout)
        self._normal_display_button = buttons.BaseButton('Normal', parent=self)
        self._template_display_button = buttons.BaseButton('Template', parent=self)
        self._reference_display_button = buttons.BaseButton('Reference', parent=self)
        display_layout.addWidget(self._normal_display_button)
        display_layout.addWidget(self._template_display_button)
        display_layout.addWidget(self._reference_display_button)

        color_widget = QWidget(parent=self)
        color_layout = layouts.VerticalLayout(spacing=2, margins=(0, 0, 0, 0))
        color_layout.setAlignment(Qt.AlignTop)
        color_widget.setLayout(color_layout)
        self._color_mode_combo = combobox.BaseComboBox(parent=self)
        self._color_mode_combo.addItems(['Index', 'RGB'])
        color_layout.addWidget(self._color_mode_combo)
        color_layout.addWidget(dividers.Divider())

        self._color_index_widget = QWidget(parent=self)
        color_index_layout = layouts.VerticalLayout(spacing=2, margins=(0, 0, 0, 0))
        self._color_index_widget.setLayout(color_index_layout)
        self._color_index_buttons_layout = layouts.GridLayout(spacing=0, margins=(0, 0, 0, 0))

        self._color_index_slider = sliders.HoudiniDoubleSlider(self, slider_type='int')

        color_index_layout.addLayout(self._color_index_buttons_layout)
        color_index_layout.addWidget(dividers.Divider(parent=self))
        color_index_layout.addWidget(self._color_index_slider)

        self._color_rgb_widget = QWidget(parent=self)
        color_rgb_layout = layouts.VerticalLayout(spacing=2, margins=(0, 0, 0, 0))
        self._color_rgb_widget.setLayout(color_rgb_layout)
        self._color_dialog_widget = color.ColorDialogWidget()
        rgb_buttons_layout = layouts.HorizontalLayout(spacing=2, margins=(0, 0, 0, 0))
        self._color_rgb_live_mode_checkbox = checkbox.BaseCheckBox('Live Update', parent=self)
        self._color_rgb_live_mode_checkbox.setChecked(True)
        self._color_rgb_apply_button = buttons.BaseButton('Apply', parent=self)
        self._color_rgb_apply_button.setVisible(False)
        rgb_buttons_layout.addWidget(self._color_rgb_live_mode_checkbox)
        rgb_buttons_layout.addStretch()
        rgb_buttons_layout.addWidget(self._color_rgb_apply_button)
        color_rgb_layout.addWidget(self._color_dialog_widget)
        color_rgb_layout.addWidget(dividers.Divider(parent=self))
        color_rgb_layout.addLayout(rgb_buttons_layout)
        self._color_rgb_widget.setVisible(False)
        color_buttons_layout = layouts.HorizontalLayout(spacing=2, margins=(0, 0, 0, 0))
        self._get_control_color_button = buttons.BaseButton('Get Color', icon=paint_icon, parent=self)
        self._select_similar_color_button = buttons.BaseButton('Select Similar Color', icon=cursor_icon, parent=self)
        self._select_from_color_button = buttons.BaseButton('Select from Color', icon=cursor_icon, parent=self)
        color_buttons_layout.addWidget(self._get_control_color_button)
        color_buttons_layout.addWidget(self._select_similar_color_button)
        color_buttons_layout.addWidget(self._select_from_color_button)

        color_layout.addWidget(self._color_index_widget)
        color_layout.addWidget(self._color_rgb_widget)
        color_layout.addWidget(dividers.Divider(parent=self))
        color_layout.addLayout(color_buttons_layout)

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

        def mirror_click(button, flag):
            enabled = flag and button is not self._none_btn
            for w in (self._mirror_color_selector, self._from_name_line, self._to_name_line, self._mirror_btn,
                      self._world_position_radio, self._original_position_radio, self._mirrored_position_radio):
                w.setEnabled(enabled)

        self._none_btn.toggled.connect(partial(mirror_click, self._none_btn))
        for btn in (self._xy_btn, self._yz_btn, self._zx_btn):
            self._mirror_button_group.addButton(btn)
            btn.setStyleSheet(self._none_btn.styleSheet())
            btn.setToolTip('Set mirror mode on {}plane'.format(btn.text()))
            btn.setCheckable(True)
            btn.value = btn.text()
            btn.toggled.connect(partial(mirror_click, btn))

        mirror_layout.addLayout(
            qtutils.get_line_layout('Axis : ', self, self._none_btn, self._xy_btn, self._yz_btn, self._zx_btn))

        self._mirror_color_selector = color.ColorSelector()
        self._mirror_color_selector.set_reset_on_close(False)
        self._mirror_color_selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._mirror_color_selector.set_display_mode(color.ColorSelector.DisplayMode.NO_ALPHA)
        self._mirror_color_selector.set_panel_parent(self.parent())

        mirror_layout.addLayout(qtutils.get_line_layout('Mirror Color : ', self, self._mirror_color_selector))
        self._from_name_line = lineedit.BaseLineEdit(text='from', parent=self)
        self._to_name_line = lineedit.BaseLineEdit(text='to', parent=self)
        mirror_layout.addLayout(
            qtutils.get_line_layout(
                'Name Pattern : ', self, self._from_name_line, QLabel(u'\u25ba', self), self._to_name_line))
        self._world_position_radio = buttons.BaseRadioButton('World', parent=self)
        self._original_position_radio = buttons.BaseRadioButton('Original', parent=self)
        self._mirrored_position_radio = buttons.BaseRadioButton('Mirrored', parent=self)
        self._mirror_replace_cbx = checkbox.BaseCheckBox('Replace', parent=self)
        self._mirror_mode_button_group = QButtonGroup()
        mirror_layout.addLayout(
            qtutils.get_line_layout('Mode : ', self, self._world_position_radio, self._original_position_radio,
                                    self._mirrored_position_radio, self._mirror_replace_cbx))
        self._mirror_mode_button_group.addButton(self._world_position_radio)
        self._mirror_mode_button_group.addButton(self._original_position_radio)
        self._mirror_mode_button_group.addButton(self._mirrored_position_radio)
        self._mirror_mode_button_group.setExclusive(True)

        self._mirror_btn = buttons.BaseButton('Mirror Shape(s)', parent=self)
        for w in (self._mirror_color_selector, self._from_name_line, self._to_name_line, self._mirror_btn,
                  self._world_position_radio, self._original_position_radio, self._mirrored_position_radio):
            w.setEnabled(False)
        mirror_layout.addWidget(self._mirror_btn)

        text_widget = QWidget(parent=self)
        text_layout = layouts.VerticalLayout()
        text_widget.setLayout(text_layout)
        self._text_line = lineedit.BaseLineEdit(parent=self)
        self._text_line.setPlaceholderText('Type control text ...')
        self._fonts_combo = combobox.BaseComboBox()
        self._create_text_control_button = buttons.BaseButton('Create Text', parent=self)
        self._create_text_control_button.setEnabled(False)
        text_layout.addWidget(self._text_line)
        text_layout.addWidget(self._fonts_combo)
        text_layout.addWidget(dividers.Divider(parent=self))
        text_layout.addWidget(self._create_text_control_button)

        self._utils_expander.addItem(title='Mirror', widget=mirror_widget, collapsed=True)
        self._utils_expander.addItem(title='Display', widget=display_widget, collapsed=True)
        self._utils_expander.addItem(title='Color', widget=color_widget, collapsed=True)
        self._utils_expander.addItem(title='Text', widget=text_widget, collapsed=True)
        self.main_layout.addWidget(self._utils_expander)

    def setup_signals(self):
        self._normal_display_button.clicked.connect(partial(self._controller.set_display_state, 0))
        self._template_display_button.clicked.connect(partial(self._controller.set_display_state, 1))
        self._reference_display_button.clicked.connect(partial(self._controller.set_display_state, 2))
        self._color_mode_combo.currentIndexChanged.connect(self._on_control_color_combo_changed)
        self._color_index_slider.valueChanged.connect(self._controller.set_index_color)
        self._color_dialog_widget.colorChanged.connect(self._controller.set_rgb_color)
        self._color_rgb_live_mode_checkbox.toggled.connect(self._on_toggled_rgb_live_mode)
        self._color_rgb_apply_button.clicked.connect(self._controller.apply_rgb_color)
        self._text_line.textChanged.connect(self._on_control_text_changed)
        self._fonts_combo.currentTextChanged.connect(self._controller.set_font)
        self._create_text_control_button.clicked.connect(self._controller.create_control_text)
        self._mirror_btn.clicked.connect(self._controller.mirror_shapes)
        self._mirror_button_group.buttonClicked.connect(self._on_mirror_button_clicked)
        self._mirror_color_selector.closedColor.connect(self._controller.set_mirror_color)
        self._from_name_line.textChanged.connect(self._controller.set_mirror_from)
        self._to_name_line.textChanged.connect(self._controller.set_mirror_to)
        self._mirror_mode_button_group.buttonClicked.connect(self._on_mirror_mode_radio_changed)
        self._mirror_replace_cbx.toggled.connect(self._controller.set_mirror_replace)
        self._get_control_color_button.clicked.connect(self._on_get_control_color)
        self._select_similar_color_button.clicked.connect(self._controller.select_controls_by_color)
        self._select_from_color_button.clicked.connect(self._controller.select_controls_from_current_color)

        self._model.colorModeChanged.connect(self._color_mode_combo.setCurrentIndex)
        self._model.controlColorsChanged.connect(self._update_controls_colors)
        self._model.indexColorChanged.connect(self._on_set_index_color)
        self._model.rgbColorChanged.connect(self._on_control_rgb_color_changed)
        self._model.textChanged.connect(self._text_line.setText)
        self._model.fontsChanged.connect(self._update_fonts)
        self._model.fontChanged.connect(self._fonts_combo.setCurrentText)
        self._model.mirrorPlaneChanged.connect(self._on_mirror_plane_changed)
        self._model.mirrorColorChanged.connect(self._on_set_mirror_color)
        self._model.mirrorFromChanged.connect(self._from_name_line.setText)
        self._model.mirrorToChanged.connect(self._to_name_line.setText)
        self._model.mirrorModeChanged.connect(self._on_mirror_mode_changed)
        self._model.mirrorReplaceChanged.connect(self._mirror_replace_cbx.setChecked)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def refresh(self):
        self._controller.update_control_colors()
        self._controller.update_fonts()

        self._color_rgb_live_mode_checkbox.setChecked(self._model.rgb_color_live_mode)
        self._color_mode_combo.setCurrentIndex(self._model.color_mode)
        self._on_set_index_color(self._model.index_color)
        self._color_dialog_widget.set_color(self._model.rgb_color)
        self._text_line.setText(self._model.text)
        self._fonts_combo.setCurrentText(self._model.font)
        self._on_mirror_plane_changed(self._model.mirror_plane)
        self._mirror_color_selector.set_color(self._model.mirror_color)
        self._from_name_line.setText(self._model.mirror_from)
        self._to_name_line.setText(self._model.mirror_to)
        self._on_mirror_mode_changed(self._model.mirror_mode)
        self._mirror_replace_cbx.setChecked(self._model.mirror_replace)

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _update_controls_colors(self, control_colors):
        """
        Internal function that updates the DCC control colors
        """

        qtutils.clear_layout(self._color_index_buttons_layout)

        current_index = 0
        index_buttons = list()
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
            color_index_button.clicked.connect(partial(self._controller.set_index_color, current_index))
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

    def _update_fonts(self, fonts):
        """
        Internal function that updates fonts combo box
        """

        self._fonts_combo.clear()

        all_fonts = list()
        for font_name in fonts:
            all_fonts.append(font_name.split('-')[0])
        if not all_fonts:
            return

        all_fonts = sorted(list(set(all_fonts)))

        self._fonts_combo.blockSignals(True)
        try:
            self._fonts_combo.addItems(all_fonts)
        finally:
            self._fonts_combo.blockSignals(False)
        self._fonts_combo.setCurrentText(self._model.font)

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

    def _on_control_color_combo_changed(self, index):
        """
        Internal callback function that is called when mode index is changed by the user
        :param index: int
        """

        if index == 0:
            self._color_index_widget.setVisible(True)
            self._color_rgb_widget.setVisible(False)
        else:
            self._color_index_widget.setVisible(False)
            self._color_rgb_widget.setVisible(True)

        self._controller.set_color_mode(index)

    def _on_set_index_color(self, index):
        """
        Internal callback function that is called when index color is selected
        :param index: int
        """

        self._color_index_slider.blockSignals(True)
        try:
            self._color_index_slider.set_value(index)
        finally:
            self._color_index_slider.blockSignals(False)

    def _on_control_rgb_color_changed(self, color):
        """
        Internal callback function that is called when RGB color wheel is updated
        :param color: QColor
        """
            
        color_rgb_live_mode = self._model.rgb_color_live_mode

        if color_rgb_live_mode:
            self._controller.apply_rgb_color(color)

    def _on_toggled_rgb_live_mode(self, flag):
        """
        Internal callback function that is called when RGB live mode is toggled
        :param flag: bool
        """

        self._controller.set_rgb_color_live_mode(flag)
        self._color_rgb_apply_button.setVisible(not flag)

    def _on_control_text_changed(self, text):
        """
        Internal callback function that updates control text
        :param text: str
        """

        self._controller.set_text(text)
        self._create_text_control_button.setEnabled(bool(text))

    def _on_mirror_button_clicked(self, mirror_button_clicked):
        """
        Internal function that is called when the user clicks on a mirror button
        :param mirror_button_clicked: BaseButton
        """

        mirror_plane = mirror_button_clicked.value
        self._controller.set_mirror_plane(mirror_plane)

    def _on_mirror_mode_radio_changed(self, position_radio_clicked):
        """
        Internal function that is called when the user clicks on the position radio button
        :param position_radio_clicked: BaseRadioButton
        """

        for i, btn in enumerate(self._mirror_mode_button_group.buttons()):
            if btn == position_radio_clicked:
                self._controller.set_mirror_mode(i)

    def _on_mirror_mode_changed(self, mirror_index):
        """
        Internall callback function that is called when mirror position button is changed
        :param mirror_index: int
        """

        position_radio = self._mirror_mode_button_group.buttons()[mirror_index]
        position_radio.setChecked(True)

    def _on_mirror_plane_changed(self, mirror_plane):
        """
        Internal function that is called when mirror plane button is changed
        :param mirror_plane: str
        """

        for mirror_axis_button in self._mirror_button_group.buttons():
            if mirror_axis_button.value == mirror_plane:
                mirror_axis_button.setChecked(True)
                break

    def _on_set_mirror_color(self, color_list):
        """
        Internal callback function that is called when mirror color is updated
        :param color_list: list
        """

        new_color = [channel_color * 255 for channel_color in color_list]
        self._mirror_color_selector.set_color(new_color)

    def _on_get_control_color(self):
        """
        Internal callback function that is called when get control color button is pressed by user
        """

        control_color = self._controller.get_control_color()
        if not control_color:
            return

        self._model.blockSignals(True)
        try:
            self._controller.set_rgb_color(control_color)
            self._color_dialog_widget.set_color(control_color)
        finally:
            self._model.blockSignals(False)


class ControlRigUtilsModel(QObject, object):

    colorModeChanged = Signal(int)
    indexColorChanged = Signal(int)
    rgbColorChanged = Signal(object)
    rgbColorLiveModeChanged = Signal(bool)
    controlColorsChanged = Signal(list)
    fontsChanged = Signal(list)
    textChanged = Signal(str)
    fontChanged = Signal(str)
    mirrorPlaneChanged = Signal(str)
    mirrorColorChanged = Signal(tuple)
    mirrorFromChanged = Signal(str)
    mirrorToChanged = Signal(str)
    mirrorModeChanged = Signal(int)
    mirrorReplaceChanged = Signal(bool)

    def __init__(self):
        super(ControlRigUtilsModel, self).__init__()

        # TODO: Color mode default value can vary between DCCs, we should add a client function to retrieve if a
        # TODO: specific DCC supports index or RGB based colors
        self._color_mode = 1
        self._index_color = 0
        self._rgb_color = [240, 245, 255]
        self._rgb_color_live_mode = False
        self._controls_colors = list()
        self._fonts = list()
        self._text = ''
        self._font = 'Times New Roman'
        self._mirror_plane = 'XY'
        self._mirror_color = [255, 0, 0]
        self._mirror_from = '_l_'
        self._mirror_to = '_r_'
        self._mirror_mode = 0
        self._mirror_replace = True

    @property
    def color_mode(self):
        return self._color_mode

    @color_mode.setter
    def color_mode(self, value):
        self._color_mode = int(value)
        self.colorModeChanged.emit(self._color_mode)

    @property
    def index_color(self):
        return self._index_color

    @index_color.setter
    def index_color(self, value):
        self._index_color = int(value)
        self.indexColorChanged.emit(self._index_color)

    @property
    def rgb_color(self):
        return self._rgb_color

    @rgb_color.setter
    def rgb_color(self, new_color):
        self._rgb_color = new_color
        self.rgbColorChanged.emit(self._rgb_color)

    @property
    def rgb_color_live_mode(self):
        return self._rgb_color_live_mode

    @rgb_color_live_mode.setter
    def rgb_color_live_mode(self, flag):
        self._rgb_color_live_mode = flag
        self.rgbColorLiveModeChanged.emit(self._rgb_color_live_mode)

    @property
    def control_colors(self):
        return self._control_colors

    @control_colors.setter
    def control_colors(self, colors_list):
        self._controls_colors = python.force_list(colors_list)
        self.controlColorsChanged.emit(self._controls_colors)

    @property
    def fonts(self):
        return self._fonts

    @fonts.setter
    def fonts(self, fonts_list):
        self._fonts = python.force_list(fonts_list)
        self.fontsChanged.emit(self._fonts)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = str(value)
        self.textChanged.emit(self._text)

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, font_name):
        self._font = str(font_name)
        self.fontChanged.emit(self._font)

    @property
    def mirror_plane(self):
        return self._mirror_plane

    @mirror_plane.setter
    def mirror_plane(self, value):
        self._mirror_plane = str(value)
        self.mirrorPlaneChanged.emit(self._mirror_plane)

    @property
    def mirror_color(self):
        return self._mirror_color

    @mirror_color.setter
    def mirror_color(self, color_tuple):
        self._mirror_color = python.force_tuple(color_tuple)
        self.mirrorColorChanged.emit(self._mirror_color)

    @property
    def mirror_from(self):
        return self._mirror_from

    @mirror_from.setter
    def mirror_from(self, value):
        self._mirror_from = str(value)
        self.mirrorFromChanged.emit(self._mirror_from)

    @property
    def mirror_to(self):
        return self._mirror_to

    @mirror_to.setter
    def mirror_to(self, value):
        self._mirror_to = str(value)
        self.mirrorToChanged.emit(self._mirror_to)

    @property
    def mirror_mode(self):
        return self._mirror_mode

    @mirror_mode.setter
    def mirror_mode(self, value):
        self._mirror_mode = int(value)
        self.mirrorModeChanged.emit(self._mirror_mode)

    @property
    def mirror_replace(self):
        return self._mirror_replace

    @mirror_replace.setter
    def mirror_replace(self, flag):
        self._mirror_replace = bool(flag)
        self.mirrorReplaceChanged.emit(self._mirror_replace)


class ControlRigUtilsController(object):
    def __init__(self, client, model):
        super(ControlRigUtilsController, self).__init__()

        self._client = client
        self._model = model

    def update_control_colors(self):
        """
        Updates available control colors
        :return: list
        """

        control_colors = self._client.get_control_colors() or list()
        self._model.control_colors = control_colors

    def update_fonts(self):
        """
        Updates available fonts
        :return: list
        """

        fonts = self._client.get_fonts() or list()
        self._model.fonts = fonts

    def apply_rgb_color(self, rgb_color=None):
        rgb_color = rgb_color or self._model.rgb_color
        self._client.set_rgb_color(rgb_color)

    def set_display_state(self, display_index):
        """
        Sets the display mode of the selected controls
        :param display_index: int
        """

        return self._client.update_display_state(display_index=display_index)

    def set_color_mode(self, mode_index):
        """
        Sets the color mode to use (0 = index; 1 = RGB)
        :param mode_index: int
        """

        self._model.color_mode = mode_index

    def set_index_color(self, index):
        """
        Sets the index color of the selected controls
        :param index: int
        """

        success = self._client.set_index_color(index)
        if not success:
            return False

        self._model.index_color = index

        return True

    def set_rgb_color(self, rgb_color):
        """
        Sets the RGB color of the selected controls
        :param rgb_color: QColor
        """

        color_list = rgb_color.toRgb().toTuple() if hasattr(rgb_color, 'toRgb') else rgb_color
        color_list = [color_channel / 255 for color_channel in color_list]
        self._model.rgb_color = color_list

    def set_rgb_color_live_mode(self, flag):
        """
        Sets whether RGB color should be applied on live mode or not
        :param flag: bool
        """

        self._model.rgb_color_live_mode = flag

    def set_text(self, text):
        """
        Sets the text for the new text control
        :param text: str
        """

        self._model.text = text

    def set_font(self, font_name):
        """
        Sets current font used
        :param font_name: str
        """

        self._model.font = font_name

    def set_mirror_plane(self, mirror_plane_index):
        """
        Sets the mirror plane used to create the control
        :param mirror_plane_index: int
        """

        self._model.mirror_plane = mirror_plane_index

    def set_mirror_color(self, mirror_color):
        """
        Sets the current mirror control color
        :param mirror_color: QColor, Qt color in 0-1 range
        """

        color_list = mirror_color.toRgb().toTuple() if hasattr(mirror_color, 'toRgb') else mirror_color
        color_list = [color_channel / 255 for color_channel in color_list]
        self._model.mirror_color = color_list

    def set_mirror_from(self, value):
        """
        Sets the name from name for the mirror
        :param value: str
        """

        self._model.mirror_from = value

    def set_mirror_to(self, value):
        """
        Sets the name to name for the mirror
        :param value: str
        """

        self._model.mirror_to = value

    def set_mirror_mode(self, position_index):
        """
        Sets the type of mirror to use
        :param position_index: int
        """

        self._model.mirror_mode = position_index

    def set_mirror_replace(self, flag):
        """
        Sets whether or not mirror replace behaviur is active or not
        :param flag: bool
        """

        self._model.mirror_replace = flag

    def create_control_text(self):
        """
        Creates a new text control
        """

        text = self._model.text
        font = self._model.font
        if not text or not font:
            return False

        return self._client.create_control_text(text, font)

    def mirror_shapes(self):
        """
        Mirror shapes
        """

        mirror_plane = self._model.mirror_plane
        mirror_color = self._model.mirror_color
        from_name = self._model.mirror_from
        to_name = self._model.mirror_to
        mirror_mode = self._model.mirror_mode
        mirror_replace = self._model.mirror_replace

        return self._client.mirror_control(mirror_plane, mirror_color, from_name, to_name, mirror_mode, mirror_replace)

    def get_control_color(self):
        """
        Returns current control color
        :return: list(float, float, float)
        """

        return self._client.get_control_color()

    def select_controls_by_color(self):
        """
        Selects current scene controls that have the same color of the current selected control
        :return: list(str), list of selected nodes
        """

        return self._client.select_controls_by_color()

    def select_controls_from_current_color(self):
        """
        Selects current scene controls that have the same color of the current selected RGB color in color picker
        """

        current_rgb_color = self._model.rgb_color
        if not current_rgb_color:
            return

        return self._client.select_controls_by_color(rgb_color=current_rgb_color)
