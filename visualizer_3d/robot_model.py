from PyQt5.QtGui import QMatrix4x4

from urdfpy import URDF
import pyqtgraph.opengl as gl

import os

class RobotLink(gl.GLGraphicsItem.GLGraphicsItem):
    def __init__(self, link_info):
        gl.GLGraphicsItem.GLGraphicsItem.__init__(self)

        print(f"Created link: {link_info.name}")

        self.name = link_info.name
        self.parent_joint = None
        self._static_transform = QMatrix4x4()

        self.visuals = []
        for visual in link_info.visuals:
            for mesh in visual.geometry.meshes:
                mesh_data = gl.MeshData(vertexes=mesh.vertices, faces=mesh.faces)
                mesh = gl.GLMeshItem(meshdata=mesh_data, drawEdges=True)
                mesh.setTransform(visual.origin)
                mesh.setParentItem(self)
                self.visuals.append(mesh)

    def setParentJoint(self, joint):
        #print(f"Type: {joint.joint_type}, axis: {joint.axis}\norigin: {joint.origin}")
        self._type = joint.joint_type
        self._axis = joint.axis
        self._limit = joint.limit
        self._static_transform = QMatrix4x4(*joint.origin.ravel())
        #print(self._static_transform)
        self.setTransform(self._static_transform)

    def setJointQ(self, q):
        print(f"Setting {self.name} to {q}")
        clamp = lambda x: max(self._limit.lower, min(x, self._limit.upper))
        j_transform = QMatrix4x4()
        if self._type == 'prismatic':
            j_transform.translate(*(clamp(q) * self._axis))
        elif self._type == 'revolute':
            j_transform.rotate(clamp(q), *self._axis)
        elif self._type == 'continuous':
            j_transform.rotate(q, *self._axis)
        else:
            print(f"Unsupported joint type - '{self._type}'")

        self.setTransform(self._static_transform * j_transform)
        self.update()

class RobotModel(gl.GLGraphicsItem.GLGraphicsItem):
    def __init__(self, urdf_file):
        gl.GLGraphicsItem.GLGraphicsItem.__init__(self)

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
            # Store the child link in the joint map
            self.joints[joint.name] = joint.child

        self.links[robot_info.base_link.name].setParentItem(self)

        #for n, l in self.links.items():
        #    print(f"{n} - parent: {l.parentItem()}, children: {l.childItems()}")

    def setJointQ(self, joint, q):
        if joint in self.joints:
            print(f"Setting {joint} to {q}")
            self.links[self.joints[joint]].setJointQ(q)
        else:
            print(f"Invalid joint name: '{joint}'")

    def setJointQs(self, qs):
        if len(qs) != len(self.joints):
            print(f"Error, supplied joint length doesn't match actual joint length ({len(qs)} != {len(self.joints)})")
            return

        for i, q in enumerate(qs):
            self.links[i+1].setJointQ(q)

