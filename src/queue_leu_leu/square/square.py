# You can use any other library that includes standard Vector things
from pygame import Vector2
import math

SPEED_SCALE = 1 / 8
PI2 = math.pi * 2


class SquareFollowRing:
  def __init__(self):
    self.angle = 0
    self.radius = 0
    self.sizes: list[float] = []

  def add_angle(self, degree: int):
    self.angle += math.radians(degree)
    self.angle %= PI2


class SquareFollowElement:
  def __init__(self, pos: Vector2, size: float):
    self.pos = pos
    self.size = size


class SquareFollow:
  def __init__(self, distance: float, radius: float, leader: SquareFollowElement, speed: float=1):
    """
    :param distance: distance between followers
    :param radius: minimum radius between rings
    :param leader: the leader
    """
    self.leader = leader
    self.followers: list[SquareFollowElement] = []
    self.__radius = Vector2(radius, 0)
    self.radius = radius
    self.distance = distance
    self.speed = speed
    self.rings: list[SquareFollowRing] = []
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
#    ii = 0
#    
#    for i, f in enumerate(self.followers):
#      
#      size = len(self.followers)
#
#      side = math.ceil(math.sqrt(size + 1));
#      cx = i % side
#      cy = i / side
#
#      #don't hog the middle spot
#      if cx == side/2 and cy == side/2 and (side%2)==1:
#        cx = size % side
#        cy = size / side
#      
#      offset = Vector2(cx - (side/2 - 0.5), cy - (side/2 - 0.5))
#      self.followers[ii].pos = self.leader.pos + offset * self.distance
#      ii += 1

  def adapt_rings(self):
    """Recalculate the rings"""
    ring = 0
    total = 0
    circumference = PI2 * ((ring + 1) * self.radius)
    if ring < len(self.rings): self.rings[ring].sizes.clear()

    for i, f in enumerate(self.followers):
      
      size = 2 * f.size + self.distance
      total += size
      
      if total > circumference:
        ring += 1
        circumference = PI2 * ((ring + 1) * self.radius)
        total = 0
        if ring < len(self.rings): self.rings[ring].sizes.clear()
      
      if ring >= len(self.rings): self.rings.append(SquareFollowRing())
      self.rings[ring].sizes.append(size)
      #if size > self.rings[ring].radius: self.rings[ring].radius = size
    
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

  def add_follower(self, follower: SquareFollowElement):
    """Add a new follower in the trail"""
    self.followers.append(follower)
    self.check_rings()

  def pop_follower(self, index: int=-1):
    self.remove_follower(self.followers[index])

  def remove_follower(self, follower: SquareFollowElement):
    """Remove a follower of the trail"""
    if self.followers:
      self.followers.remove(follower)
      self.adapt_rings()
