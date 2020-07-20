#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains control viewer widget for tpRigToolkit.tools.controlrig
"""

from __future__ import print_function, division, absolute_import

import math
from copy import copy

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *


class ControlViewer(QWidget, object):
    """
    Custom 3D viewer to display control shapes
    """

    class ShapePool(object):
        """
        Stack for the displayed shapes, with a direction conversion to QLines
        """

        def __init__(self):
            super(ControlViewer.ShapePool, self).__init__()
            self._shapes = list()

        def get_shapes(self):
            return self._shapes

        shapes = property(get_shapes)

        def __setitem__(self, key, points):
            pts = list()
            if len(points):
                start = points[0]
                for pt in points[1:]:
                    pts.append(QLineF(start, pt))
                    start = pt
            self._shapes[key] = pts

        def __iter__(self):
            for shape in self._shapes:
                yield shape

        def flush(self, length):
            for idx in range(len(self._shapes) - 1, -1, -1):
                self._shapes.pop(idx)
            for i in range(length):
                self._shapes.append([])

    def __init__(self, parent=None):
        super(ControlViewer, self).__init__(parent=parent)

        self.setObjectName('controlViewer')
        self._shapes = list()
        self._baked_lines = self.ShapePool()
        self._control = None

        self._mouse_pos = QPoint(0, 0)
        self._mouse_press = False

        self._rotate_order = 'XYZ'

        self._scale = 30
        self._ref = 0.5
        self._rotation = 235
        self._height_rotate = 60

        self._draw_ref = False
        self._draw_axis = True

        self._gradient_color_1 = QColor(44, 46, 48)
        self._gradient_color_2 = QColor(124, 143, 163)
        self._control_color = QColor(240, 245, 255)
        self._control_line_width = 1.5

        gradient = QLinearGradient(QRectF(self.rect()).bottomLeft(), QRectF(self.rect()).topLeft())
        gradient.setColorAt(0, self._gradient_color_1)
        gradient.setColorAt(1, self._gradient_color_2)
        self._background = QBrush(gradient)
        self._axis_pen = [QPen(QColor(255, 0, 0), 0.5), QPen(QColor(0, 255, 0), 0.5), QPen(QColor(125, 125, 255), 0.5)]
        self._sub_grid_pen = QPen(QColor(74, 74, 75), 0.25)
        self._control_pen = QPen(self._control_color, self._control_line_width)

        self._ref_display = QCheckBox('joint', self)
        sheet = '''
        QCheckBox {color:white; background-color: transparent;}
        QCheckBox:unchecked {color:rgb(212, 201, 206);}
        QCheckBox::indicator {width: 10px;height: 10px;background:rgb(34, 38, 45);
        border:1px solid rgb(134, 138, 145);border-radius:5px;}
        QCheckBox::indicator:hover {background:rgb(34, 108, 185);border:1px solid white; border-radius:5px;}
        QCheckBox::indicator:checked{background:rgb(74, 168, 235);border:2px solid rgb(34, 108, 185); padding:-1px;}
        QCheckBox::indicator:checked:hover{background:rgb(74, 168, 235);border:1px solid white; padding:0px;}
        '''

        self._ref_display.setStyleSheet(sheet)
        self._ref_display.setGeometry(5, -2, self._ref_display.width(), self._ref_display.height())
        self._ref_display.stateChanged.connect(self._on_toggle_ref)

        self._axis_display = QCheckBox('axis', self)
        self._axis_display.setStyleSheet(sheet)
        self._axis_display.setGeometry(5, 13, self._axis_display.width(), self._axis_display.height())
        self._axis_display.stateChanged.connect(self._on_toggle_axis)
        self._axis_display.setChecked(True)

        self._infos = QLabel('', self)
        self._infos.setStyleSheet('QLabel {color:rgb(134, 138, 145); background-color: transparent;}')

    @property
    def control(self):
        return self._control

    @control.setter
    def control(self, ctrl):
        self._control = ctrl

    @property
    def ref(self):
        return self._ref

    @ref.setter
    def ref(self, value):
        self._ref = value

    @property
    def shapes(self):
        return self._shapes

    @shapes.setter
    def shapes(self, shapes_list):
        self._shapes = shapes_list

    @property
    def control_color(self):
        return self._control_color

    @control_color.setter
    def control_color(self, color):
        self._control_color = color
        self._control_pen = QPen(self._control_color, self._control_line_width)

    def mousePressEvent(self, event):
        if event.button() == 1:
            self._mouse_press = True
            self._mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self._mouse_press:
            delta = self._mouse_pos - event.pos()
            self._rotation -= delta.x()
            self._height_rotate = min(max(self._height_rotate + delta.y(), 60), 120)
            self._mouse_pos = event.pos()
            self.update_coords()

    def mouseReleaseEvent(self, event):
        self._mouse_press = False

    def wheelEvent(self, event):
        self._scale = max(self._scale + event.delta() / 40, 10)
        self.update_coords()

    def resizeEvent(self, event):
        gradient = QLinearGradient(QRectF(self.rect()).bottomLeft(), QRectF(self.rect()).topLeft())
        gradient.setColorAt(0, QColor(44, 46, 48))
        gradient.setColorAt(1, QColor(124, 143, 163))
        self._background = QBrush(gradient)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)

        painter.setRenderHint(painter.Antialiasing)
        painter.setBrush(self._background)
        painter.drawRoundedRect(QRect(0, 0, self.size().width(), self.size().height()), 4, 4)
        self._draw_grid(painter=painter)
        painter.setPen(self._control_pen)

        for shape in self._baked_lines:
            painter.drawLines(shape)

        painter.end()

    def load(self, shapes):
        """
        Updates the viewport with new shapes, cleaning old stuff and smoothing the shape using
        Catmull Rom method
        :param shapes:
        """

        self._shapes = shapes
        for i, shape in enumerate(self._shapes):
            if shape.degree != 1 and not shape.smooth:
                shape.cvs = self._smooth(copy(shape.cvs), shape.degree, shape.periodic)
                shape.smooth = True
                shape.apply_transform()

        self.update_coords()

    def update_coords(self):
        """
        Refresh 2D lines viewport array
        """

        self._baked_lines.flush(len(self._shapes))

        for i, shape in enumerate(self._shapes):
            self.set_shape_coords(shape, i)

        self.update()

    def set_shape_coords(self, shape, shape_index):
        """
        This converts shape's transfomred CVs into 2D points for the viewer's drawing
        :param shape:
        :param shape_index:
        """

        points_2d = list()
        for pt in shape.transformed_cvs:
            points_2d.append(self._convert_3D_to_2D(*pt))

        # If the shape is closed, we add the first points to close the loop
        if shape.periodic and shape.degree == 1:
            points_2d.append(self._convert_3D_to_2D(*shape.transformed_cvs[0]))

        self._baked_lines[shape_index] = points_2d
    # endregion

    # region Private Functions
    def _convert_3D_to_2D(self, x, y, z):
        """
        Cheap conversion from 3D coordinates to 2D coordinates depending on the view
        :param x: int, x coordinate
        :param y: int, y coordinate
        :param z: int, z coordinate
        :return: QPointF, 2D coordinates
        """

        _x = x * math.cos(math.radians(self._rotation))
        _x -= z * math.cos(math.radians(-self._rotation + 90))
        _x *= self._scale

        # We do a 2D projection (key to fake the vertical camera rotation)
        _y = (x * math.sin(math.radians(self._rotation)) - y + z * math.sin(
            math.radians(-self._rotation + 90))) * self._scale
        # Round the vertical rotate to achieve a uniform scaling on the shape when the camera turns up and down
        _y *= math.cos(math.radians(self._height_rotate))
        # Push compensation from the Y attribute of the point
        _y += y * self._scale * (math.tan(math.radians(90 - self._height_rotate)) + math.sin(
            math.radians(self._height_rotate)))
        _y *= -1

        # Center the point on the view
        _x += self.width() * 0.5
        _y += self.height() * 0.5

        return QPointF(_x, _y)

    def _smooth(self, cv, deg, periodic):
        """
        Smoothing the given coordinates (cv) using the Catmull Rom method

        # TODO: At this moment, we set the degree as the number of divison of the Catmull Rom method, this is not
        # TODO: correct and whe should change this to fit with each DCC method

        :param cv:
        :param degree:
        :param periodic:
        :return:
        """

        from tpRigToolkit.libs.controlrig.core import controldata

        pts = []
        points_length = len(cv)

        # mapping the division's steps
        div_map = [j / float(deg) for j in range(deg)]
        for i in range(0, points_length + 1):
            if (i < 0 or (i - deg) > points_length) and periodic:
                continue
            if (i <= 0 or (i + deg) > points_length) and not periodic:
                continue
            p0 = controldata.ControlV(cv[i - 1])
            p1 = controldata.ControlV(cv[i if i < points_length else (i - points_length)])
            p2 = controldata.ControlV(cv[(i + 1) if (i + 1) < points_length else (i + 1 - points_length)])
            p3 = controldata.ControlV(cv[(i + 2) if (i + 2) < points_length else (i + 2 - points_length)])

            # CUBIC       spline smoothing #
            # a = p3 - p2 - p0 + p1
            # b = p0 - p1 - a
            # c = p2 - p0
            # d = p1
            # for j in range(deg):
            #     t = j / float(deg)
            #     t2 = t**2
            #     pos = a*t*t2 + b*t2 + c*t + d

            # CATMULL ROM   spline smoothing #

            a = .5 * (p1 * 2)
            b = .5 * (p2 - p0)
            c = .5 * (2 * p0 - 5 * p1 + 4 * p2 - p3)
            d = .5 * (-1 * p0 + 3 * p1 - 3 * p2 + p3)

            for j, t in enumerate(div_map):
                pos = a + (b * t) + (c * t * t) + (d * t * t * t)
                pts.append(pos)

        return pts

    def _draw_grid(self, painter):
        """
        Draw the grid of the viewport, displaying the main axis
        :param painter:
        :return:
        """

        from tpRigToolkit.libs.controlrig.core import controldata

        if self._draw_axis:
            parent_main_axis = self._rotate_order
            for x in range(3):
                self._axis_pen[x].setWidthF(0.5)
            self._axis_pen[controldata.axis_eq[parent_main_axis[0]]].setWidthF(1.5)
            painter.setPen(self._axis_pen[0])
            painter.drawLine(self._convert_3D_to_2D(0, 0, 0), self._convert_3D_to_2D(100, 0, 0))
            painter.setPen(self._sub_grid_pen)
            step = self._ref if self._ref > 0.3 else (5 * self._ref if self._ref > 0.05 else 50 * self._ref)
            rows = int(10 * (1 / step) * 0.75)

            for i in range(-rows, rows):
                painter.drawLine(self._convert_3D_to_2D(-100, 0, i * step), self._convert_3D_to_2D(100, 0, i * step))
                painter.drawLine(self._convert_3D_to_2D(i * step, 0, -100), self._convert_3D_to_2D(i * step, 0, 100))

            painter.setPen(self._axis_pen[1])
            painter.drawLine(self._convert_3D_to_2D(0, 0, 0), self._convert_3D_to_2D(0, 100, 0))
            painter.setPen(self._axis_pen[2])
            painter.drawLine(self._convert_3D_to_2D(0, 0, 0), self._convert_3D_to_2D(0, 0, 100))

        if self._draw_ref:
            painter.setPen(QPen(QColor(125, 165, 185), 0.8))
            sp = [[0.0, 0.0, 1.0], [-0.5, 0.0, 0.87], [-0.87, 0.0, 0.5], [-1.0, 0.0, 0.0], [-0.87, 0.0, -0.5],
                  [-0.5, 0.0, -0.87], [0.0, 0.0, -1.0], [0.5, 0.0, -0.87], [0.87, 0.0, -0.5], [1.0, 0.0, 0.0],
                  [0.87, 0.0, 0.5], [0.5, 0.0, 0.87], [0.0, 0.0, 1.0], [0.0, 0.7, 0.7], [0.0, 1.0, 0.0],
                  [0.0, 0.7, -0.7], [0.0, 0.0, -1.0], [0.0, -0.7, -0.7], [0.0, -1.0, 0.0], [-0.5, -0.87, 0.0],
                  [-0.87, -0.5, 0.0], [-1.0, 0.0, 0.0], [-0.87, 0.5, 0.0], [-0.5, 0.87, 0.0], [0.0, 1.0, 0.0],
                  [0.5, 0.87, 0.0], [0.87, 0.5, 0.0], [1.0, 0.0, 0.0], [0.87, -0.5, 0.0], [0.5, -0.87, 0.0],
                  [0.0, -1.0, 0.0], [0.0, -0.7, 0.7], [0.0, 0.0, 1.0]]
            for i, p in enumerate(sp[:-1]):
                s, e = controldata.ControlV(p), controldata.ControlV(sp[i + 1])
                s *= self._ref * 0.5
                e *= self._ref * 0.5

                painter.drawLine(self._convert_3D_to_2D(*s), self._convert_3D_to_2D(*e))

        if self._shapes:
            height = 40
            info = 'degree%s : %i' % ('s' if self._shapes[0].degree > 1 else '', self._shapes[0].degree)
            info += '\nclosed : %s' % ('no', 'yes')[bool(self._shapes[0].periodic)]
            if len(self._shapes) > 1:
                info += '\nshapes : %i' % len(self._shapes)
                height += 20
            self._infos.setText(info)
            self._infos.setFixedHeight(height)
            self._infos.setGeometry(10, self.height() - height, self.width(), self._infos.height())

    def _on_toggle_ref(self, state):
        self._draw_ref = state
        self.repaint()

    def _on_toggle_axis(self, state):
        self._draw_axis = state
        self.repaint()
