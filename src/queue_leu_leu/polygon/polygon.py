# You can use any other library that includes standard Vector things
from types import UnionType
from pygame import Vector2
from math import pi, cos, sin, asin, radians, sqrt, isclose
from typing import Any, Generator, Self, Callable, Sequence
from enum import IntEnum, auto


type HashedVector2 = tuple[float, float]
type Intersection = tuple[int, Vector2, float]
type Walker = Generator[Vector2|None, tuple[float, float], None]
type NoCrossOverlapWalker = Generator[Vector2|None, float, None]


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


class GrowthMode(IntEnum):
  EXPAND_AND_MERGE = 0
  EXPAND = auto()
  SCALE_FAST = auto()
  _MODULO = auto()


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
    self._check_sum: int = 0
    
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
    
    # Used for fast approximative change detection
    self._check_sum = sum((p.x + p.y for p in self.points))
  
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
  
  def get_near_far_fast(self) -> tuple[float, float]:
    return self._incircle_radius, max(p.length() for p in self.points)
  
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
    cached_len: int = len(self.points)
    intersections: list[list[Intersection]] = [[] for _ in range(cached_len)]
    
    for i, point in enumerate(self.points):
      for other_i in range(i+2, cached_len) if i else range(i+2, cached_len-1):
        intersection: Vector2|None = intersect_segments(point, self.points[(i+1)%cached_len], self.points[other_i], self.points[(other_i+1)%cached_len])
        if intersection is not None:
          intersections[i].append((other_i, intersection, self.get_segment_progress(intersection, i)))
          intersections[other_i].append((i, intersection, self.get_segment_progress(intersection, other_i)))
    
    for i, l in enumerate(intersections):
      l.sort(key=lambda intersection: intersection[2])
      l.insert(0, ((i-1)%cached_len, self.points[i], -1))
      l.append(((i+1)%cached_len, self.points[(i+1)%cached_len], 2))
    
    graph: dict[HashedVector2, list[HashedVector2]] = {(*intersection[1],): [] for segment in intersections for intersection in segment}
    
    for segment in intersections:
      for inter_i in range(1, len(segment)):
        graph[(*segment[inter_i-1][1],)].append((*segment[inter_i][1],))
        graph[(*segment[inter_i][1],)].append((*segment[inter_i-1][1],))
    
    start_point: HashedVector2 = min(graph.keys(), key=lambda hash_: hash_[0])
    new_points: list[HashedVector2] = [start_point]
    current_point: HashedVector2 = min(
      (point for point in graph[start_point]),
      key=lambda point: get_absolute_angle_deg(Vector2(point)-start_point)
    )
    
    while current_point != start_point:
      new_points.append(current_point)
      reference: Vector2 = Vector2(current_point) - new_points[-2]
      current_point = min(
        (point for point in graph[current_point] if point != new_points[-2]),
        key=lambda point: angle_to_deg_closest_to_0(reference, Vector2(point)-current_point)
      )
    
    self.points = [*map(Vector2, new_points)]
    self.bake()
    return self


  def walk(self) -> Walker:
    if len(self.points) <= 1:
      print("[W] Invalid polygon for walk: Point count is", len(self.points))
      yield self.points[0] if self.points else Vector2()
      yield None
    
    segment_i: int = 0
    segment: Vector2 = self._vectors[segment_i]
    segment_progress: float = 0
    segment_length: float = segment.length()
    last_pos: Vector2 = self.points[0]
    wanted_progress, distance_to_end = yield last_pos
    reversed_polygon: Polygon|None = None
    
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
            to_start: Vector2 = self.points[new_segment_i] - last_pos
            angle_last_start_new: float = abs(pi - radians(abs(to_start.angle_to(self._vectors[new_segment_i]))))
            distance_last_start = to_start.length()
            sin_next: float = distance_last_start * sin(angle_last_start_new) / wanted_progress
            angle_deviation: float = angle_last_start_new + asin(sin_next)
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
      
      if distance_to_end > 0:
        if reversed_polygon is None:
          reversed_polygon = Polygon([self.points[0]] + self.points[:0:-1])
        
        reversed_walker = reversed_polygon.walk()
        reversed_walker.send(None)
        reversed_walker.send((distance_to_end, -1))
        _locals = reversed_walker.gi_frame.f_locals
        reversed_seg_i: int = len(self._vectors) - _locals["segment_i"] - 1
        if reversed_seg_i < segment_i or (
          reversed_seg_i == segment_i and segment_length - _locals["segment_progress"] < segment_progress
        ):
          yield None
          return
      
      wanted_progress, distance_to_end = yield last_pos
  
  def bulk_walk(self, distances: list[float], distances_to_end: list[float]) -> tuple[Walker, list[Vector2|None]]:
    walker: Generator[Vector2, float, None] = self.walk()
    result: list[Vector2] = [next(walker)]
    for data in zip(distances, distances_to_end):
      result.append(walker.send(data))
      if result[-1] is None: # DO NOT check falsy (Vector2(0, 0) conflict)
        break
    return walker, result
  
  def walk_no_cross_overlap(self, spacing: float, first_size: float) -> NoCrossOverlapWalker:
    if len(self.points) <= 1:
      print("[W] Invalid polygon for walk: Point count is", len(self.points))
      yield self.points[0] if self.points else Vector2()
      yield None
    
    segment_i: int = 0
    segment: Vector2 = self._vectors[segment_i]
    segment_progress: float = 0
    segment_length: float = segment.length()
    positions: list[Vector2] = [self.points[0]]
    sizes: list[float] = [first_size, (yield positions[-1])]
    space_from: int = -1
    wanted_progress: float = sizes[-1] + spacing + sizes[-2]
    
    while True:
      if space_from == -1 and segment_progress + wanted_progress <= segment_length:
          segment_progress += wanted_progress
          if segment_progress == segment_length:
            segment_i += 1
            if segment_i >= len(self._vectors):
              yield None
              return
            segment = self._vectors[segment_i]
            segment_length = segment.length()
            segment_progress = 0
            positions.append(self.points[segment_i])
          else:
            positions.append(self.points[segment_i] + scale_to_length(segment, segment_progress))
      else:
        if space_from == -1:
          new_segment_i: int = segment_i + 1
        else:
          new_segment_i = segment_i
        result: None|Vector2 = None
        while new_segment_i < len(self._vectors):
          to_start: Vector2 = self.points[new_segment_i] - positions[space_from]
          angle_to_next: float = radians(self._vectors[new_segment_i].angle_to(to_start))
          if abs(angle_to_next%pi) <= 1e-6:
            extend_from = self.project(positions[space_from], new_segment_i)
            extend_by = wanted_progress * cos(asin((extend_from - positions[space_from]).length()/wanted_progress))
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
              if (segment_progress / segment_length if new_segment_i == segment_i else 0) <= attempt[1] <= 1:
                result = attempt[0]
                segment_progress = (result - self.points[new_segment_i]).length()
                break
          else:
            angle_last_start_new: float = abs(pi - radians(abs(to_start.angle_to(self._vectors[new_segment_i]))))
            distance_last_start = to_start.length()
            sin_next: float = distance_last_start * sin(angle_last_start_new) / wanted_progress
            angle_deviation: float = angle_last_start_new + asin(sin_next)
            new_progress: float = distance_last_start * sin(angle_deviation) / sin_next
            attempt: Vector2 = self.points[new_segment_i] + scale_to_length(self._vectors[new_segment_i], new_progress)
            if 0 <= self.get_segment_progress(attempt, new_segment_i) <= 1:
              result = attempt
              segment_progress = new_progress
          
          if result is not None: # Warning: Do not check falsy as Vector can be (0, 0)
            segment_i = new_segment_i
            segment = self._vectors[segment_i]
            segment_length = segment.length()
            positions.append(result)
            break
          
          new_segment_i += 1
        else:
          yield None
          return
      
      for i in range(len(sizes) - (2 if space_from == -1 else 1)):
        if i != space_from and (sizes[i] + spacing + sizes[-1])**2 > (positions[i] - positions[-1]).length_squared():
          positions.pop()
          space_from = i
          wanted_progress = sizes[i] + spacing + sizes[-1]
          break
      else:
        sizes.append((yield positions[-1]))
        wanted_progress = sizes[-1] + spacing + sizes[-2]
        space_from = -1
  
  def bulk_walk_no_cross_overlap(self, spacing: float, sizes: list[float]) -> tuple[NoCrossOverlapWalker, list[Vector2|None]]:
    walker: Generator[Vector2, float, None] = self.walk_no_cross_overlap(spacing, sizes[0])
    result: list[Vector2] = [next(walker)]
    for i in range(1, len(sizes)):
      result.append(walker.send(sizes[i]))
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
  def __init__(self, spacing: float, gap: float, polygon: Polygon, leader: PolygonFollower, cross_overlap: bool = True, growth_mode: GrowthMode = GrowthMode.EXPAND_AND_MERGE):
    """
    :param spacing: distance between followers
    :param gap: minimum distance between rings
    :param max_angle: max angle each side, at back of the leader
    :param leader: the leader
    :param cross_overlap: If True, non consecutive followers can overlap (like at intersections). If False, a slow algorithm prevent this.
    """
    self.leader: PolygonFollower = leader
    self.followers: list[PolygonFollower] = []
    self.relative_positions: list[Vector2] = []
    self.spacing: float = spacing
    self.gap: float = gap
    self.polygon: Polygon = polygon
    self.cross_overlap: bool = cross_overlap
    self.growth_mode: GrowthMode = growth_mode
    
    self._debug_polygons: list[Polygon] = []
    
    self.__last_gap: float = self.gap
    self.__last_spacing: float = self.spacing
    self.__last_total_size: float = 0
    self.__last_identity: float = 0
    self.__cross_overlap: bool = cross_overlap
    self.__last_growth_mode: GrowthMode = growth_mode

  def update_pos(self, new_pos: Vector2):
    """Update the position of the leader"""
    self.check_change()
    
    self.leader.pos = new_pos
    
    for follower, relative_pos in zip(self.followers, self.relative_positions):
      follower.pos = new_pos + relative_pos
  
  def adapt(self):
    """
    Update follower placement
    """
    self.relative_positions.clear()
    self._debug_polygons.clear()
    
    if not self.followers or len(self.polygon.points) <= 2:
      return
    
    # Caches
    to_add: list[float] = [f.size for f in self.followers]
    if self.cross_overlap:
      chords: list[float] = [to_add[i] + self.spacing + to_add[i+1] for i in range(len(to_add)-1)]
    
    # Tracking variables
    last_growed_polygon: Polygon|None = None
    last_growed_polygon_biggest: float = 0
    start_i: int = 0
    end_i: int = -1
    
    # Polygon specific variables
    biggest: float = to_add[0]
    last_biggest: float = 0
    def get_polygon() -> Polygon:
      if last_growed_polygon:
        match self.growth_mode:
          case GrowthMode.EXPAND_AND_MERGE:
            return last_growed_polygon.growed(last_growed_polygon_biggest + self.gap + biggest, True)
          case GrowthMode.EXPAND:
            return last_growed_polygon.growed(last_growed_polygon_biggest + self.gap + biggest, False)
          case GrowthMode.SCALE_FAST:
            near, far = last_growed_polygon.get_near_far_fast()
            return last_growed_polygon.growed_to_inradius(far + last_growed_polygon_biggest + self.gap + biggest)
      else:
        return self.polygon.growed_to_inradius(self.leader.size + self.gap + biggest)
    polygon: Polygon = get_polygon()
    walker: Walker|NoCrossOverlapWalker = polygon.walk() if self.cross_overlap else polygon.walk_no_cross_overlap(self.spacing, to_add[start_i])
    positions: list[Vector2] = [next(walker)]
    last_positions: list[Vector2] = []
    if self.cross_overlap:
      cached_distance_to_end: float = to_add[start_i] + self.spacing
    
    while end_i < len(to_add) - 1:
      end_i += 1
      size: float = to_add[end_i]
      overfits = False
      
      if size > biggest:
        last_biggest = biggest
        last_positions = positions
        biggest = size
        polygon = get_polygon()
        walker, positions = polygon.bulk_walk(chords[start_i:end_i-1], (cached_distance_to_end + to_add[i] for i in range(start_i, end_i))) if self.cross_overlap else polygon.bulk_walk_no_cross_overlap(self.spacing, to_add[start_i:end_i])
        # Depending on the polygon, a grown version can fit less of the same followers
        if positions[-1] is None:
          overfits = "growth"
      
      if not overfits and end_i - start_i >= 1:
        positions.append(walker.send((chords[end_i-1], cached_distance_to_end + to_add[end_i]) if self.cross_overlap else to_add[end_i]))
      
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
            polygon = get_polygon()
          else:
            positions.pop()
          
        
        self.relative_positions += positions
        
        # Progress
        self._debug_polygons += [
          polygon.growed(-biggest),
          polygon,
          polygon.growed(biggest),
        ]
        if self.growth_mode == GrowthMode.EXPAND_AND_MERGE:
          self._debug_polygons.insert(-2, last_growed_polygon.growed(last_growed_polygon_biggest + self.gap + biggest, False) if last_growed_polygon else Polygon())
        
        last_growed_polygon = polygon
        last_growed_polygon_biggest = biggest
        
        # Clean up variables
        start_i = end_i + 1
        if start_i < len(to_add):
          biggest = to_add[start_i]
          last_biggest = 0
          polygon = get_polygon()
          walker = polygon.walk() if self.cross_overlap else polygon.walk_no_cross_overlap(self.spacing, to_add[start_i])
          positions = [next(walker)]
          last_positions = []
          if self.cross_overlap:
            cached_distance_to_end = to_add[start_i] + self.spacing
  
  def check_change(self):
    total_size = sum(f.size for f in self.followers)
    if (
      self.__last_gap != self.gap
      or self.__last_spacing != self.spacing
      or self.__last_total_size != total_size
      or self.__last_identity != self.polygon._check_sum
      or self.__cross_overlap != self.cross_overlap
      or self.__last_growth_mode != self.growth_mode
    ):
      self.__last_gap = self.gap
      self.__last_spacing = self.spacing
      self.__last_total_size = total_size
      self.__last_identity = self.polygon._check_sum
      self.__cross_overlap = self.cross_overlap
      self.__last_growth_mode = self.growth_mode
      self.adapt()
  
  def add_follower(self, follower: PolygonFollower):
    """Add a new follower"""
    self.followers.append(follower)

  def pop_follower(self, index: int=-1):
    self.followers.pop(index)

  def remove_follower(self, follower: PolygonFollower):
    """Remove a follower of the trail"""
    self.pop_follower(self.followers.index(follower))
  
