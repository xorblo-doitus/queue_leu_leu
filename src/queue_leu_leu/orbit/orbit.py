# You can use any other library that includes standard Vector things
from pygame import Vector2
import math

SPEED_SCALE = 1 / 8
PI2 = math.pi * 2


class OrbitFollowRing:
  def __init__(self):
    self.angle = 0
    self.width = 0
    self.sizes: list[float] = []

  def add_angle(self, degree: int):
    self.angle += math.radians(degree)
    self.angle %= PI2
  
  def add_size(self, size: float):
    if 2*size > self.width:
      self.width = 2*size
    self.sizes.append(size)
  
  def clear_sizes(self):
    self.sizes.clear()
    self.width = 0


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
    self.__radius = Vector2(radius, 0)
    self.radius = radius
    self.distance = distance
    self.speed = speed
    self.rings: list[OrbitFollowRing] = []
    self.__last_speed = self.speed
    self.__last_distance = self.distance
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
    ii = 0
    
    radius_tracker = self.radius
    for i, ring in enumerate(self.rings):
      if not ring.sizes: continue

      angle = ring.angle
      step = PI2 / len(ring.sizes)
      radius = radius_tracker + ring.width / 2

      for i, s in enumerate(ring.sizes):
        self.followers[ii].pos = self.leader.pos + Vector2(math.cos(angle), math.sin(angle)) * radius
        angle += step
        ii += 1
      
      radius_tracker += ring.width + self.distance
    
  def adapt_rings(self):
    """Recalculate the rings"""
    ring = 0
    total = 0
    radius_tracker = self.radius
    circumference = PI2 * radius_tracker
    if ring < len(self.rings): self.rings[ring].clear_sizes()

    for i, f in enumerate(self.followers):
      total += 2*f.size + self.distance
      
      if total > circumference:
        radius_tracker += self.distance + self.rings[ring].width # Add processed ring's width
        ring += 1
        circumference = PI2 * radius_tracker
        total = 2*f.size
        if ring < len(self.rings): self.rings[ring].clear_sizes()
      
      if ring >= len(self.rings): self.rings.append(OrbitFollowRing())
      self.rings[ring].add_size(f.size)
    
    # Remove empty rings
    ring += 1
    for _ in range(len(self.rings) - ring):
      self.rings.pop(ring)
  
  def check_rings(self):
    """Recalculate the rings if .radius, .distance or a follower size has been changed"""
    total = sum(map(lambda f: f.size, self.followers))
    if (self.radius != self.__radius.x or 
        self.distance != self.__last_distance or 
        total != self.__total_size
    ):
      self.radius = max(self.radius, 1)
      self.__radius.x = self.radius
      self.distance = max(self.distance, 0)
      self.__last_distance = self.distance
      self.__total_size = total
      self.adapt_rings()
    
    # Clamp the speed
    if self.__last_speed != self.speed:
      self.speed = int(max(min(self.speed, 180 / SPEED_SCALE), -180 / SPEED_SCALE))
      self.__last_speed = self.speed

  def add_follower(self, follower: OrbitFollowElement):
    """Add a new follower in the trail"""
    self.followers.append(follower)
    self.adapt_rings()

  def pop_follower(self, index: int=-1):
    self.remove_follower(self.followers[index])

  def remove_follower(self, follower: OrbitFollowElement):
    """Remove a follower of the trail"""
    if self.followers:
      self.followers.remove(follower)
      self.adapt_rings()
