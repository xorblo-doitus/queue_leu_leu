# You can use any other library that includes standard Vector things
from pygame import Vector2


class OrbitFollowElement:
  def __init__(self, pos: Vector2, size: float):
    self.pos = pos
    self.size = size


class OrbitFollow:
  def __init__(self, distance: float, radius: float, leader: OrbitFollowElement):
    """
    :param distance: distance between followers
    :param radius: minimum radius between rings
    :param leader: the leader
    """
    self.leader = leader
    self.followers: list[OrbitFollowElement] = []
    self.radius = radius
    self.distance = distance
    self.angle = 0

  def update_pos(self, new_pos: Vector2):
    """Update the position of the leader"""
    self.leader.pos = new_pos

    for i, f in enumerate(self.followers):
      # TODO: make this

      f.pos = Vector2(self.leader.pos)

  def add_follower(self, follower: OrbitFollowElement):
    """Add a new follower in the trail"""
    self.followers.append(follower)

  def pop_follower(self, index: int=-1):
    self.remove_follower(self.followers[index])

  def remove_follower(self, follower: OrbitFollowElement):
    """Remove a follower of the trail"""
    if self.followers:
      self.followers.remove(follower)
