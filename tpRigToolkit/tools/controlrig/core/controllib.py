#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with ControlLib
"""

from __future__ import print_function, division, absolute_import

import os
import logging
from copy import copy

from Qt.QtGui import *

import tpDccLib as tp
from tpPyUtils import jsonio, yamlio

from tpRigToolkit.tools.controlrig.core import controldata, controlutils

# TODO: We need to remove all dependencies from Maya
if tp.is_maya():
    import tpMayaLib as maya
    from tpMayaLib.core import transform as xform_utils, shape as shape_utils


LOGGER = logging.getLogger()


class ControlLib(object):

    DEFAULT_DATA = {
        'controls': {
            'circle': [{"cvs": [(0.0, 0.7, -0.7), (0.0, 0.0, -1.0), (0.0, -0.7, -0.7), (0.0, -1.0, 0.0),
                                (0.0, -0.7, 0.7), (0.0, 0.0, 1.0), (0.0, 0.7, 0.7), (0.0, 1.0, 0.0)],
                        "degree": 3,
                        "periodic": 1}],
            'cross': [{"cvs": [(0.0, 0.5, -0.5), (0.0, 1.0, -0.5), (0.0, 1.0, 0.5), (0.0, 0.5, 0.5),
                               (0.0, 0.5, 1.0), (0.0, -0.5, 1.0), (0.0, -0.5, 0.5), (0.0, -1.0, 0.5),
                                (0.0, -1.0, -0.5), (0.0, -0.5, -0.5), (0.0, -0.5, -1.0), (0.0, 0.5, -1.0),
                                (0.0, 0.5, -0.5)],
                       "degree": 1,
                       "periodic": 1}],
            'cube': [{"cvs": [(-1.0, -1.0, 1.0), (-1.0, 1.0, 1.0), (-1.0, 1.0, -1.0), (-1.0, -1.0, -1.0),
                                (-1.0, -1.0, 1.0), (1.0, -1.0, 1.0), (1.0, -1.0, -1.0), (1.0, 1.0, -1.0),
                                (1.0, 1.0, 1.0), (1.0, -1.0, 1.0), (1.0, 1.0, 1.0), (-1.0, 1.0, 1.0),
                                (-1.0, 1.0, -1.0), (1.0, 1.0, -1.0), (1.0, -1.0, -1.0), (-1.0, -1.0, -1.0)],
                        "degree": 1,
                      "periodic": 1}]
                },
                'categories': []
            }

    def __init__(self):
        self._controls_file = None
        self._parser_format = 'json'

    @property
    def controls_file(self):
        return self._controls_file

    @controls_file.setter
    def controls_file(self, controls_file_path):
        self._controls_file = controls_file_path

    def has_valid_controls_file(self):
        """
        Returns whether controls file is valid or not
        :return: bool
        """

        return self._controls_file and os.path.isfile(self._controls_file)

    def load_control_data(self):
        """
        Function that initializes controls data file
        """

        controls = controldata.ControlPool()

        new_controls_file = False
        if not self.has_valid_controls_file():
            try:
                f = open(self._controls_file, 'w')
                f.close()
            except Exception:
                pass

        if not self.has_valid_controls_file():
            LOGGER.warning('Impossible to initialize controls data because controls file "{}" does not exists!'.format(
                self._controls_file
            ))
            return None

        if self._parser_format == 'yaml':
            data = yamlio.read_file(self._controls_file)
        else:
            data = jsonio.read_file(self._controls_file)
        if not data:
            data = self.DEFAULT_DATA
            if self._parser_format == 'yaml':
                yamlio.write_to_file(data, self._controls_file)
            else:
                jsonio.write_to_file(data, self._controls_file)
            new_controls_file = True

        data_controls = data.get('controls')
        if not data_controls:
            LOGGER.warning('No controsl found in current controls data!')
            return None

        for ctrl in data_controls:
            new_ctrl = controldata.ControlData(name=ctrl, ctrl_data=data_controls[ctrl])
            controls.add(new_ctrl)

        if new_controls_file:
            self.save_control_data(control_pool=controls)

        return controls

    def save_control_data(self, control_pool):
        """
        Stores the controls data to the controls data file (overwriting existing data)
        """

        control_data_dict = dict()

        if self._parser_format == 'yaml':
            current_data = yamlio.read_file(self._controls_file)
        else:
            current_data = jsonio.read_file(self._controls_file)

        control_data_dict['controls'] = control_pool()
        control_data_dict['categories'] = current_data['categories'] if current_data is not None else list()
        if self._parser_format == 'yaml':
            yamlio.write_to_file(control_data_dict, self._controls_file)
        else:
            jsonio.write_to_file(control_data_dict, self._controls_file)

    def get_controls(self):
        """
        Returns all available controls
        :return: list
        """

        return self.load_control_data()

    def add_control(self, control_name, curve_info):
        """
        Adds a new control to the list of controls
        :param control_name: str, name of the control we want to add
        :param curve_info: dict, dictionary with proper data curve
        :return:
        """

        control_pool = self.load_control_data()
        if control_name in control_pool:
            LOGGER.warning('Control "{}" already exists in Control File. Aborting adding control operation ...')
            return

        new_ctrl = controldata.ControlData(
            name=control_name,
            ctrl_data=curve_info
        )
        if not new_ctrl:
            LOGGER.error(
                'Control Data for "{}" curve was not created properly! Aborting control add operation ...'.format(
                    control_name))
            return

        control_pool.add(new_ctrl)
        self.save_control_data(control_pool)

        return new_ctrl

    def rename_control(self, old_name, new_name):
        """
        Renames control with given new wame
        :param old_name: str, name of the control we want to rename
        :param new_name: str, new name of the control
        """

        control_pool = self.load_control_data()
        if old_name not in control_pool:
            LOGGER.warning(
                'Control "{}" is not stored in Control File. Aborting renaming control operation ...'.format(old_name))
            return False

        if new_name in control_pool:
            LOGGER.warning(
                'New Control name "{}" is already stored in Control File. Aborting renaming control operation ...'.format(
                    new_name))
            return False

        control_pool[old_name].name = new_name
        self.save_control_data(control_pool)

        return True

    def delete_control(self, control_name):
        """
        Removes control with given control_name from the controls data file
        :param control_name:
        :return:
        """

        control_pool = self.load_control_data()
        if control_name not in control_pool:
            LOGGER.warning(
                'Control "{}" is not stored in Control File. Aborting deleting control operation ...')
            return

        control_pool.remove(control_name)
        self.save_control_data(control_pool)

    @staticmethod
    def create_control(shape_data, target_object=None, name='new_ctrl', size=1, offset=(0, 0, 0), ori=(1, 1, 1),
                       axis_order='XYZ', mirror=None, shape_parent=False, parent=None, color=None):
        """
        Creates a new control
        :param shape_data: str, shape name from the dictionary
        :param target_object: str, object(s) on which we will create the control
        :param name: str, name of the curve
        :param size: float, global size of the control
        :param offset: tuple<float>, X, Y or Z offset around the object
        :param ori: tuple<float>, X, Y or Z multiply of the shape
        :param axis order: str, 'XYZ' will take X as main axis, etc
        :param axis mirror: str, axis of mirror or None if no wanted mirror
        :param shape_parent, bool, True will parent the shape to the target object
        :return: parent: str, parent of the curve
        """

        if not tp.is_maya():
            return

        target_object = [target_object] if not isinstance(target_object, list) else target_object
        controls = list()
        orient = controldata.ControlV(ori)

        def create(name, offset=(0, 0, 0), shape_data=None):
            """
            Creates a curve an apply the appropiate transform to the shape
            :param shape_data: ControlShape, shape object of the curve
            :param name: str, name of the curve
            :param offset: tuple<float>, X, Y or Z offset around the object
            :return:
            """

            points, degree, periodic = copy(shape_data.__cvs__), shape_data.degree, shape_data.periodic
            order = [controldata.axis_eq[x] for x in axis_order]

            for i, point in enumerate(points):
                point *= size * orient.reorder(order)
                point += offset.reorder(order)
                point *= controldata.ControlV.mirror_vector()[mirror]
                points[i] = point.reorder(order)

            # Create a unique name for the controller
            i, n = 2, name
            try:
                while tp.Dcc.get_attribute_value(n, 't'):
                    n = '%s_%02d' % (name, i)
                    i += 1
            except ValueError:
                name = n

            # Make curve periodic if necessary
            if periodic and points[0] != points[-degree]:
                points.extend(points[0:degree])

            # Create the curve
            return maya.cmds.curve(n=name, d=degree, p=points, k=[i for i in range(-degree + 1, len(points))], per=periodic)

        def create_name(obj_name):
            compo_name = [name if len(name) else obj_name]
            return '_'.join(compo_name)

        if len(target_object) != 0 and target_object[0]:
            for obj in target_object:
                ctrls = list()
                ro = tp.Dcc.get_attribute_value(obj, 'ro')
                ctrl_name = create_name(obj)
                for shp in shape_data:
                    try:
                        offset_perc = [
                            maya.cmds.getAttr('%s.t%s' % (maya.cmds.listRelatives(obj, c=True, type='joint')[0], x))[0] * offset[
                                i] for i, x in enumerate('xyz')]
                    except (ValueError, TypeError):
                        offset_perc = offset
                    finally:
                        ctrl = create(shape_data=shp, name=ctrl_name, offset=controldata.ControlV(offset_perc))

                    # Realign controller and set rotation order
                    maya.cmds.setAttr('{}.t'.format(ctrl), *controlutils.getpos(obj), type='double3')
                    controlutils.snap(obj, ctrl, t=False)
                    maya.cmds.setAttr(ctrl + '.ro', ro)

                    ctrls.append(ctrl)
                controls.append(ctrls)
        else:
            controls.append(
                [create(shape_data=shp, name=create_name(name), offset=controldata.ControlV(offset)) for shp in
                 shape_data])

        # The apply last transforms
        for i, ctrls in enumerate(controls):
            ctrl = ctrls[0]
            if len(shape_data) > 1:
                for obj in ctrls[1:]:

                    # Update shape color
                    shape = maya.cmds.listRelatives(obj, s=True, ni=True, f=True)
                    if maya.cmds.attributeQuery('overrideEnabled', node=shp, exists=True):
                        maya.cmds.setAttr(shp + '.overrideEnabled', True)
                    if color:
                        if maya.cmds.attributeQuery('overrideRGBColors', node=shp, exists=True) and type(color) != int:
                            maya.cmds.setAttr(shp + '.overrideRGBColors', True)
                            if type(color) in [list, tuple]:
                                maya.cmds.setAttr(shp + '.overrideColorRGB', color[0], color[1], color[2])
                            elif isinstance(color, QColor):
                                maya.cmds.setAttr(shp + '.overrideColorRGB', *color.toTuple())
                        elif maya.cmds.attributeQuery('overrideColor', node=shp, exists=True):
                            if type(color) == int and -1 < color < 32:
                                maya.cmds.setAttr(shp + '.overrideColor', color)
                    else:
                        if name.startswith('l_') or name.endswith('_l') or '_l_' in name:
                            maya.cmds.setAttr(shp + '.overrideColor', 6)
                        elif name.startswith('r_') or name.endswith('_r') or '_r_' in name:
                            maya.cmds.setAttr(shp + '.overrideColor', 13)
                        else:
                            maya.cmds.setAttr(shp + '.overrideColor', 22)

                    # Update shape parent
                    maya.cmds.parent(shape, ctrl, s=True, add=True, relative=True)
                maya.cmds.delete(ctrls[1:])

            if parent:
                tp.Dcc.set_parent(ctrl, parent)
            elif shape_parent and len(target_object) != 0:
                pass

        return controls

    def create_control_by_name(self, ctrl_name, name='new_ctrl', size=1, offset=(0, 0, 0), ori=(1, 1, 1), axis_order='XYZ',
                               mirror=None, shape_parent=False, parent=None, color=None):
        """
        Creates a new control given its name in the library
        :param ctrl_name: str, name of the control we want to create from the library
        :return: list<str>
        """

        controls = self.get_controls() or list()

        for control in controls:
            if control.name == ctrl_name:
                return self.create_control(control.shapes, name=name, size=size, offset=offset,
                                           ori=ori, axis_order=axis_order, mirror=mirror,
                                           shape_parent=shape_parent, parent=parent, color=color)

        # If the given control is not valid we create the first one of the list of controls
        return self.create_control(controls[0].shapes)

    @staticmethod
    def validate_curve(crv):
        """
        Returns whether the given name corresponds to a valid NURBS curve
        :param crv: str, name of the curve we want to check
        :return: bool
        """

        if not tp.is_maya():
            return False

        if crv is None or not tp.Dcc.object_exists(crv):
            return False

        crv_shapes = list()
        if tp.Dcc.node_type(crv) == 'transform':
            curve_shapes = maya.cmds.listRelatives(crv, c=True, s=True)
            if curve_shapes:
                if maya.cmds.nodeType(curve_shapes[0]) == 'nurbsCurve':
                    crv_shapes = maya.cmds.listRelatives(crv, c=True, s=True)
            crv_shapes = maya.cmds.listRelatives(crv, c=True, s=True)
        elif maya.cmds.nodeType(crv) == 'nurbsCurve':
            crv_shapes = maya.cmds.listRelatives(maya.cmds.listRelatives(crv, p=True)[0], c=True, s=True)
        else:
            LOGGER.error('The object "{}" being validated is not a curve!'.format(crv))

        return crv_shapes

    @classmethod
    def get_curve_info(cls, crv, absolute_position=True, absolute_rotation=True, degree=None, periodic=False):
        """
        Returns dictionary that contains all information for rebuilding given NURBS curve
        :param crv: str, name of the curve to get info from
        :return: list<dict>
        """

        if not tp.is_maya():
            return False

        new_crv = maya.cmds.duplicate(crv, n='duplicates', renameChildren=True)

        shapes = list()
        mx = -1

        # In the first loop we get the global bounds of the selection so we can
        # normalize the CV coordinates later
        for obj in new_crv:
            if maya.cmds.listRelatives(obj, p=True, fullPath=True):
                maya.cmds.parent(obj, w=True)
            if absolute_position or absolute_rotation:
                maya.cmds.makeIdentity(obj, apply=True, t=absolute_position, r=absolute_rotation, s=True, n=False, pn=True)

            curve_shapes = cls.validate_curve(obj)
            for crv in curve_shapes:
                for i in range(maya.cmds.getAttr('{}.degree'.format(crv)) + maya.cmds.getAttr('{}.spans'.format(crv))):
                    for p in maya.cmds.xform('{}.cv[{}]'.format(crv, i), query=True, t=True, os=True):
                        if mx < abs(p):
                            mx = abs(p)

        # In this second loop, we store the normalized data of the shapes
        for obj in new_crv:
            curve_shapes = cls.validate_curve(obj)
            for crv_shape in curve_shapes:

                cvs = list()
                degs = maya.cmds.getAttr('{}.degree'.format(crv_shape))
                spans = maya.cmds.getAttr('{}.spans'.format(crv_shape))
                c = maya.cmds.getAttr('{}.f'.format(crv_shape))
                for i in range(spans + (0 if periodic else degs)):
                    cvs.append(maya.cmds.xform('{}.cv[{}]'.format(crv_shape, i), query=True, t=True, os=True))
                cvs = [[p / mx for p in pt] for pt in cvs]

                crv_shape_dict = {
                    'cvs': cvs,
                    'form': maya.cmds.getAttr('{}.form'.format(crv_shape)),
                    'degree': degree or degs,
                    'periodic': c or periodic,
                    'color': maya.cmds.getAttr('{}.overrideColor'.format(crv_shape))
                }
                shapes.append(crv_shape_dict)

        maya.cmds.delete(new_crv)

        return shapes

    @classmethod
    def set_shape(cls, crv, crv_shape_list):
        """
        Creates a new shape on the given curve
        :param crv:
        :param crv_shape_list:
        """

        if not tp.is_maya():
            return False

        crv_shapes = cls.validate_curve(crv)

        # old_color = maya.cmds.getAttr('{}.overrideColor'.format(crv_shapes[0]))

        orig_size = None
        if crv_shapes:
            bbox = xform_utils.BoundingBox(crv).get_shapes_bounding_box()
            orig_size = bbox.get_size()

        if crv_shapes:
            maya.cmds.delete(crv_shapes)

        for i, c in enumerate(crv_shape_list):
            new_shape = maya.cmds.listRelatives(c, s=True)[0]
            maya.cmds.parent(new_shape, crv, r=True, s=True)
            maya.cmds.delete(c)
            new_shape = maya.cmds.rename(new_shape, crv+'Shape'+str(i+1).zfill(2))
            maya.cmds.setAttr(new_shape+'.overrideEnabled', True)

        bbox = xform_utils.BoundingBox(crv).get_shapes_bounding_box()
        new_size = bbox.get_size()

        if orig_size and new_size:
            scale_size = orig_size/new_size
            shape_utils.scale_shapes(crv, scale_size, relative=False)

        maya.cmds.select(crv)
