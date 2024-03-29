from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout

import pyqtgraph as pg
from pyqtgraph.opengl import GLViewWidget
import pyqtgraph.opengl as gl

import os
import numpy as np
import pywavefront
from scipy.spatial.transform import Rotation
import stl
from urdfpy import URDF

from checkable_combo_box import CheckableComboBox
from friction_cone import FrictionCone
from robot_model import RobotModel, RobotObjProxy
import utils

_DIR_ = ("x", "y", "z")
_QUAT_ = ("qx", "qy", "qz", "qw")


class VisualizerWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        main_layout = QVBoxLayout()

        self._3d_viz = Visualizer3DWidget(parent=self)
        main_layout.addWidget(self._3d_viz)

        self.setLayout(main_layout)

        self._axis_cnt = 0
        self._obj_list = CheckableComboBox()
        self._obj_list.model().itemChanged.connect(self.handleCheckStateChange)
        main_layout.addWidget(self._obj_list)

        self.drawFrictionCone()

    def addAxis(self, *args, **kwargs):
        triad = self._3d_viz.addAxis(*args, **kwargs)
        self.addToObjList(f"Axis {self._axis_cnt+1}", triad)
        self._axis_cnt += 1

    def drawMesh(self, stl_file):
        mesh = self._3d_viz.drawMesh(stl_file)
        self.addToObjList(os.path.basename(stl_file), mesh)

    def drawURDF(self, urdf_file):
        print("In VisualizerWidget.drawURDF")
        robot = self._3d_viz.drawURDF(urdf_file)
        self.addToObjList(os.path.basename(urdf_file), robot)
        controls = robot._layout # Get robot joint control layout and add to UI
        self.layout().addLayout(controls)
        self.addToObjList("robot com", RobotObjProxy(robot, 'com'))
        self.addToObjList("robot inertia", RobotObjProxy(robot, 'inertia'))
        self.addToObjList("robot axes", RobotObjProxy(robot, 'axis'))
        self.addToObjList("robot collision", RobotObjProxy(robot, 'collisions'))

    def drawFrictionCone(self):
        cone = FrictionCone(sides=6)
        self._3d_viz.addItem(cone)
        cone.setFootPosition([0.3, 0.1, 0])
        cone.setNormal([0, 0.3, 0.807])
        cone.setMu(0.4)
        #cone.update()
        cone.show()
        self.addToObjList("cone", cone, False)


    def addToObjList(self, name, item, checked=True):
        self._obj_list.addItem(name, item)
        # Start off with all items checked
        self._obj_list.setItemChecked(self._obj_list.count() - 1, checked)

    def handleCheckStateChange(self, item):
        #print(f"{item.text()}: check state: {item.checkState()}")
        #print(f"data: {item.data(Qt.UserRole)}")
        if item.checkState() == Qt.Unchecked:
            item.data(Qt.UserRole).hide()
        elif item.checkState() == Qt.Checked:
            item.data(Qt.UserRole).show()

    def update(self):
        self._3d_viz.update()

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


class Visualizer3DWidget(GLViewWidget):
    def __init__(self, parent=None):
        GLViewWidget.__init__(self, parent=parent)

        self.setMinimumSize(320, 240)
        self.resize(640, 480)

        self.setBackgroundColor((200, 200, 200, 255))

        self._base_pos = np.zeros(len(_DIR_))
        self._wRb = np.zeros(len(_QUAT_))

        self.setCameraPosition(distance=1.0)

        self._colors = pg.colormap.get('CET-C2s').getLookupTable(nPts=10, mode=pg.ColorMap.FLOAT)
        self._color_idx = 0
        # First, we need to draw the ground plane:
        grid = gl.GLGridItem()
        # grid.scale(1, 1, 1)
        #grid.setColor((0, 0, 255, 128))

        self.addItem(grid)

        self._axes = []

        self.base_triad = self.addAxis()

    def drawMesh(self, stl_file):
        _, ext = os.path.splitext(stl_file)
        if ext.lower() == '.stl':
            mesh = stl.mesh.Mesh.from_file(stl_file)
            # Recenter the mesh for now.
            _, offset, _ = mesh.get_mass_properties()
            mesh.translate(-offset)
            mesh_data = gl.MeshData(vertexes=mesh.vectors)
        elif ext.lower() == '.obj':
            mesh = pywavefront.Wavefront(stl_file, collect_faces=True)
            vertices = np.array(mesh.vertices)
            faces = np.array(mesh.mesh_list[0].faces)
            #mesh_data = gl.MeshData(vertexes=vertices[faces])
            mesh_data = gl.MeshData(vertexes=vertices, faces=faces)
        else:
            print(f"Unsupported file type '{ext}' for {stl_file}")
            return

        # Add some color
        color = self._colors[self._color_idx]
        self._color_idx = (self._color_idx + 1) % len(self._colors)
        mesh_item = gl.GLMeshItem(meshdata=mesh_data, color=np.hstack((color,[0.7])),
                                  edgeColor=[0.7,0.7,0.7,1.0], drawEdges=True)

        self.addItem(mesh_item)
        return mesh_item

    def drawURDF(self, urdf_file):
        print("InVisualizer3dWidget.drawURDF")
        robot = RobotModel(urdf_file)
        self.addItem(robot)

        return robot

    def addAxis(self, *args, **kwargs):
        new_triad = utils.createAxis(args, kwargs)

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
