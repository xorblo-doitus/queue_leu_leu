# You can use any other library that includes standard Vector things
from pygame import Vector2
import math

SPEED_SCALE = 1 / 8
PI2 = math.pi * 2
INF = float("inf")


def advance_on_circle(radius: float, progress: float) -> float:
  intermediary = progress/(2*radius)
  
  # This can rarely happen if follower spacing is higher than ring spacing
  if intermediary < -1 or intermediary > 1:
    return INF
  
  return 2 * math.asin(intermediary)

def regular_polygon_radius(sides: int, side_len: float) -> float:
  return side_len / (2 * math.sin(math.pi/sides))


class OrbitFollowRing:
  def __init__(self):
    self.angle = 0
    self.radius: float = 1
    self.width: float = 0
    self.angles: list[float] = []

  def add_angle(self, degree: int):
    self.angle += math.radians(degree)
    self.angle %= PI2


class OrbitFollowElement:
  def __init__(self, pos: Vector2, size: float):
    self.pos = pos
    self.size = size


class OrbitFollow:
  MODE_EVEN_SPACING = 1
  MODE_EVEN_PLACEMENT = 2
  mode_names = {MODE_EVEN_SPACING: "Even spacing", MODE_EVEN_PLACEMENT: "Even placement"}
  
  def __init__(self, follower_spacing: float, ring_spacing: float, speed: float, leader: OrbitFollowElement):
    """
    :param distance: distance between followers
    :param radius: minimum radius between rings
    :param leader: the leader
    """
    self.leader = leader
    self.followers: list[OrbitFollowElement] = []
    self.rings: list[OrbitFollowRing] = []
    self.ring_spacing = ring_spacing
    self.follower_spacing = follower_spacing
    self.speed = speed
    self.mode = OrbitFollow.MODE_EVEN_SPACING
    self.__last_radius = self.ring_spacing
    self.__last_distance = self.follower_spacing
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
      if not ring.angles: continue

      angle_shift = ring.angle
      step = PI2 / len(ring.angles)

      for angle in ring.angles:
        self.followers[i].pos = self.leader.pos + Vector2(math.cos(angle_shift + angle), math.sin(angle_shift + angle)) * ring.radius
        angle += step
        i += 1
  
  def adapt_rings(self):
    if self.mode == OrbitFollow.MODE_EVEN_PLACEMENT:
      self.adapt_rings_even_placement()
    else:
      self.adapt_rings_even_spacing()
  
  def adapt_rings_even_spacing(self):
    for ring in self.rings:
      ring.angles.clear()
    
    # Tracking variables
    ring_i = 0
    total_radius = self.ring_spacing + self.leader.size
    to_add: list[OrbitFollowElement] = self.followers[::-1]
    
    # Ring specific variables
    in_ring: list[OrbitFollowElement] = []
    current_angle = 0
    biggest_size: float = 0
    second_biggest_size: float = 0
    
    while to_add:
      in_ring.append(to_add.pop())
      current_size = in_ring[-1].size
      
      if current_size > biggest_size:
        second_biggest_size = biggest_size
        biggest_size = current_size
        
        # Recalculate previous angles
        current_angle = 0
        for i in range(len(in_ring) - 2):
          current_angle += advance_on_circle(total_radius + biggest_size, in_ring[i].size + self.follower_spacing + in_ring[i+1].size)
      
      if len(in_ring) >= 2:
        current_angle += advance_on_circle(total_radius + biggest_size, in_ring[-2].size + self.follower_spacing + in_ring[-1].size)
      
      overfits = (
        len(in_ring) > 2
        and current_angle + advance_on_circle(total_radius + biggest_size, in_ring[-1].size + self.follower_spacing + in_ring[0].size) > PI2
      )
      
      if overfits or not to_add:
        if overfits:
          # Remove the follower who is overflowing
          to_add.append(in_ring.pop())
          if to_add[-1].size > current_size: # Don't use min() it won't work in every case
            biggest_size = second_biggest_size
            current_angle = 0
            for i in range(len(in_ring) - 2):
              current_angle += advance_on_circle(total_radius + biggest_size, in_ring[i].size + self.follower_spacing + in_ring[i+1].size)
          elif len(in_ring) >= 1:
            current_angle -= advance_on_circle(total_radius + biggest_size, in_ring[-1].size + self.follower_spacing + to_add[-1].size)
        
        current_angle += advance_on_circle(total_radius + biggest_size, in_ring[-1].size + self.follower_spacing + in_ring[0].size)
        
        # Create the new ring with every selected followers
        ring = self.get_ring(ring_i)
        ring.radius = total_radius + biggest_size
        ring.width = 2*biggest_size
        bonus_angle = (PI2 - current_angle) / len(in_ring)
        ring.angles.append(0)
        for i in range(1, len(in_ring)):
          ring.angles.append(ring.angles[-1] + bonus_angle + advance_on_circle(ring.radius, in_ring[i-1].size + self.follower_spacing + in_ring[i].size))
        
        # Progress
        total_radius += 2*biggest_size + self.follower_spacing
        ring_i += 1
        
        # Clean up variables
        in_ring.clear()
        current_angle = 0
        biggest_size = 0
        second_biggest_size = 0
    
    # Remove empty rings
    self.rings = self.rings[:ring_i]
  
  def adapt_rings_even_placement(self):
    """Recalculate the rings"""
    for ring in self.rings:
      ring.angles.clear()
    
    # Tracking variables
    ring_i = 0
    total_radius = self.ring_spacing + self.leader.size
    to_add: list[OrbitFollowElement] = self.followers[::-1]
    
    # Ring specific variables
    in_ring: list[OrbitFollowElement] = []
    longest_side: float = 0
    biggest_size: float = 0
    second_biggest_size: float = 0
  
    while to_add:
      in_ring.append(to_add.pop())
      current_size = in_ring[-1].size
      
      if current_size > biggest_size:
        second_biggest_size = biggest_size
        biggest_size = current_size
      
      if len(in_ring) > 1:
        longest_side = max(longest_side, current_size + in_ring[-2].size + self.follower_spacing)
      
      overfits = (
        len(in_ring) > 2
        and regular_polygon_radius(len(in_ring), longest_side) > total_radius + biggest_size
      )
      
      if overfits or not to_add:
        if overfits:
          # Remove the follower who is overflowing
          to_add.append(in_ring.pop())
          if to_add[-1].size > current_size: # Don't use min() it won't work in every case
            biggest_size = second_biggest_size
            # Don't need to update longest_side.
        
        # Create the new ring with every selected followers
        ring = self.get_ring(ring_i)
        ring.radius = total_radius + biggest_size
        ring.width = 2*biggest_size
        step = PI2 / len(in_ring)
        ring.angles = [step * i for i in range(len(in_ring))]
        
        # Progress
        total_radius += 2*biggest_size + self.follower_spacing
        ring_i += 1
        
        # Clean up variables
        in_ring.clear()
        biggest_size = 0
        second_biggest_size = 0
        longest_side = 0
    
    # Remove empty rings
    self.rings = self.rings[:ring_i]

  def check_rings(self):
    """Recalculate the rings if .radius, .distance or a follower size has been changed"""
    total = sum(map(lambda f: f.size, self.followers))
    if (self.ring_spacing != self.__last_radius or 
        self.follower_spacing != self.__last_distance or 
        total != self.__total_size
    ):
      self.ring_spacing = max(self.ring_spacing, 1)
      self.__last_radius = self.ring_spacing
      self.follower_spacing = max(self.follower_spacing, 0)
      self.__last_distance = self.follower_spacing
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