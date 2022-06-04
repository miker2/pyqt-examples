
import algorithms as alg

import matplotlib.pyplot as plt

def draw_poly(pts, draw_vertices=False, draw_normals=False):

    x = [pt.x for pt in pts]
    x.append(pts[0].x)

    y = [pt.y for pt in pts]
    y.append(pts[0].y)
    
    plt.plot(x, y, color='b')

    if draw_vertices:
        v_c = vertex_convexity(pts)
        plt.scatter(x[:-1], y[:-1], c=v_c, marker='o')

    if draw_normals:
        sc = 0.1
        n_pts = len(pts)
        for i in range(n_pts):
            ip1 = (i+1) % n_pts

            mid = alg.calc_midpoint(pts[i], pts[ip1])
            n_vec = alg.calc_normal(pts[i], pts[ip1])
            plt.plot([mid.x, mid.x + sc*n_vec[0]], [mid.y, mid.y + sc*n_vec[1]], color='green')

def vertex_convexity(pts):

    n_pts = len(pts)

    convex = []
    for i in range(n_pts):
        im1 = (i-1) % n_pts
        ip1 = (i+1) % n_pts
    
        if alg.is_convex(pts[im1], pts[i], pts[ip1]):
            convex.append('b')
        else:
            convex.append('r')

    return convex
