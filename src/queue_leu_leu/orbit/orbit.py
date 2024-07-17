# You can use any other library that includes standard Vector things
from pygame import Vector2
import math

SPEED_SCALE = 1 / 8
PI2 = math.pi * 2


def advance_on_circle(radius: float, distance: float, fallback: float=PI2) -> float:
  alpha = distance/(2*radius)
  # This can rarely happen if follower spacing is higher than ring spacing
  if not -1<=alpha<=1: return fallback
  return 2 * math.asin(alpha)

def regular_polygon_radius(sides: int, side_lenght: float) -> float:
  return side_lenght / (2 * math.sin(math.pi/sides))

def Vector2_from_polar(magnitude: float, angle_rad: float) -> Vector2:
  return magnitude * Vector2(math.cos(angle_rad), math.sin(angle_rad))



class OrbitFollowRing:
  def __init__(self):
    self.angle = 0
    self.radius: float = 1
    self.angles: list[float] = []

  def add_angle(self, degree: int):
    self.angle += math.radians(degree)
    self.angle %= PI2


class OrbitFollowElement:
  def __init__(self, pos: Vector2, size: float):
    self.pos = pos
    self.size = size


class OrbitFollow:
  def __init__(self, follower_spacing: float, ring_spacing: float, speed: float, leader: OrbitFollowElement, ring_builder: callable = None):
    """
    :param follower_spacing: distance between followers
    :param ring_spacing: minimum distance between rings
    :param speed: angle (in deg) to add each updates
    :param leader: the leader
    :param ring_builder: Set to :py:meth:`adapt_rings_even_spacing` and :py:meth:`adapt_rings_even_placement`.
    """
    self.leader = leader
    self.followers: list[OrbitFollowElement] = []
    self.rings: list[OrbitFollowRing] = []
    self.ring_spacing = ring_spacing
    self.follower_spacing = follower_spacing
    self.speed = speed
    if ring_builder:
      self.adapt_rings: callable = ring_builder
    self.__last_ring_spacing = self.ring_spacing
    self.__last_follower_spacing = self.follower_spacing
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
    follower_i = 0
    
    for ring in self.rings:
      angle_shift = ring.angle

      for angle in ring.angles:
        self.followers[follower_i].pos = self.leader.pos + Vector2_from_polar(ring.radius, angle_shift + angle)
        follower_i += 1
  
  def adapt_rings_even_spacing(self):
    """Place followers with even spacing between them."""
    
    # Tracking variables
    ring_i: int = 0
    total_radius: float = self.ring_spacing + self.leader.size
    to_add: list[float] = [f.size for f in self.followers]
    
    # Ring specific variables
    # in_ring: list[float] = []
    start_i = 0
    current_i = -1
    angle: float = 0
    biggest: float = 0
    previous_biggest: float = 0
    
    while current_i < len(to_add) - 1:
      # in_ring.append(to_add.pop())
      current_i += 1
      current_size: float = to_add[current_i]
      
      if current_size > biggest:
        previous_biggest = biggest
        biggest = current_size
        
        # Recalculate previous angles
        angle = 0
        for i in range(start_i, current_i - 1):
          angle += advance_on_circle(total_radius + biggest, to_add[i] + self.follower_spacing + to_add[i+1])
      
      if current_i - start_i >= 1:
        angle += advance_on_circle(total_radius + biggest, to_add[current_i-1] + self.follower_spacing + current_size)
      
      overfits = (
        current_i - start_i > 1
        and angle + advance_on_circle(total_radius + biggest, current_size + self.follower_spacing + to_add[start_i]) > PI2
      )
      
      if overfits or current_i >= len(to_add) - 1:
        if overfits:
          # Remove the follower who is overflowing
          # to_add.append(in_ring.pop())
          current_i -= 1
          
          if to_add[current_i+1] > current_size: # Don't use min() it won't work in every case
            biggest = previous_biggest
            angle = 0
            for i in range(start_i, current_i - 1):
              angle += advance_on_circle(total_radius + biggest, to_add[i] + self.follower_spacing + to_add[i+1])
          elif current_i - start_i >= 0:
            angle -= advance_on_circle(total_radius + biggest, to_add[current_i] + self.follower_spacing + to_add[current_i+1])
        
        angle += advance_on_circle(total_radius + biggest, to_add[current_i] + self.follower_spacing + to_add[start_i])
        
        # Create the new ring with every selected followers
        ring = self.get_ring(ring_i)
        ring.radius = total_radius + biggest
        bonus_angle = (PI2 - angle) / (current_i - start_i + 1)
        ring.angles.clear()
        ring.angles.append(0)
        for i in range(start_i + 1, current_i + 1):
          ring.angles.append(ring.angles[-1] + bonus_angle + advance_on_circle(ring.radius, to_add[i-1] + self.follower_spacing + to_add[i]))
        
        # Progress
        total_radius += 2*biggest + self.follower_spacing
        ring_i += 1
        
        # Clean up variables
        # in_ring.clear()
        start_i = current_i + 1
        current_i = start_i - 1
        angle = 0
        biggest = 0
        previous_biggest = 0
      
    # Remove empty rings
    self.rings = self.rings[:ring_i]
  
  def adapt_rings_even_placement(self):
    """Place followers with even spacing between their centers."""
    
    # Tracking variables
    ring_i: int = 0
    total_radius: float = self.ring_spacing + self.leader.size
    to_add: list[float] = [f.size for f in self.followers[::-1]]
    
    # Ring specific variables
    in_ring: list[float] = []
    longest_side: float = 0
    biggest: float = 0
    previous_biggest: float = 0
  
    while to_add:
      in_ring.append(to_add.pop())
      current_size = in_ring[-1]
      
      if current_size > biggest:
        previous_biggest = biggest
        biggest = current_size
      
      if len(in_ring) > 1:
        longest_side = max(longest_side, current_size + in_ring[-2] + self.follower_spacing)
      
      overfits = (
        len(in_ring) > 2
        and regular_polygon_radius(len(in_ring), longest_side) > total_radius + biggest
      )
      
      if overfits or not to_add:
        if overfits:
          # Remove the follower who is overflowing
          to_add.append(in_ring.pop())
          
          if to_add[-1] > current_size: # Don't use min() it won't work in every case
            biggest = previous_biggest
            # Don't need to update longest_side.
        
        # Create the new ring with every selected followers
        ring = self.get_ring(ring_i)
        ring.radius = total_radius + biggest
        step = PI2 / len(in_ring)
        ring.angles = [step * i for i in range(len(in_ring))]
        
        # Progress
        total_radius += 2*biggest + self.follower_spacing
        ring_i += 1
        
        # Clean up variables
        in_ring.clear()
        biggest = 0
        previous_biggest = 0
        longest_side = 0
    
    # Remove empty rings
    self.rings = self.rings[:ring_i]

  adapt_rings = adapt_rings_even_spacing

  def check_rings(self):
    """Recalculate the rings if .radius, .distance or a follower size has been changed"""
    total = sum(map(lambda f: f.size, self.followers))
    if (self.ring_spacing != self.__last_ring_spacing or 
        self.follower_spacing != self.__last_follower_spacing or 
        total != self.__total_size
    ):
      self.ring_spacing = max(self.ring_spacing, 1)
      self.__last_ring_spacing = self.ring_spacing
      self.follower_spacing = max(self.follower_spacing, 0)
      self.__last_follower_spacing = self.follower_spacing
      self.__total_size = total
      self.adapt_rings()
    
    # Clamp the speed
    if self.__last_speed != self.speed:
      self.speed = int(max(min(self.speed, 180 / SPEED_SCALE), -180 / SPEED_SCALE))
      self.__last_speed = self.speed

  def add_follower(self, follower: OrbitFollowElement):
    """Add a new follower in the rings"""
    self.followers.append(follower)
    
    # Adapt rings
    self.__total_size += follower.size
    self.adapt_rings()

  def pop_follower(self, index: int=-1):
    removed = self.followers.pop(index)
    # Adapt rings
    self.__total_size -= removed.size
    self.adapt_rings()

  def remove_follower(self, follower: OrbitFollowElement):
    """Remove a follower of the rings"""
    self.pop_follower(self.followers.index(follower))
  
  def get_ring(self, i: int) -> OrbitFollowRing:
    """Create missing rings if needed and return the requested one"""
    for _ in range(i-len(self.rings)+1):
      self.rings.append(OrbitFollowRing())
    return self.rings[i]