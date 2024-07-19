# You can use any other library that includes standard Vector things
from pygame import Vector2


class JointFollowElement:
  def __init__(self, pos: Vector2, size: float):
    self.pos = pos
    self.size = size


class JointFollow:
  def __init__(self, distance: float, leader: JointFollowElement):
    """
    :param distance: distance between each followers (must never be less than 0)
    :param leader: the leader
    """
    self.leader = leader
    self.followers: list[JointFollowElement] = []
    self.distance = distance

  def update_pos(self, new_pos: Vector2):
    """Update the position of the leader"""
    self.leader.pos = new_pos
    # Security
    if self.distance < 0: self.distance = 0

    for i, f in enumerate(self.followers):
      target = self.leader if i == 0 else self.followers[i - 1]
      distance = f.pos.distance_to(target.pos)
      min_distance = self.distance * 2 + target.size + f.size

      if distance > min_distance:
        f.pos += (target.pos - f.pos) / distance * (distance - min_distance)

  def add_follower(self, follower: JointFollowElement):
    """Add a new follower in the trail"""
    self.followers.append(follower)

  def pop_follower(self, index: int=-1):
    self.followers.pop(index)

  def remove_follower(self, follower: JointFollowElement):
    """Remove a follower of the trail"""
    self.pop_follower(self.followers.index(follower))
