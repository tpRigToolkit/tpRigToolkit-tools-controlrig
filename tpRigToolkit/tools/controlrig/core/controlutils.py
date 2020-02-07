#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utility functions related with tpRigToolkit.tools.controlrig
"""

from __future__ import print_function, division, absolute_import

import tpDccLib as tp

if tp.is_maya():
    import tpMayaLib as maya


def getpos(node, x=False, v=True):
    """
    Get the absolute object's position, shorter than typing the whole xform
    :param node: object we want to get the position
    :param x: force xform
    :param v: force boundingBox
    :return: object position
    """

    if not tp.is_maya():
        return

    if (maya.cmds.ls(node, showType=True)[1] in ('joint', 'locator') or x) and v:
        r = maya.cmds.xform(node, query=True, t=True, ws=True)
    else:
        r = [maya.cmds.getAttr(node + '.boundingBoxCenter' + a) for a in 'XYZ']

    return r


def snap(master, slave, pos=True, rot=True, t=True, r=True, clear=True, c=True):
    """
    Snaps an object to another
    :param master: reference objec t
    :param slave: objecth which whill be aligned
    :param pos: bool, align position
    :param rot: bool, align rotations
    :param t:
    :param r:
    :param clear: if you want to keep the constraints after evaluation, set to False
    :param c:
    :return:
    """

    if not tp.is_maya():
        return

    r, t, c = rot and r, pos and t, clear and c
    cons = list()
    if t:
        cons.append(maya.cmds.pointConstraint(master, slave, w=True)[0])
    if r:
        cons.append(maya.cmds.orientConstraint(master, slave, w=1)[0])
    if c:
        maya.cmds.delete(cons)


def shape_to_transform(shapes=None, transforms=None):
    """
    Parent n shapes directly to n transforms
    :param shapes: list of shape's transforms
    :param transforms: list of transforms
    """

    if not tp.is_maya():
        return

    if shapes is None:
        shapes = list()

    if transforms is None:
        transforms = list()

    shapes = shapes if isinstance(shapes, list) else [shapes]
    transforms = transforms if isinstance(transforms, list) else [transforms]

    assert len(shapes) == len(transforms)

    for s, t in zip(shapes, transforms):
        shape = maya.cmds.listRelatives(s, c=True, s=True, ni=True, f=True)
        maya.cmds.parent(shape, t, s=True, add=True)
        if len(shape) == 1:
            maya.cmds.rename(shape, t + 'Shape')
        else:
            for i, shp in enumerate(shape):
                maya.cmds.rename(shp, '%s_Shape_%02d' % (t, i))

        # Delete old shape's transform
        maya.cmds.delete(s)
