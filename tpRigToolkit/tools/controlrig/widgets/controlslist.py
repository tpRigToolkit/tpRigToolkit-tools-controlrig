#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains control viewer widget for tpRigToolkit.tools.controlrig
"""

from __future__ import print_function, division, absolute_import

import json

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpDcc.libs.qt.widgets import lists


class ControlsList(lists.EditableList, object):
    def __init__(self, controls_path=None, parent=None):
        super(ControlsList, self).__init__(parent=parent)

        self._controls_path = controls_path
        self._drag = None
        self._drag_start_pos = None
        self._drag_start_index = None

        self.setHeaderHidden(True)
        self.setSortingEnabled(True)
        self.setMouseTracking(True)
        self.setRootIsDecorated(False)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.sortByColumn(0, Qt.AscendingOrder)
        self.setUniformRowHeights(True)
        self.setAlternatingRowColors(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setStyleSheet(
            '''
            QTreeView{alternate-background-color: #3b3b3b;}
            QTreeView::item {padding:3px;}
            QTreeView::item:!selected:hover {
                background-color: #5b5b5b;
                margin-left:-3px;
                border-left:0px;
            }
            QTreeView::item:selected {
                background-color: #48546a;
                border-left:2px solid #6f93cf;
                padding-left:2px;
            }
            QTreeView::item:selected:hover {
                background-color: #586c7a;
                border-left:2px solid #6f93cf;
                padding-left:2px;
            }
            '''
        )

    @property
    def controls_path(self):
        return self._controls_path

    @controls_path.setter
    def controls_path(self, path):
        self._controls_path = path

    def startDrag(self, event):
        item = self.currentItem()
        if not item:
            return

        mime_data = QMimeData()
        mime_data.setText(json.dumps({'controls_path': self._controls_path, 'control': item.control.name}))
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec_()
