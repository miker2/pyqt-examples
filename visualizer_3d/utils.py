import numpy as np
from scipy.spatial.transform import Rotation

import pyqtgraph.opengl as gl

def createSphere(radius=0.05, color=(1., 0, 0, 1.), draw_faces=True, draw_edges=False):
    sphere = gl.MeshData.sphere(rows=10, cols=10, radius=radius)
    mesh = gl.GLMeshItem(meshdata=sphere, smooth=True,
                         drawFaces=draw_faces, color=color,
                         drawEdges=draw_edges, edgeColor=color)
    return mesh


def createAxis(*args, **kwargs):
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
    ang = np.linalg.norm(ax_ang)
    axis = np.array([0, 0, 1])
    if ang != 0:
        axis = ax_ang / ang

    new_triad.rotate(ang * 180 / np.pi, *axis)
    new_triad.translate(*position)

    return new_triad
