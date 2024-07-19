from math import cos, sin, asin, pi
from pygame import Vector2


PI2 = 2 * pi

def advance_on_circle(radius: float, chord: float, fallback: float = PI2) -> float:
  alpha: float = chord / (2*radius)
  if not -1 <= alpha <=1: return fallback
  return 2 * asin(alpha)


def Vector2_polar(magnitude: float, angle_rad: float) -> Vector2:
  return magnitude * Vector2(cos(angle_rad), sin(angle_rad))