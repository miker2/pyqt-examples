from dataclasses import dataclass
import numpy as np

@dataclass
class Point:
    x : float = 0
    y : float = 0
    

def is_convex(pt1 : Point, pt2 : Point, pt3 : Point) -> bool:
    if triangle_area(pt1, pt2, pt3) < 0:
        return True

    return False

def triangle_area(pt1 : Point, pt2 : Point, pt3 : Point) -> float:
    area = 0

    area += pt1.x * (pt3.y - pt2.y)
    area += pt2.x * (pt1.y - pt3.y)
    area += pt3.x * (pt2.y - pt1.y)

    # For the actual area, we need to multiple 'area' by 0.5, but we
    # only care about the sign of the area

    return area

def calc_midpoint(pt1 : Point, pt2 : Point):
    return Point(0.5 * (pt1.x + pt2.x), 0.5 * (pt1.y + pt2.y))

def calc_normal(pt1 : Point, pt2 : Point):
    vec = np.array([pt2.x, pt2.y], dtype=np.float64) - np.array([pt1.x, pt1.y])
    print(f"vec: {vec}, norm: {np.linalg.norm(vec)}")
    vec /= np.linalg.norm(vec)

    return [-vec[1], vec[0]]
