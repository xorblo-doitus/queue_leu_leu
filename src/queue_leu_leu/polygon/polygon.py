# You can use any other library that includes standard Vector things
from pygame import Vector2
from math import pi, cos, sin, radians, sqrt


ANGULAR_REFERENCE = Vector2(1, 0)
get_absolute_angle_deg = ANGULAR_REFERENCE.angle_to


def Vector2_polar(magnitude: float, angle_rad: float) -> Vector2:
  return magnitude * Vector2(cos(angle_rad), sin(angle_rad))


class Polygon:
  """
  Warning: Make sure to call `bake()` each time `points` are modified.
  Warning: Consecutive points can't be at the same position (zero-lenght sides are forbidden)
  """
  
  def __init__(self, points: list[Vector2] = []) -> None:
    self.points: list[Vector2] = points
    
    self._vectors: list[Vector2] = []
    self._growth_vectors: list[Vector2] = []
    self._incircle_radius: float = 1
    
    self.bake()
  
  @property
  def vectors(self) -> list[Vector2]:
    """Read-only: The vector at index i is the translation from point i to point i+1"""
    return self._vectors
  
  def bake(self) -> None:
    """
    This method should be called each time points are modified.
    You can do modifications in bulk without calling this method between each operation,
    but make sure to call this method at the end of the modifications in order to update internal caches.
    """
    if len(self.points) >= 2:
      self.points = [point for point, next_ in zip(self.points, self.points[1:] + [self.points[0]]) if point != next_]
      
    self._bake_vectors()
    self._bake_growth_vectors()
    self._bake_incircle()
  
  def _bake_incircle(self):
    self._incircle_radius = sqrt(min(map(lambda v: v.length_squared(), self.project_all_clamped(Vector2())))) if self._vectors else 1
  
  def _bake_vectors(self) -> None:
    if len(self.points) >= 2:
      self._vectors = [end - start for start, end in zip(self.points, self.points[1:] + [self.points[0]])]
    else:
      self._vectors = []
  
  def _bake_growth_vectors(self) -> None:
    if len(self.points) < 3:
      self._growth_vectors = []
      return
    
    new_growth_vectors: list[Vector2] = []
    
    for before, after in zip([self._vectors[-1]] + self._vectors, self._vectors):
      mean: Vector2 = before.normalize() + after.normalize()
      if mean:
          direction: Vector2 = mean.normalize().rotate(-90)
          new_growth_vectors.append(
            direction / sin(radians(direction.angle_to(after)))
          )
      else:
        # It is impossible to have a working growth vector for opposed vectors,
        # so we fallback on this.
        new_growth_vectors.append(before.normalize())
      
    
    self._growth_vectors = new_growth_vectors
  
  def sort_by_angle(self):
    """
    In place, Stable, O(n log n)
    """
    self.points.sort(key=get_absolute_angle_deg)
    self.bake()
  
  def growed(self, distance: float) -> "Polygon":
    return Polygon(list(map(lambda point, growth_vector: point + growth_vector * distance, self.points, self._growth_vectors)))
  
  def project(self, point: Vector2, segment_i: int) -> Vector2:
    return (point - self.points[segment_i]).project(self._vectors[segment_i]) + self.points[segment_i]
  
  def project_clamped(self, point: Vector2, segment_i: int) -> Vector2:
    projection: Vector2 = self.project(point, segment_i)
    progress: float = self.get_segment_progress(projection, segment_i)
    
    if progress >= 1:
      return self.points[(segment_i+1)%len(self.points)]
    elif progress <= 0:
      return self.points[segment_i]
    
    return projection
  
  def project_all(self, point: Vector2) -> list[Vector2]:
    return [self.project(point, i) for i in range(len(self._vectors))]
  
  def project_all_clamped(self, point: Vector2) -> list[Vector2]:
    return [self.project_clamped(point, i) for i in range(len(self._vectors))]
  
  def get_segment_progress(self, point: Vector2, segment_i: int) -> float:
    """Assumes point lies on the segment"""
    relative_to_start: Vector2 = point - self.points[segment_i]
    return relative_to_start.x / self._vectors[segment_i].x if self._vectors[segment_i].x else relative_to_start.y / self._vectors[segment_i].y

class PolygonFollower:
  def __init__(self, pos: Vector2, size: float):
    self.pos = pos
    self.size = size


class PolygonFollow:
  def __init__(self, spacing: float, gap: float, polygon: Polygon, leader: PolygonFollower):
    """
    :param spacing: distance between followers
    :param gap: minimum distance between rings
    :param max_angle: max angle each side, at back of the leader
    :param leader: the leader
    """
    self.leader: PolygonFollower = leader
    self.followers: list[PolygonFollower] = []
    self.polygons: list[Polygon] = []
    self.spacing: float = spacing
    self.gap: float = gap
    self.polygon: Polygon = polygon
    self.rotation: float = 0

  @property
  def rotation_deg(self) -> float:
    return self.rotation / pi * 180
  
  @rotation_deg.setter
  def rotation_deg(self, new: float):
    self.rotation = new / 180 * pi

  def update_pos(self, new_pos: Vector2):
    """Update the position of the leader"""
    self.adapt() # TODO remove this once the change checking is done
    
    self.leader.pos = new_pos
    
    # Update followers
    pass
  
  def adapt(self):
    """
    Update polygons and follower placement
    """
    pass
  

  def add_follower(self, follower: PolygonFollower):
    """Add a new follower"""
    self.followers.append(follower)

  def pop_follower(self, index: int=-1):
    self.followers.pop(index)

  def remove_follower(self, follower: PolygonFollower):
    """Remove a follower of the trail"""
    self.pop_follower(self.followers.index(follower))
  
