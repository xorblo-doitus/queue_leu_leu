# You can use any other library that includes standard Vector things
from pygame import Vector2
import math

SPEED_SCALE = 1 / 8
PI2 = math.pi * 2


def advance_on_circle(radius: float, progress: float):
  return 2 * math.asin(progress/(-2*radius))

def regular_polygon_radius(sides: int, size: float) -> float:
  return size / (2 * math.sin(math.pi/sides))


class OrbitFollowRing:
  def __init__(self):
    self.angle = 0
    self.radius = 1
    self.sizes: list[float] = []

  def add_angle(self, degree: int):
    self.angle += math.radians(degree)
    self.angle %= PI2


class OrbitFollowElement:
  def __init__(self, pos: Vector2, size: float):
    self.pos = pos
    self.size = size


class OrbitFollow:
  def __init__(self, distance: float, radius: float, speed: float, leader: OrbitFollowElement):
    """
    :param distance: distance between followers
    :param radius: minimum radius between rings
    :param leader: the leader
    """
    self.leader = leader
    self.followers: list[OrbitFollowElement] = []
    self.rings: list[OrbitFollowRing] = []
    self.radius = radius
    self.distance = distance
    self.speed = speed
    self.__last_radius = self.radius
    self.__last_distance = self.distance
    self.__last_speed = self.speed
    self.__total_size = 0

  def update_pos(self, new_pos: Vector2):
    """Update the position of the leader"""
    self.check_rings()
    self.leader.pos = new_pos
    
    # No rings so stop here
    if not self.rings: return
    
    # Update rings angle
    for i in range(len(self.rings)):
      self.rings[i].add_angle((self.speed if i % 2 else -self.speed) * SPEED_SCALE)
    
    # Update followers
    i = 0
    for ring in self.rings:
      if not ring.sizes: continue

      angle = ring.angle
      step = PI2 / len(ring.sizes)

      for s in ring.sizes:
        self.followers[i].pos = self.leader.pos + Vector2(math.cos(angle), math.sin(angle)) * ring.radius
        angle += step
        i += 1
   
  def adapt_rings(self):
    """Recalculate the rings"""
    # Clear rings
    for ring in self.rings: ring.sizes.clear()

    ring = longest_side = ii = 0
    biggest_size = self.leader.size
    total_radius = self.radius + biggest_size
    
    for i, f in enumerate(self.followers):
      self.get_ring(ring).sizes.append(2*f.size + self.distance)
      ii += 1
      biggest_size = max(biggest_size, f.size)
      
      if ii > 1: longest_side = max(longest_side, f.size + self.followers[i-1].size + self.distance)
      if ii > 2 and regular_polygon_radius(ii, longest_side) > total_radius + biggest_size:
        self.get_ring(ring).radius = total_radius + biggest_size
        total_radius += self.radius + 2*biggest_size
        ring += 1
        biggest_size = longest_side = ii = 0
        
    self.get_ring(ring).radius = total_radius + biggest_size
    # Remove empty rings
    self.rings = [ring for ring in self.rings if ring.sizes]

  def check_rings(self):
    """Recalculate the rings if .radius, .distance or a follower size has been changed"""
    total = sum(map(lambda f: f.size, self.followers))
    if (self.radius != self.__last_radius or 
        self.distance != self.__last_distance or 
        total != self.__total_size
    ):
      self.radius = max(self.radius, 1)
      self.__last_radius = self.radius
      self.distance = max(self.distance, 0)
      self.__last_distance = self.distance
      self.__total_size = total
      self.adapt_rings()
    
    # Clamp the speed
    if self.__last_speed != self.speed:
      self.speed = int(max(min(self.speed, 180 / SPEED_SCALE), -180 / SPEED_SCALE))
      self.__last_speed = self.speed

  def add_follower(self, follower: OrbitFollowElement):
    """Add a new follower in the rings"""
    self.followers.append(follower)
    self.__total_size += follower.size
    self.adapt_rings()

  def pop_follower(self, index: int=-1):
    self.remove_follower(self.followers[index])

  def remove_follower(self, follower: OrbitFollowElement):
    """Remove a follower of the rings"""
    if self.followers:
      self.followers.remove(follower)
      self.__total_size -= follower.size
      self.adapt_rings()
  
  def get_ring(self, i: int) -> OrbitFollowRing:
    """Create missing rings if needed and return the requested one"""
    for _ in range(i-len(self.rings)+1):
      self.rings.append(OrbitFollowRing())
    return self.rings[i]
