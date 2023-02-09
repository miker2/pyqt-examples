from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMatrix4x4
from PyQt5.QtWidgets import QHBoxLayout, QComboBox, QSlider

from urdfpy import URDF
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import numpy as np

import math
import os

import utils

import trimesh


__LEAD_DENSITY__=11340  # kg / m^3
__DEFAULT_GL_OPT__='translucent'

class RobotLink(gl.GLGraphicsItem.GLGraphicsItem):
    def __init__(self, link_info):
        gl.GLGraphicsItem.GLGraphicsItem.__init__(self)

        self.setGLOptions(__DEFAULT_GL_OPT__)

        print(f"Created link: {link_info.name}")

        self.name = link_info.name
        self.parent_joint = None
        self._static_transform = QMatrix4x4()
        self._pos = 0

        self.visuals = []
        for visual in link_info.visuals:
            color = [0.7, 0.7, 0.7, 1.0]
            opt='opaque'
            if visual.material is not None and visual.material.color is not None:
                color = visual.material.color
                if color[-1] < 1:
                    opt='translucent'
            edge_color = 0.8 * np.array(color)  # Make the edge colors slightly darker than the face colors
            for mesh in visual.geometry.meshes:
                mesh_data = gl.MeshData(vertexes=mesh.vertices, faces=mesh.faces)
                mesh = gl.GLMeshItem(meshdata=mesh_data, drawEdges=True, color=color, edgeColor=edge_color, \
                                     glOptions='translucent') #, shader='shaded')
                mesh.setGLOptions(__DEFAULT_GL_OPT__)
                mesh.setTransform(visual.origin)
                mesh.setParentItem(self)
                self.visuals.append(mesh)

        self.collisions = []
        for collision in link_info.collisions:
            print(collision.name, collision.origin, collision.geometry)
            color = [0.0, 0.5, 0.0, 0.8]
            opt='translucent'
            edge_color = 0.8 * np.array(color)
            # hacky workaround for urdfpy bug related to cylinders
            print(f"box: {visual.geometry.box}, cylinder: {visual.geometry.cylinder}")

            if collision.geometry.cylinder is not None and collision.geometry.cylinder._meshes is None:
                print("Trying to work around bug!")
                collision.geometry.cylinder._meshes = []
                collision.geometry.cylinder._mesh = [trimesh.creation.cylinder(
                  radius=collision.geometry.cylinder.radius,
                  height=collision.geometry.cylinder.length
                )]

            for mesh in collision.geometry.meshes:
                mesh_data = gl.MeshData(vertexes=mesh.vertices, faces=mesh.faces)
                mesh = gl.GLMeshItem(meshdata=mesh_data, drawEdges=True, color=color, edgeColor=edge_color, \
                                     glOptions='translucent') #, shader='shaded')
                mesh.setGLOptions(__DEFAULT_GL_OPT__)
                mesh.setTransform(collision.origin)
                mesh.setParentItem(self)
                self.collisions.append(mesh)

        # Add a sphere representing the mass of the link (at the CoM location)
        # The sphere radius is determined using a representative sphere with the density of lead
        lead_volume = link_info.inertial.mass / __LEAD_DENSITY__
        lead_radius = (lead_volume * 3 / 4 / math.pi) ** (1/3)
        self.com = utils.createSphere(radius=lead_radius, color=(0., 0., 1., 0.9))
        self.com.setParentItem(self)
        self.com.setTransform(link_info.inertial.origin)
        self.com.setGLOptions(__DEFAULT_GL_OPT__)
        self.com.setDepthValue(-20)

        # Add an ellipsoid representing the inertia of the link (at the CoM location)
        # First, we must compute the principle axes and principle moments of inertia of the
        # inertia tensor
        I_principal, I_axes = np.linalg.eig(link_info.inertial.inertia)

        self.inertia = utils.createSphere(radius=1, color=(1., 0, 0, 0.6))
        self.inertia.setParentItem(self)
        self.inertia.setTransform(link_info.inertial.origin)
        ellipsoid_inertia = math.sqrt(10 / link_info.inertial.mass) * np.sqrt(
            np.array([-I_principal[0] + I_principal[1] + I_principal[2],
                       I_principal[0] - I_principal[1] + I_principal[2],
                       I_principal[0] + I_principal[1] - I_principal[2]])) / 2
        self.inertia.scale(*ellipsoid_inertia)
        R = np.eye(4)
        R[:3,:3] = I_axes.T
        #self.inertia.applyTransform(pg.Transform3D(*R.ravel()), False)
        self.inertia.setGLOptions(__DEFAULT_GL_OPT__)

        self.axis = utils.createAxis(size=0.2)
        self.axis.setParentItem(self)

    def setParentJoint(self, joint):
        #print(f"Type: {joint.joint_type}, axis: {joint.axis}\norigin: {joint.origin}")
        self._type = joint.joint_type
        self._axis = joint.axis
        self._limit = joint.limit
        self._static_transform = QMatrix4x4(*joint.origin.ravel())
        #print(self._static_transform)
        self.setTransform(self._static_transform)

    @property
    def pos(self):
        return self._pos

    @property
    def limits(self):
        return self._limit

    def setJointQ(self, q):
        print(f"Setting {self.name} to {q}")
        self._pos = q
        self.setTransform(self._static_transform)
        clamp = lambda x: max(self._limit.lower, min(x, self._limit.upper))
        j_transform = QMatrix4x4()
        if self._type == 'prismatic':
            j_transform.translate(*(clamp(q) * self._axis))
        elif self._type == 'revolute':
            j_transform.rotate(clamp(q)*180/math.pi, *self._axis)
        elif self._type == 'continuous':
            j_transform.rotate(q*180/math.pi, *self._axis)
        else:
            print(f"Unsupported joint type - '{self._type}'")

        self.applyTransform(j_transform, local=True)

    def hideObj(self, name):
        obj = getattr(self, name)
        if obj:
            try:
                obj.hide()
            except AttributeError:
                for o in obj:
                    o.hide()
        else:
            print(f"Object attribute '{name}' not valid!")

    def showObj(self, name):
        obj = getattr(self, name)
        if obj:
            try:
                obj.show()
            except AttributeError:
                for o in obj:
                    o.show()
        else:
            print(f"Object attribute '{name}' not valid!")

class RobotModel(gl.GLGraphicsItem.GLGraphicsItem):

    joint_moved = pyqtSignal()

    def __init__(self, urdf_file):
        gl.GLGraphicsItem.GLGraphicsItem.__init__(self)

        # Create the layout here that will be used to hold the controls. This may be unused.
        self._layout = QHBoxLayout()

        print(f"Creating model from {os.path.basename(urdf_file)}")
        robot_info = URDF.load(urdf_file)

        self.links = {}
        for link in robot_info.links:
            self.links[link.name] = RobotLink(link)

        # A mapping of joint to child link names
        self.joints = {}
        for joint in robot_info.joints:
            print(f"Connected {joint.child} to {joint.parent}")
            self.links[joint.child].setParentJoint(joint)
            self.links[joint.child].setParentItem(self.links[joint.parent])
            if joint.joint_type == "fixed":
                continue
            # Store the child link in the joint map
            self.joints[joint.name] = joint.child

        self.links[robot_info.base_link.name].setParentItem(self)

        #for n, l in self.links.items():
        #    print(f"{n} - parent: {l.parentItem()}, children: {l.childItems()}")

        # Here we'll create our widgets for modifying the robot configuration. The user will have to
        # place these widgets in a GUI if desired.
        self._joint_selector = QComboBox()
        for jnt in self.joints.keys():
            self._joint_selector.addItem(jnt)
        self._joint_selector.currentIndexChanged.connect(self.jointChanged)
        self._joint_pos = QSlider(Qt.Horizontal)
        self._joint_pos.setMinimum(-314)
        self._joint_pos.setMaximum(314)
        self._joint_pos.valueChanged.connect(self.setJointQFromSlider)
        self._layout.addWidget(self._joint_selector)
        self._layout.addWidget(self._joint_pos)

    def setJointQ(self, joint, q):
        if joint in self.joints:
            #print(f"Setting {joint} to {q}")
            self.links[self.joints[joint]].setJointQ(q)
            self.joint_moved.emit()
        else:
            print(f"Invalid joint name: '{joint}'")

    def setJointQs(self, qs):
        if len(qs) != len(self.joints):
            print(f"Error, supplied joint length doesn't match actual joint length ({len(qs)} != {len(self.joints)})")
            return

        for i, q in enumerate(qs):
            self.links[i+1].setJointQ(q)

    def jointChanged(self, idx):
        # Map the index to a name:
        jnt_name = self._joint_selector.itemText(idx)
        link_name = self.joints[jnt_name]
        jnt_limits = self.links[link_name].limits
        self._joint_pos.setMaximum(int(jnt_limits.upper * 100))
        self._joint_pos.setMinimum(int(jnt_limits.lower * 100))
        self._joint_pos.setValue(int(self.links[link_name].pos * 100))

    def setJointQFromSlider(self, value):
        angle = value / 100.
        jnt_name = self._joint_selector.currentText()
        self.setJointQ(jnt_name, angle)
        self.update()

    def hideObj(self, obj):
        for name, link in self.links.items():
            link.hideObj(obj)
        self.update()

    def showObj(self, obj):
        for name, link in self.links.items():
            link.showObj(obj)
        self.update()


class RobotObjProxy:
    def __init__(self, robot, attr):
        self._robot = robot
        self._attr = attr

    def show(self):
        self._robot.showObj(self._attr)

    def hide(self):
        self._robot.hideObj(self._attr)

