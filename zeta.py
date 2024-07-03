# You can use any other library that includes standard Vector things
from pygame import Vector2


class TrailElement:
  def __init__(self, pos: Vector2, size: float):
    self.pos = pos
    self.size = size


class Trail:
  def __init__(self, distance: float, leader: TrailElement, precise=False, stack=False):
    self.leader = leader
    self.followers: list[TrailElement] = []
    self.trail = [self.leader.pos]
    self.distance = distance
    self.__last_distance = self.distance
    self.__total_size = self.leader.size
    self.__i = 0
    
    if precise: self.update_trail = self.update_trail_precise
    if stack: self.update_pos = self.update_pos_stack

  def update_pos(self, new_pos: Vector2):
    self.check_trail()
    
    self.leader.pos = new_pos
    current_pos = self.trail[self.__i]
    
    while self.trail[self.__i].distance_to(new_pos) >= self.get_distance():
      current_pos = current_pos.move_towards(new_pos, self.get_distance())
      self.__i = self._wrapped(self.__i - 1)
      self.trail[self.__i] = current_pos

    self.update_trail()
    
  def update_pos_stack(self, new_pos: Vector2):
    self.check_trail()
    
    self.leader.pos = new_pos
    current_pos = self.trail[self.__i].move_towards(new_pos, self.get_distance())
    self.__i = self._wrapped(self.__i - 1)
    self.trail[self.__i] = current_pos

    self.update_trail()
    
  def update_trail(self):
    i = self.__i + self.calculate_size(self.leader.size)/2
    tsize = len(self.trail)
    
    for follower in self.followers:
      size = self.calculate_size(follower.size)/2
      i += size
      follower.pos = self.trail[self._wrapped(int(i % tsize))] 
      i += size
  
  def update_trail_precise(self):
    i = self.leader.size + self.get_distance() - self.leader.pos.distance_to(self.trail[self.__i])
    tsize = len(self.trail)
    
    for follower in self.followers:
      i += follower.size
      offset = self.__i + i / self.distance
      follower.pos = Vector2.lerp(  # vvv equivalent of ceil()
        self.trail[self._wrapped(int(-(-(offset % tsize)//1)))],
        self.trail[self._wrapped(int(offset % tsize))] if i >= 0 else self.leader.pos,
        1 - (offset % 1)
      )
      i += follower.size + self.get_distance()

  def check_trail(self):
    total = sum(map(lambda f: f.size, self.followers))
    if self.distance != self.__last_distance or total != self.__total_size:
      self.__last_distance = self.distance
      self.__total_size = total
      self.adapt_trail()    

  def add_follower(self, follower: TrailElement):
    self.followers.append(follower)
    self.__total_size += follower.size
    self.adapt_trail(self.calculate_size(follower.size))

  def pop_follower(self, index: int=-1):
    self.remove_follower(self.followers[index])

  def remove_follower(self, follower: TrailElement):
    if self.followers:
      self.followers.remove(follower)
      self.__total_size -= follower.size
      self.adapt_trail(-self.calculate_size(follower.size))

  def adapt_trail(self, amout: int=0):
    delta = amout if amout != 0 else self.get_total_size() + 1 - len(self.trail)
    
    if delta > 0: 
      away_from = self.trail[self._wrapped(self.__i - 2)] if len(self.trail) > 1 else self.leader.pos
      self.increase_trail(self.__i, delta, self.trail[self._wrapped(self.__i - 1)], away_from)
    elif delta < 0: self.decrease_trail(-delta)

  def increase_trail(self, at: int, amount: int, position: Vector2, away_from: Vector2):
    if self.__i >= at: self.__i += amount
    offset = position - away_from
    
    for i in range(amount): 
      position = position + offset
      self.trail.insert(at+i, position)

  def decrease_trail(self, amount: int):
    # TODO: a refaire, cela n'est pas possible en Java
    self.trail = [
      self.trail[i] for i in range(self.__i - len(self.trail), self.__i - amount)
    ]
    self.__i = 0

  def calculate_size(self, size: float) -> int:
    return int((size + self.get_distance()) / self.get_distance() * 2)
  
  def get_distance(self) -> int:
    if self.distance < 1: self.distance = 1
    return self.distance
  
  def get_total_size(self) -> int:
    return (self.calculate_size(self.leader.size) + 
            sum(map(lambda f: self.calculate_size(f.size), self.followers)))

  def get_leader_index(self):
    return self.__i

  def _wrapped(self, i: int) -> int:
    return i % len(self.trail)
  