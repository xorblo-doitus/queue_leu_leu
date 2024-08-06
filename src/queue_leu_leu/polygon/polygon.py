# You can use any other library that includes standard Vector things
from types import UnionType
from pygame import Vector2
from math import pi, cos, sin, asin, radians, sqrt, isclose
from typing import Any, Generator, Self, Callable, Sequence

type HashedVector2 = tuple[float, float]
type Intersection = tuple[int, Vector2, float]

# PI2 = pi*2
ANGULAR_REFERENCE = Vector2(1, 0)
get_absolute_angle_deg = ANGULAR_REFERENCE.angle_to


def angle_to_deg_closest_to_0(self: Vector2, other: Vector2) -> float:
  angle: float = self.angle_to(other)
  
  if angle < -180:
    angle += 360
  elif angle > 180:
    angle -= 360
  
  return angle


def scale_to_length(vector: Vector2, scale: float) -> Vector2:
  """QOL because the native method is in place"""
  new = Vector2(vector)
  new.scale_to_length(scale)
  return new


def get_segment_progress(point: Vector2, start: Vector2, displacement: Vector2) -> float:
  """Assumes point lies on the segment"""
  relative_to_start: Vector2 = point - start
  return (
    relative_to_start.x / displacement.x
    if displacement.x else
    relative_to_start.y / displacement.y
  )


def is_inside(point: Vector2, start: Vector2, displacement: Vector2, epsilon=0e-6) -> bool:
  return epsilon <= get_segment_progress(point, start, displacement) <= 1 + epsilon


def intersect_lines(p1: Vector2, p2: Vector2, d1: Vector2, d2: Vector2) -> Vector2|None:
  """
  WARNING: Computes intersection for infinite lines.
  WARNING: Return None if lines are parallel
  Python application of this formula :
  https://en.wikipedia.org/w/index.php?title=Line%E2%80%93line_intersection&oldid=1229564037#Given_two_points_on_each_line
  """
  x1, y1, x2, y2, x3, y3, x4, y4 = *p1, *p2, *d1, *d2
  denominator = ((x1-x2)*(y3-y4) - (y1-y2)*(x3-x4))
  
  if denominator == 0:
    return None
  
  cache_a = (x1*y2 - y1*x2)
  cache_b = (x3*y4 - y3*x4)
  
  return Vector2(
    (cache_a*(x3-x4) - (x1-x2)*cache_b) / denominator,
    (cache_a*(y3-y4) - (y1-y2)*cache_b) / denominator
  )


def intersect_segments(p1: Vector2, p2: Vector2, d1: Vector2, d2: Vector2) -> Vector2|None:
  """
  WARNING: Computes intersection for infinite lines.
  WARNING: Return None if there is no intersection or if lines are coincident.
  Python application of this formula :
  https://en.wikipedia.org/w/index.php?title=Line%E2%80%93line_intersection&oldid=1229564037#Given_two_points_on_each_line
  """
  intersection = intersect_lines(p1, p2, d1, d2)
  
  if intersection is None or not is_inside(intersection, p1, p2-p1) or not is_inside(intersection, d1, d2-d1):
    return None
  
  return intersection

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
  
  def growed(self, distance: float, self_merge: bool = False) -> "Polygon":
    new = Polygon(list(map(lambda point, growth_vector: point + growth_vector * distance, self.points, self._growth_vectors)))
    
    if self_merge:
      new.merge_self_contained()
    
    return new
  
  def growed_to_inradius(self, desired_inradius: float) -> "Polygon":
    return self * (desired_inradius / self._incircle_radius)
  
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
  
  def merge_self_contained(self) -> Self:
    # return
    # i: int = 0
    # clockwise: bool = True
    # points: list[Vector2] = []
    # while i < len(self.points):
    #   points.append(self.points[i])
    #   for preshot_i in range(i+2, len(self.points)-2) if clockwise else :
    #     intersetion: Vector2|None = intersect_segments(self.points[i], self.points[i+1], self.points[preshot_i], self.points[preshot_i+1])
    #     if intersetion is not None:
    #       points.append(intersetion)
    #       clockwise = self._vectors[i].angle_to(self.points[preshot_i+1] - intersetion) % PI2 > pi
    #       i = preshot_i
    #       break
    #   i += 1 if clockwise else -1
    # print("merged")
    
    
    
    hashes: list[HashedVector2] = [(*point,) for point in self.points]
    intersections: list[list[Intersection]] = [[] for _ in range(len(self.points))]
    for i, (point, hash_, segment) in enumerate(zip(self.points, hashes, self._vectors)):
      # graph[hash_] = [self.points[i-1], self.points[(i+1)%len(self.points)]]
      for other_i in range(i+2, len(self.points)) if i else range(i+2, len(self.points)-1):
        intersection: Vector2|None = intersect_segments(self.points[i], self.points[(i+1)%len(self.points)], self.points[other_i], self.points[(other_i+1)%len(self.points)])
        if intersection is not None:
          # print(i, other_i, intersection)
          intersections[i].append((other_i, intersection, self.get_segment_progress(intersection, i)))
          intersections[other_i].append((i, intersection, self.get_segment_progress(intersection, other_i)))
    
    for i, l in enumerate(intersections):
      l.sort(key=lambda intersection: intersection[2])
      l.insert(0, ((i-1)%len(self.points), self.points[i], -1))
      l.append(((i+1)%len(self.points), self.points[(i+1)%len(self.points)], 2))
    
    graph: dict[HashedVector2, list[HashedVector2]] = {(*intersection[1],): [] for segment in intersections for intersection in segment}
    # print(
    #   "\n\n=======================\n\n",
    #   intersections,
    # )
    for seg_i, segment in enumerate(intersections):
      # graph[(*segment[0][1],)].append((*intersections[seg_i-1][-1][1],))
      # graph[(*segment[0][1],)].append((*segment[1][1],))
      # for inter_i in range(1, len(segment)-1):
      for inter_i in range(1, len(segment)):
        graph[(*segment[inter_i-1][1],)].append((*segment[inter_i][1],))
        graph[(*segment[inter_i][1],)].append((*segment[inter_i-1][1],))
      # DO NOT uncomment: wouldinsert extremities twice
      # graph[(*segment[-1][1],)].append((*segment[-2][1],))
      # graph[(*segment[0][1],)].append((*intersections[(seg_i+1)%len(intersections)][0][1],))
    
    
    # start_i = 0
    # start_point: Vector2 = self.points[start_i]
    # for i, point in enumerate(self.points[1:]):
    #   if point.x < start_point:
    #     start_point = point
    #     start_i = i
    start_point: HashedVector2 = min(graph.keys(), key=lambda hash_: hash_[0])
    new_points: list[HashedVector2] = [
      start_point,
    ]
    current_point: HashedVector2 = min(
      (point for point in graph[start_point]),
      key=lambda point: get_absolute_angle_deg(Vector2(point)-start_point)
    )
    
    while current_point != start_point:
      new_points.append(current_point)
      reference: Vector2 = Vector2(current_point) - new_points[-2]
      # print([point for point in graph[current_point] if point != new_points[-2]])
      current_point = min(
        (point for point in graph[current_point] if point != new_points[-2]),
        key=lambda point: angle_to_deg_closest_to_0(reference, Vector2(point)-current_point)
      )
    
    self.points = [*map(Vector2, new_points)]
    self.bake()
    return self


# class PolygonWalker():
#   def __init__(self, polygon: Polygon) -> None:
#     self._polygon: Polygon = polygon
#     self._segment_i: int = 0
#     self._segment_progress: float = 0
    
#     self._segment_length: float = self._polygon._vectors[self._segment_i].length()
  
#   def progress(self, distance: float) -> Vector2:
#     if self._segment_progress + distance <= self._segment_length:
#       self._segment_progress += distance
#       if self._segment_progress == self._segment_length:
#         self._segment_i += 1


  def walk(self) -> Generator[Vector2, float, None]:
    if len(self.points) <= 1:
      print("[W] Invalid polygon for walk: Point count is", len(self.points))
      yield self.points[0] if self.points else Vector2()
      yield None
    
    segment_i: int = 0
    segment: Vector2 = self._vectors[segment_i]
    segment_progress: float = 0
    segment_length: float = segment.length()
    last_pos: Vector2 = self.points[0]
    wanted_progress: float = yield last_pos
    
    while True:
      if segment_progress + wanted_progress <= segment_length:
          segment_progress += wanted_progress
          if segment_progress == segment_length:
            segment_i += 1
            if segment_i >= len(self._vectors):
              yield None
              return
            segment = self._vectors[segment_i]
            segment_length = segment.length()
            segment_progress = 0
            last_pos = self.points[segment_i]
          else:
            last_pos = self.points[segment_i] + scale_to_length(segment, segment_progress)
      else:
        new_segment_i: int = segment_i + 1
        # available_progress: float = segment.length() - segment_progress
        result: None|Vector2 = None
        while new_segment_i < len(self._vectors):
          angle_to_next: float = radians(self._vectors[new_segment_i].angle_to(segment))
          if abs(angle_to_next%pi) <= 1e-6:
            extend_from = self.project(last_pos, new_segment_i)
            extend_by = wanted_progress * cos(asin((extend_from - last_pos).length()/wanted_progress))
            displacement = scale_to_length(segment, extend_by)
            attempts: list[tuple[Vector2, float]] = list(map(
              lambda attempt: (attempt, self.get_segment_progress(attempt, new_segment_i)),
              [
                extend_from + displacement,
                extend_from - displacement
              ]
            ))
            attempts.sort(key=lambda attempt: attempt[1])
            for attempt in attempts:
              if 0 <= attempt[1] <= 1:
                result = attempt[0]
                segment_progress = (result - self.points[new_segment_i]).length()
                break
          else:
            # progress_to_intersection: float = (
            #   available_progress
            #   if segment_i + 1 == new_segment_i else
            #   (intersect(
            #     self.points[segment_i],
            #     self.points[segment_i+1],
            #     self.points[new_segment_i],
            #     self.points[(new_segment_i+1)%len(self.points)]
            #   ) - self.points[segment_i] + scale_to_length(segment, segment_progress)).length()
            # )
            to_start: Vector2 = self.points[new_segment_i] - last_pos
            angle_last_start_new: float = abs(pi - radians(abs(to_start.angle_to(self._vectors[new_segment_i]))))
            distance_last_start = to_start.length()
            sin_next: float = distance_last_start * sin(angle_last_start_new) / wanted_progress
            angle_deviation: float = angle_last_start_new + asin(sin_next)
            # if angle_deviation <= 0:
            #   print("fixed")
            #   angle_deviation = pi - angle_last_start_new - asin(sin_next)
            # print(angle_last_start_new + abs(asin(sin_next)), "vs", pi - angle_last_start_new - abs(asin(sin_next)))
            # angle_deviation: float =  angle_last_start_new + abs(asin(sin_next))
            # angle_deviation: float = pi - angle_last_start_new - abs(asin(sin_next))
            new_progress: float = distance_last_start * sin(angle_deviation) / sin_next
            attempt: Vector2 = self.points[new_segment_i] + scale_to_length(self._vectors[new_segment_i], new_progress)
            if 0 <= self.get_segment_progress(attempt, new_segment_i) <= 1:
              result = attempt
              segment_progress = new_progress
          
          if result is not None: # Warning: Do not check falsy as Vector can be (0, 0)
            segment_i = new_segment_i
            segment = self._vectors[segment_i]
            segment_length = segment.length()
            last_pos = result
            break
          
          new_segment_i += 1
        else:
          yield None
          return
      
      wanted_progress: float = yield last_pos
  
  def bulk_walk(self, distances) -> tuple[Generator[Vector2, float, None], list[Vector2|None]]:
    walker: Generator[Vector2, float, None] = self.walk()
    result: list[Vector2] = [next(walker)]
    for distance in distances:
      result.append(walker.send(distance))
      if result[-1] is None: # DO NOT check falsy (Vector2(0, 0) conflict)
        break
    return walker, result
  
  def rotate_deg(self, angle: float) -> Self:
    for point in self.points:
      point.rotate_ip(angle)
    self.bake()
    return self
  
  def rotate_rad(self, angle: float) -> Self:
    for point in self.points:
      point.rotate_rad_ip(angle)
    self.bake()
    return self
  
  def __mul__(self, other: float) -> "Polygon":
    return Polygon([point * other for point in self.points])
  
  __rmul__ = __mul__
  
  def __imul__(self, other: float) -> Self:
    for point in self.points:
      point *= other
    self.bake()
    return self


class PolygonFollower:
  def __init__(self, pos: Vector2, size: float):
    self.pos: Vector2 = pos
    self.size: float = size


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
    self.relative_positions: list[Vector2] = []
    self.spacing: float = spacing
    self.gap: float = gap
    self.polygon: Polygon = polygon
    self.rotation: float = 0
    self.prevent_self_including: bool = True
    
    self._debug_polygons: list[Polygon] = []

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
    
    for follower, relative_pos in zip(self.followers, self.relative_positions):
      follower.pos = new_pos + relative_pos
  
  def adapt(self):
    """
    Update follower placement
    """
    # return
    self.relative_positions.clear()
    self._debug_polygons.clear()
    
    if not self.followers or len(self.polygon.points) <= 2:
      return
    
    # Caches
    to_add: list[float] = [f.size for f in self.followers]
    chords: list[float] = [to_add[i] + self.spacing + to_add[i+1] for i in range(len(to_add)-1)] 
    
    # Tracking variables
    last_growed_polygon: Polygon|None = None
    last_growed_polygon_biggest: float = 0
    start_i: int = 0
    end_i: int = -1
    
    # Polygon specific variables
    biggest: float = to_add[0]
    last_biggest: float = 0
    polygon: Polygon = last_growed_polygon.growed(last_growed_polygon_biggest + self.gap + biggest, self.prevent_self_including) if last_growed_polygon else self.polygon.growed_to_inradius(self.leader.size + self.gap + biggest)
    walker: Generator[Vector2, float, None] = polygon.walk()
    positions: list[Vector2] = [next(walker)]
    last_positions: list[Vector2] = []
    
    while end_i < len(to_add) - 1:
      end_i += 1
      size: float = to_add[end_i]
      overfits = False
      
      if size > biggest:
        last_biggest = biggest
        last_positions = positions
        biggest = size
        polygon = last_growed_polygon.growed(last_growed_polygon_biggest + self.gap + biggest, self.prevent_self_including) if last_growed_polygon else self.polygon.growed_to_inradius(self.leader.size + self.gap + biggest)
        walker, positions = polygon.bulk_walk(chords[start_i:end_i-1])
        # Depending on the polygon, a grown version can fit less of the same followers
        if positions[-1] is None:
          overfits = "growth"
      
      if not overfits and end_i - start_i >= 1:
        positions.append(walker.send(chords[end_i-1]))
      
      overfits = (
        overfits
        or end_i - start_i > 0
        and positions[-1] is None
      )
      
      if overfits or end_i >= len(to_add) - 1:
        if overfits:
          end_i -= 1
          if overfits == "growth":
            biggest = last_biggest
            positions = last_positions
            polygon = last_growed_polygon.growed(last_growed_polygon_biggest + self.gap + biggest, self.prevent_self_including) if last_growed_polygon else self.polygon.growed_to_inradius(self.leader.size + self.gap + biggest)
          else:
            positions.pop()
          
        
        self.relative_positions += positions
        
        # Progress
        self._debug_polygons += [
          polygon.growed(-biggest),
          polygon,
          polygon.growed(biggest),
        ]
        if self.prevent_self_including:
          self._debug_polygons.insert(-2, last_growed_polygon.growed(last_growed_polygon_biggest + self.gap + biggest, self.prevent_self_including) if last_growed_polygon else Polygon())
        
        last_growed_polygon = polygon
        last_growed_polygon_biggest = biggest
        
        # Clean up variables
        start_i = end_i + 1
        if start_i < len(to_add):
          biggest = to_add[start_i]
          last_biggest = 0
          polygon = last_growed_polygon.growed(last_growed_polygon_biggest + self.gap + biggest, self.prevent_self_including) if last_growed_polygon else self.polygon.growed_to_inradius(self.leader.size + self.gap + biggest)
          walker = polygon.walk()
          positions = [next(walker)]
          last_positions = []
  

  def add_follower(self, follower: PolygonFollower):
    """Add a new follower"""
    self.followers.append(follower)

  def pop_follower(self, index: int=-1):
    self.followers.pop(index)

  def remove_follower(self, follower: PolygonFollower):
    """Remove a follower of the trail"""
    self.pop_follower(self.followers.index(follower))
  
