from PyQt5.QtGui import QMatrix4x4

from urdfpy import URDF
import pyqtgraph.opengl as gl

import os

class RobotLink(gl.GLGraphicsItem.GLGraphicsItem):
    def __init__(self, link_info):
        gl.GLGraphicsItem.GLGraphicsItem.__init__(self)
        
        print(f"Created link: {link_info.name}")
        
        self.parent_joint = None
        self._static_transform = QMatrix4x4()
        
        self.visuals = []
        for visual in link_info.visuals:
            for mesh in visual.geometry.meshes:
                mesh_data = gl.MeshData(vertexes=mesh.vertices, faces=mesh.faces)
                mesh = gl.GLMeshItem(meshdata=mesh_data, drawEdges=True)
                mesh.setParentItem(self)
                self.visuals.append(mesh)

    def setParentJoint(self, joint):
        #print(f"Type: {joint.joint_type}, axis: {joint.axis}\norigin: {joint.origin}")
        self._static_transform = QMatrix4x4(*joint.origin.ravel())
        #print(self._static_transform)
        self.setTransform(self._static_transform)

class RobotModel(gl.GLGraphicsItem.GLGraphicsItem):
    def __init__(self, urdf_file):
        gl.GLGraphicsItem.GLGraphicsItem.__init__(self)

        print(f"Creating model from {os.path.basename(urdf_file)}")
        robot_info = URDF.load(urdf_file)
        
        links = {}
        for link in robot_info.links:
            links[link.name] = RobotLink(link)

        for joint in robot_info.joints:
            print(f"Connected {joint.child} to {joint.parent}")
            links[joint.child].setParentJoint(joint)
            links[joint.child].setParentItem(links[joint.parent])

        links[robot_info.base_link.name].setParentItem(self)
