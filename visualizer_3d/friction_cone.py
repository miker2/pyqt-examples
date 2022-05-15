from PyQt5.QtGui import QMatrix4x4

import numpy as np
from scipy.spatial.transform import Rotation

import pyqtgraph.opengl as gl

class FrictionCone(gl.GLGraphicsItem.GLGraphicsItem):
    def __init__(self, **kwargs):
        gl.GLGraphicsItem.GLGraphicsItem.__init__(self)

        # Default options
        self.opts = {
            'sides' : 8,
            'mu' : 1,
            'height' : 0.25,
            'drawFaces' : True,
            'color' : (1., 0., 0., 0.5),
            'drawEdges' : True,
            'edgeColor' : (0., 0., 0., 1.),
            'glOptions' : 'translucent'  # 'additive'
        }

        self._pos = None
        self._rot = None
        
        self.opts.update(kwargs)
        height = self.opts.pop('height')
        sides = self.opts.pop('sides')
        self._mu = self.opts.pop('mu')

        # Create the friction cone data. The base data will be a cone with unit friction (i.e. mu=1)
        cone = gl.MeshData.cylinder(1, sides, radius=[0, height], length=height, offset=False)
        
        mesh = gl.GLMeshItem(meshdata=cone, **self.opts)
        mesh.setParentItem(self)
        self.hide()  # Start hidden until the user asks for it.

    def setMu(self, mu):
        self._mu = mu
        self._updateTransform()

    def setNormal(self, normal):
        ## With the normal set, we can compute the orientation of the cone:
        z_axis = np.array([0, 0, 1])
        
        # First we need the angle between the vertical axis and the normal vector:
        axis = np.cross(z_axis, normal)
        
        # Now, calculate the angle between these two vectors using:
        #  θ = sin-1 [ |a × b| / (|a| |b|) ]
        ang = np.arcsin( np.linalg.norm(axis) / (np.linalg.norm(z_axis) * np.linalg.norm(normal)) )

        self._rot = { 'ang': ang, 'axis': axis }
        self._updateTransform()

    def setFootPosition(self, pos):
        self._pos = pos
        self._updateTransform()

    def _updateTransform(self):
        # Ensure that both a position and rotation exist before applying any transform.
        if self._pos is not None and self._rot is not None:
            transform = QMatrix4x4()
            transform.translate(*self._pos)
            transform.rotate(self._rot['ang'] * 180/np.pi, *self._rot['axis'])
            transform.scale(self._mu, self._mu, 1)
            self.setTransform(transform)
        
