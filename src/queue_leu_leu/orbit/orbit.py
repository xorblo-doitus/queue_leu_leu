# You can use any other library that includes standard Vector things
from pygame import Vector2
import math

SPEED_SCALE = 1 / 8
PI2 = math.pi * 2


def regular_polygon_radius(sides: int, side_len: float) -> float:
  return side_len / (2 * math.sin(math.pi/sides))


class OrbitFollowRing:
  def __init__(self):
    self.angle = 0
    self.radius: float = 1
    self.width: float = 0
    self.sizes: list[float] = []

  def add_angle(self, degree: int):
    self.angle += math.radians(degree)
    self.angle %= PI2
  
  def add_size(self, size: float):
    if 2*size > self.width:
      self.width = 2*size
    self.sizes.append(size)
  
  def clear_sizes(self):
    if self.sizes: self.sizes.clear()
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
    self.rings: list[OrbitFollowRing] = []
    self.radius = radius
    self.distance = distance
    self.speed = speed
    self.adapt_mode = "approximation" # Temporary as long as both methods exists
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
    if self.adapt_mode == "approximation":
      self.adapt_rings_trough_approximation()
    else:
      self.adapt_rings_trough_regular_polygon()
  
  def adapt_rings_trough_approximation(self):
    """Recalculate the rings"""
    ring = 0
    total_size = 0
    biggest_size = 0
    total_radius = self.radius + self.leader.size + self.distance
    circumference = PI2 * total_radius
    self.get_ring(ring).clear_sizes()

    for f in self.followers:
      if f.size > biggest_size:
        total_radius += f.size - biggest_size
        biggest_size = f.size
        # circumference = PI2 * total_radius # FIXME Techniquement, cette ligne est vraie, mais elle empire les chevauchements à cause de l'approximation.
      
      if total_size > circumference:
        self.get_ring(ring).radius = total_radius
        total_radius += self.distance + self.get_ring(ring).width # Add processed ring's width
        ring += 1
        circumference = PI2 * total_radius
        total_size = 0
        biggest_size = 0
        self.get_ring(ring).clear_sizes()

      total_size += 2*f.size + self.distance
      self.get_ring(ring).add_size(f.size)
    
    self.get_ring(ring).radius = total_radius
    
    # Remove empty rings
    ring += 1
    for _ in range(len(self.rings) - ring):
      self.rings.pop(ring)
  
  def adapt_rings_trough_regular_polygon(self):
    """Recalculate the rings"""
    for ring in self.rings:
      ring.clear_sizes()
    
    # Tracking variables
    ring_i = 0
    total_radius = self.radius + self.leader.size + self.distance
    followers_to_add: list[OrbitFollowElement] = self.followers[::-1]
    
    # Ring specific variables
    buffered_followers: list[OrbitFollowElement] = []
    longest_side: float = 0
    biggest_size: float = 0
    second_biggest_size: float = 0
  
    while followers_to_add:
      buffered_followers.append(followers_to_add.pop())
      
      current_size = buffered_followers[-1].size
      
      if current_size > biggest_size:
        second_biggest_size = biggest_size
        biggest_size = current_size
      
      if len(buffered_followers) > 1:
        longest_side = max(longest_side, current_size + buffered_followers[-2].size + self.distance)
      
      overfits = (
        len(buffered_followers) > 2
        and regular_polygon_radius(len(buffered_followers), longest_side) > total_radius + biggest_size
      )
      
      if overfits or not followers_to_add:
        if overfits:
          # Unbuffer the last buffered follower
          followers_to_add.append(buffered_followers.pop())
          if followers_to_add[-1].size > current_size: # Don't use min() it won't work in every case
            biggest_size = second_biggest_size
          # Don't need to update longest_side.
        
        # Create the new ring with every buffered followers
        ring = self.get_ring(ring_i)
        ring.width = 2*biggest_size
        ring.radius = total_radius + biggest_size
        ring.sizes = [f.size for f in buffered_followers]
        
        # Progress
        total_radius += 2*biggest_size + self.distance
        ring_i += 1
        
        # Clean up variables
        buffered_followers.clear()
        biggest_size = 0
        second_biggest_size = 0
        longest_side = 0
        
    
    # Remove empty rings
    self.rings = self.rings[:ring_i]
  
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
    self.adapt_rings()

  def pop_follower(self, index: int=-1):
    self.remove_follower(self.followers[index])

  def remove_follower(self, follower: OrbitFollowElement):
    """Remove a follower of the rings"""
    if self.followers:
      self.followers.remove(follower)
      self.adapt_rings()
  
  def get_ring(self, i: int) -> OrbitFollowRing:
    """Create missing rings if needed and return the requested one"""
    for _ in range(i-len(self.rings)+1):
      self.rings.append(OrbitFollowRing())
    return self.rings[i]
