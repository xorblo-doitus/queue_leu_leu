# You can use any other library that includes standard Vector things
from pygame import Vector2


class TrailFollowElement:
  def __init__(self, pos: Vector2, size: float):
    self.pos = pos
    self.size = size


class TrailFollow:
  def __init__(self, distance: float, leader: TrailFollowElement, precise=False, elastic=False):
    """
    :param distance: distance between each followers (must never be less than 1)
    :param leader: the leader
    :param precise: when True, a lerp is performed between points to get a smooth movement
    :param elastic: when True, the trail points will gradually reach the leader point. 
    So 'distance' become 'speed'.
    
    Note: the elastic effect is already precise, so 'precise' will be always False.
    """
    self.leader = leader
    self.followers: list[TrailFollowElement] = []
    self.trail = [self.leader.pos]
    self.distance = distance
    self.__last_distance = self.distance
    self.__total_size = 0
    self.__i = 0

    if elastic:
      self.update_pos = self.update_pos_elastic
      precise = False # disable this to avoid trail problems
    if precise:
      self.update_trail = self.update_trail_precise
      self.get_size = self.get_size_precise

  def update_pos(self, new_pos: Vector2):
    """Update the position of the leader"""
    self.check_trail()

    self.leader.pos = new_pos
    current_pos = self.trail[self.__i]

    while self.trail[self.__i].distance_to(new_pos) >= self.get_distance():
      current_pos = current_pos.move_towards(new_pos, self.get_distance())
      self.__i = self._wrapped(self.__i - 1)
      self.trail[self.__i] = current_pos

    self.update_trail()

  def update_pos_elastic(self, new_pos: Vector2):
    self.check_trail()

    self.leader.pos = new_pos
    current_pos = self.trail[self.__i].move_towards(new_pos, self.get_distance())
    self.__i = self._wrapped(self.__i - 1)
    self.trail[self.__i] = current_pos

    self.update_trail()

  def update_trail(self):
    """Update the trail"""
    i = self.__i + self.get_size(self.leader)/2
    tsize = len(self.trail)

    for follower in self.followers:
      size = self.get_size(follower)/2
      i += size
      follower.pos = self.trail[self._wrapped(int(i % tsize))]
      i += size

  def update_trail_precise(self):
    i = self.leader.size + self.get_distance() - self.leader.pos.distance_to(self.trail[self.__i])
    tsize = len(self.trail)

    for follower in self.followers:
      i += follower.size
      offset = self.__i + i / self.get_distance()
      follower.pos = Vector2.lerp(  # vvv equivalent of ceil()
        self.trail[self._wrapped(int(-(-(offset % tsize)//1)))],
        self.trail[self._wrapped(int(offset % tsize))] if i >= 0 else self.leader.pos,
        1 - (offset % 1)
      )
      i += follower.size + self.get_distance()

  def check_trail(self):
    """
    Check the trail and
    recalculate it when .distance has changed or if one of the followers changed of size.
    """
    total = sum(map(lambda f: f.size, self.followers))
    if self.get_distance() != self.__last_distance or total != self.__total_size:
      self.__last_distance = self.get_distance()
      self.__total_size = total
      self.adapt_trail()

  def add_follower(self, follower: TrailFollowElement):
    """Add a new follower in the trail"""
    self.followers.append(follower)
    self.__total_size += follower.size
    self.adapt_trail()

  def pop_follower(self, index: int=-1):
    self.remove_follower(self.followers[index])

  def remove_follower(self, follower: TrailFollowElement):
    """Remove a follower of the trail"""
    if self.followers:
      self.followers.remove(follower)
      self.__total_size -= follower.size
      self.adapt_trail()

  def adapt_trail(self):
    """
    Automatically adapt the trail. \n
    Must be used instead of .increase_trail() and .decrease_trail().
    """
    delta = self.get_total_size() + 1 - len(self.trail)

    if delta > 0:
      away_from = self.trail[self._wrapped(self.__i - 2)] if len(self.trail) > 1 else self.leader.pos
      self.increase_trail(self.__i, delta, self.trail[self._wrapped(self.__i - 1)], away_from)
    elif delta < 0: self.decrease_trail(-delta)

  def increase_trail(self, at: int, amount: int, position: Vector2, away_from: Vector2):
    """
    Increase the trail 'at' an index, of an 'amount' of points with a dest 'position'
    and an 'await_from' position.
    """
    if self.__i >= at: self.__i += amount
    offset = position - away_from

    for i in range(amount):
      position = position + offset
      self.trail.insert(at+i, position)

  def decrease_trail(self, amount: int):
    """Remove an 'amount' of points at end of the trail"""
    self.trail = [
      self.trail[i] for i in range(self.__i - len(self.trail), self.__i - amount)
    ]
    self.__i = 0

  def get_size(self, follower: TrailFollowElement) -> int:
    """Get the size of a follower (in the trail)"""
    return int((follower.size + self.get_distance()) / self.get_distance() * 2)

  def get_size_precise(self, follower: TrailFollowElement) -> float:
    return (2 * follower.size + self.get_distance()) / self.get_distance()

  def get_distance(self) -> int:
    """Security to never get a distance less than 0"""
    if self.distance < 1: self.distance = 1
    return self.distance

  def get_total_size(self) -> int:
    """Get the total size of the trail"""
    return int(self.get_size(self.leader) + sum(map(lambda f: self.get_size(f), self.followers)))

  def get_leader_index(self):
    """Get the leader index in the trail"""
    return self.__i

  def _wrapped(self, i: int) -> int:
    """Cyclic index of the trail"""
    return i % len(self.trail)
