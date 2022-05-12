from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from pyqtgraph.opengl import GLViewWidget
import pyqtgraph.opengl as gl

import os
import numpy as np
from scipy.spatial.transform import Rotation

_DIR_ = ("x", "y", "z")
_QUAT_ = ("qx", "qy", "qz", "qw")

class VisualizerWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        main_layout = QVBoxLayout()

        self._3d_viz = Visualizer3DWidget(parent=self)
        main_layout.addWidget(self._3d_viz)

        self.setLayout(main_layout)

    def addAxis(self, *args, **kwargs):
        self._3d_viz.addAxis(*args, **kwargs)

# Shape helpers:
def _createArrow(color=(1., 1., 1., 1.), width=2, pos=[0, 0, 0], vec=[0, 0, 0]):
    # Not much of an arrow at the moment, but it will have to do for now.
    pos = np.array(pos)
    vec = pos + np.array(vec)
    data = np.zeros((2, 3))
    data[0,:] = pos
    data[1,:] = vec
    arrow = gl.GLLinePlotItem(pos=data, color=color, width=width, glOptions='opaque')
    return arrow

def _createSphere(radius=0.05, color=(1., 0, 0, 1.), draw_faces=True, draw_edges=False):
    sphere = gl.MeshData.sphere(rows=10, cols=10, radius=radius)
    mesh = gl.GLMeshItem(meshdata=sphere, smooth=True,
                         drawFaces=draw_faces, color=color,
                         drawEdges=draw_edges, edgeColor=color)
    return mesh


class Visualizer3DWidget(GLViewWidget):
    def __init__(self, parent=None):
        GLViewWidget.__init__(self, parent=parent)

        self.setMinimumSize(320, 240)
        self.resize(640, 480)

        self.setBackgroundColor((200, 200, 200, 255))

        self._base_pos = np.zeros(len(_DIR_))
        self._wRb = np.zeros(len(_QUAT_))

        self.setCameraPosition(distance=1.0)

        # First, we need to draw the ground plane:
        grid = gl.GLGridItem()
        # grid.scale(1, 1, 1)
        #grid.setColor((0, 0, 255, 128))

        self.addItem(grid)

        self._axes = []
        
        self.base_triad = self.addAxis()

        self.addAxis(translation=[0,0,0.1])
        self.addAxis(translation=[0.3, 0, 0.2], quaternion=[0.707, 0, 0, 0.707])



    def addAxis(self, *args, **kwargs):
        size = kwargs.get('size', 0.1)
        position = kwargs.get("translation", [0, 0, 0])

        if len(position) != 3:
            print(f"Invalid position. Must contain 3 elements: '{position}'")
            return None

        R = Rotation.identity()
        try:
            rot_type = None
            rot_val = None
            if 'quaternion' in kwargs:
                rot_type = "quaternion"
                rot_val = kwargs[rot_type]
                try:
                    R = Rotation.from_quat(rot_val)
                except:
                    R = Rotation.from_quat([rot_val[i] for i in _QUAT_])
            elif 'axis_angle' in kwargs:
                rot_type = "axis_angle"
                rot_val = kwargs[rot_type]
                R = Rotation.from_rotvec(rot_val)
            elif 'rotation_matrix' in kwargs:
                rot_type = "rotation_matrix"
                rot_val = kwargs[rot_type]
                R = Rotation.from_matrix(rot_val)
        except:
            print(f"Invalid rotation of type '{rot_type}' with value: '{rot_val}'")
            return None

        new_triad = gl.GLAxisItem(glOptions='opaque')            
        new_triad.setSize(x=size, y=size, z=size)

        new_triad.resetTransform()

        # GLAxisItem expects an axis/angle representation
        ax_ang = R.as_rotvec()
        ang = np.linalg.norm(ax_ang) * 180 / np.pi
        try:
            axis = ax_ang / np.linalg.norm(ax_ang)
        except Exception as ex:
            print(ex)
            axis = np.array([0, 0, 1])

        new_triad.rotate(ang, *axis)
        new_triad.translate(*position)
        
        self._axes.append(new_triad)
        self.addItem(new_triad)

        return new_triad
        
    def updateAxisFrame(self, axis):
        # Get base to world transform:
        wRb = Rotation.from_quat(self._wRb)

        self.base_triad.resetTransform()
        ax_ang = wRb.as_rotvec()
        ang = np.linalg.norm(ax_ang) * 180 / np.pi
        try:
            axis = ax_ang / np.linalg.norm(ax_ang)
        except Exception as ex:
            print(ex)
            axis = np.array([0, 0, 1])
        self.base_triad.rotate(ang, *axis)
        self.base_triad.translate(*self._base_pos)

