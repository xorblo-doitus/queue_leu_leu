# You can use any other library that includes standard Vector things
from pygame import Vector2
import math

SPEED_SCALE = 1 / 8
PI2 = math.pi * 2


def advance_on_circle(radius: float, progress: float, default: float=PI2) -> float:
  alpha = progress/(2*radius)
  # This can rarely happen if follower spacing is higher than ring spacing
  if not -1<=alpha<=1: return default
  return 2 * math.asin(alpha)

def regular_polygon_radius(sides: int, size: float) -> float:
  return size / (2 * math.sin(math.pi/sides))


class OrbitFollowRing:
  def __init__(self):
    self.angle = 0
    self.radius = 1
    self.angles: list[float] = []

  def add_angle(self, degree: int):
    self.angle += math.radians(degree)
    self.angle %= PI2


class OrbitFollowElement:
  def __init__(self, pos: Vector2, size: float):
    self.pos = pos
    self.size = size


class OrbitFollow:
  def __init__(self, spacing: float, radius: float, speed: float, leader: OrbitFollowElement, precise=True):
    """
    :param spacing: distance between followers
    :param radius: minimum radius between rings
    :param speed: angle (in deg) to add each updates
    :param leader: the leader
    :param precise: if True, followers will be distributed by their sizes and not equally, on the ring
    """
    self.leader = leader
    self.followers: list[OrbitFollowElement] = []
    self.rings: list[OrbitFollowRing] = []
    self.radius = radius
    self.spacing = spacing
    self.speed = speed
    self.__last_radius = self.radius
    self.__last_distance = self.spacing
    self.__last_speed = self.speed
    self.__total_size = 0
    
    if precise: self.adapt_rings = self.adapt_rings_precise

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
    ring = 0
    i = 0
    for f in self.followers:
      step = self.rings[ring].angle + self.rings[ring].angles[i]
      f.pos = self.leader.pos + Vector2(math.cos(step), math.sin(step)) * self.rings[ring].radius
      
      i += 1
      if i >= len(self.rings[ring].angles):
        ring += 1
        i = 0

  def adapt_rings(self):
    """Recalculate the rings"""
    # Clear rings
    for ring in self.rings: ring.angles.clear()

    ring = longest_side = ii = 0
    biggest_size = self.leader.size
    total_radius = self.radius + biggest_size
    max_i = len(self.followers) - 1
    
    for i, f in enumerate(self.followers):
      ii += 1
      biggest_size = max(biggest_size, f.size)
      
      if ii > 1: longest_side = max(longest_side, f.size + self.followers[i-1].size + self.spacing)
      if ((ii > 2 and regular_polygon_radius(ii, longest_side) > total_radius + biggest_size)
          or i >= max_i):
        self.get_ring(ring).radius = total_radius + biggest_size
        step = PI2 / ii
        self.get_ring(ring).angles = [step * i for i in range(ii)]
        total_radius += self.radius + 2*biggest_size
        ring += 1
        biggest_size = longest_side = ii = 0
        
    # Remove empty rings
    self.rings = self.rings[:ring]

  def adapt_rings_precise(self):
    """Recalculate the rings"""
    for ring in self.rings: ring.angles.clear()
    
    ring_i = angle = biggest_size = last_biggest_size = 0
    total_radius = self.radius + self.leader.size
    to_add: list[float] = list(map(lambda f: f.size, self.followers[::-1]))
    in_ring: list[float] = []
    
    while to_add:
      in_ring.append(to_add.pop())

      if in_ring[-1] > biggest_size:
        last_biggest_size = biggest_size
        biggest_size = in_ring[-1]
        
        # Recalculate previous angles
        angle = 0
        for i in range(len(in_ring) - 2):
          angle += advance_on_circle(total_radius + biggest_size, in_ring[i] + self.spacing + in_ring[i+1])
      
      if len(in_ring) >= 2:
        angle += advance_on_circle(total_radius + biggest_size, in_ring[-2] + self.spacing + in_ring[-1])
      
      overfits = (
        len(in_ring) > 2 and
        angle + advance_on_circle(total_radius + biggest_size, in_ring[-1] + self.spacing + in_ring[0]) > PI2
      )
      
      if overfits or not to_add:
        if overfits:
          # Remove the follower who is overflowing
          to_add.append(in_ring.pop())
          
          if to_add[-1] > in_ring[-1]:
            biggest_size = last_biggest_size
            angle = 0
            for i in range(len(in_ring) - 2):
              angle += advance_on_circle(total_radius + biggest_size, in_ring[i] + self.spacing + in_ring[i+1])
          
          elif len(in_ring) >= 1:
            angle -= advance_on_circle(total_radius + biggest_size, in_ring[-1] + self.spacing + to_add[-1])
        
        angle += advance_on_circle(total_radius + biggest_size, in_ring[-1] + self.spacing + in_ring[0])
        
        # Create the new ring with every selected followers
        ring = self.get_ring(ring_i)
        ring.radius = total_radius + biggest_size
        step = (PI2 - angle) / len(in_ring)
        ring.angles.append(0)
        for i in range(1, len(in_ring)):
          ring.angles.append(ring.angles[-1] + step + advance_on_circle(ring.radius, in_ring[i-1] + self.spacing + in_ring[i]))
        
        total_radius += 2*biggest_size + self.spacing
        ring_i += 1
        angle = biggest_size = last_biggest_size = 0
    
    # Remove empty rings
    self.rings = self.rings[:ring_i]
  
  def check_rings(self):
    """Recalculate the rings if .radius, .distance or a follower size has been changed"""
    total = sum(map(lambda f: f.size, self.followers))
    if (self.radius != self.__last_radius or 
        self.spacing != self.__last_distance or 
        total != self.__total_size
    ):
      self.radius = max(self.radius, 1)
      self.__last_radius = self.radius
      self.spacing = max(self.spacing, 0)
      self.__last_distance = self.spacing
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