# You can use any other library that includes standard Vector things
from pygame import Vector2
import math


class ArcFollowElement:
  def __init__(self, pos: Vector2, size: float):
    self.pos = pos
    self.size = size


class ArcFollow:
  def __init__(self, distance: float, radius: float, max_angle: float, leader: ArcFollowElement):
    """
    :param distance: distance between followers
    :param radius: minimum radius between rings
    :param max_angle: max angle each side, at back of the leader
    :param leader: the leader
    """
    self.leader = leader
    self.followers: list[ArcFollowElement] = []
    self.rings: list[int] = []
    self.distance = distance
    self.radius = radius
    self.max_angle = max_angle
    self.rotation = 0

  def update_pos(self, new_pos: Vector2):
    """Update the position of the leader"""
    self.check_properties()
    
    self.leader.pos = new_pos
    ring = 0
    size = 0
    self.rings.clear()

    for i, f in enumerate(self.followers):
      ...

    self.update_rings()

  def update_rings(self):
    """Update followers in rings"""
    for i, f in enumerate(self.followers):
#      f_angle = 0 if i == 0 else (self.distance if (i+1)%2 == 0 else -self.distance) * math.ceil((i+1)/2)
#      angle = math.radians(self.rotation + 180 + (math.fmod(f_angle, self.max_angle) if f_angle != 0 else f_angle))
#      radius = self.leader.size + (f.size + self.radius) * (abs(math.ceil(f_angle/self.max_angle))+1)
#
#      f.pos = Vector2(
#        self.leader.pos.x + math.cos(angle) * radius, 
#        self.leader.pos.y + math.sin(angle) * radius
#      )
      f.pos = Vector2(self.leader.pos)

  def check_properties(self):
    """Security to always have the right properties values"""
    # Check max angle
    self.max_angle = max(min(self.max_angle, 180), 1)
    # Check the distance
    if self.distance < 0: self.distance = 0
    # Check rotation
    if self.rotation > 180: self.rotation = -180
    elif self.rotation < -180: self.rotation = 180

  def add_follower(self, follower: ArcFollowElement):
    """Add a new follower"""
    self.followers.append(follower)

  def pop_follower(self, index: int=-1):
    self.remove_follower(self.followers[index])

  def remove_follower(self, follower: ArcFollowElement):
    """Remove a follower"""
    if self.followers:
      self.followers.remove(follower)
