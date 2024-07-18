# You can use any other library that includes standard Vector things
from pygame import Vector2
import math

SPEED_SCALE = 1 / 8
PI2 = math.pi * 2


def advance_on_circle(radius: float, chord: float, fallback: float=PI2) -> float:
  alpha = chord/(2*radius)
  # This can rarely happen if follower spacing is higher than ring spacing
  if not -1<=alpha<=1: return fallback
  return 2 * math.asin(alpha)

def regular_polygon_radius(sides: int, side: float) -> float:
  return side / (2 * math.sin(math.pi/sides))

def Vector2_polar(magnitude: float, angle_rad: float) -> Vector2:
  return magnitude * Vector2(math.cos(angle_rad), math.sin(angle_rad))


class OrbitFollowRing:
  def __init__(self):
    self.angle: float = 0
    self.radius: float = 1
    self.angles: list[float] = []

  def add_angle(self, degree: int):
    self.angle += math.radians(degree)
    self.angle %= PI2


class OrbitFollowElement:
  def __init__(self, pos: Vector2, size: float):
    self.pos: Vector2 = pos
    self.size: float = size


class OrbitFollow:
  def __init__(self, spacing: float, gap: float, speed: float, leader: OrbitFollowElement, adapter: callable = None):
    """
    :param spacing: distance between followers
    :param gap: minimum distance between rings
    :param speed: angle (in deg) to add each updates
    :param leader: the leader
    :param adapter: Set to :py:meth:`adapt_rings_even_spacing`, :py:meth:`adapt_rings_even_placement` or :py:meth:`adapt_rings_even_spacing_no_retrocorrection`.
    """
    self.leader: OrbitFollowElement = leader
    self.followers: list[OrbitFollowElement] = []
    self.rings: list[OrbitFollowRing] = []
    self.gap: float = gap
    self.spacing: float = spacing
    self.speed: float = speed
    self.__last_gap: float = self.gap
    self.__last_spacing: float = self.spacing
    self.__last_speed: float = self.speed
    self.__total_size: float = 0

    if adapter: self.adapt_rings: callable = adapter
    
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
      for angle in ring.angles:
        self.followers[i].pos = self.leader.pos + Vector2_polar(ring.radius, ring.angle + angle)
        i += 1
  
  def adapt_compact_approx(self):
    """
    Place followers with even spacing between them.
    This mode is faster than :py:meth:`adapt_compact`.
    WARNING: this method can create overlapping followers.
    """
    for ring in self.rings: ring.angles.clear()

    ring = angle = 0
    biggest = self.leader.size
    total_radius = self.gap + biggest
    max_i = len(self.followers) - 1
    in_ring = []
    
    for i, f in enumerate(self.followers):
      in_ring.append(f.size)
      size = in_ring[-1]
      
      if size > biggest:
        biggest = size
        # Recalculate previous angles
        angle = 0
        for ii in range(len(in_ring) - 2):
          angle += advance_on_circle(total_radius + biggest, in_ring[ii] + self.spacing + in_ring[ii+1])
      
      if len(in_ring) >= 2:
        angle += advance_on_circle(total_radius + biggest, in_ring[-2] + self.spacing + size)
      
      total_angle = angle + advance_on_circle(total_radius + biggest, size + self.spacing + in_ring[0])
      
      if (len(in_ring) > 2 and total_angle > PI2) or i >= max_i:
        angle = total_angle
        
        r = self.get_ring(ring)
        r.radius = total_radius + biggest
        step = (PI2 - angle) / len(in_ring)
        r.angles.append(0)
        for ii in range(1, len(in_ring)):
          r.angles.append(r.angles[-1] + step + advance_on_circle(r.radius, in_ring[ii-1] + self.spacing + in_ring[ii]))
        
        total_radius += self.gap + 2*biggest
        ring += 1
        angle = biggest = 0
        in_ring.clear()
        
    # Remove empty rings
    self.rings = self.rings[:ring]
  
  # WARN WARNING TODO FIXME DEPRECATED (potentially) This method was rewrote in another branch while waiting for profiling. If a performance increase is confirmed, it will be replaced.
  def adapt_compact(self):
    """
    Place followers with even spacing between them.
    This mode is slower than :py:meth:`adapt_compact_approx`.
    """
    
    # Tracking variables
    ring_i: int = 0
    total_radius: float = self.gap + self.leader.size
    to_add: list[float] = [f.size for f in self.followers[::-1]]
    
    # Per ring variables
    in_ring: list[float] = []
    angle: float = 0
    biggest: float = 0
    last_biggest: float = 0
    
    while to_add:
      in_ring.append(to_add.pop())
      size: float = in_ring[-1]
      
      if size > biggest:
        last_biggest = biggest
        biggest = size
        
        # Recalculate previous angles
        angle = 0
        for i in range(len(in_ring) - 2):
          angle += advance_on_circle(total_radius + biggest, in_ring[i] + self.spacing + in_ring[i+1])
      
      if len(in_ring) >= 2:
        angle += advance_on_circle(total_radius + biggest, in_ring[-2] + self.spacing + size)
      
      overfits = (
        len(in_ring) > 2
        and angle + advance_on_circle(total_radius + biggest, size + self.spacing + in_ring[0]) > PI2
      )
      
      if overfits or not to_add:
        if overfits:
          # Remove the follower who is overflowing
          to_add.append(in_ring.pop())
          
          if to_add[-1] > size: # Don't use min() it won't work in every case
            biggest = last_biggest
            angle = 0
            for i in range(len(in_ring) - 2):
              angle += advance_on_circle(total_radius + biggest, in_ring[i] + self.spacing + in_ring[i+1])
          
          elif len(in_ring) >= 1:
            angle -= advance_on_circle(total_radius + biggest, in_ring[-1] + self.spacing + to_add[-1])
        
        angle += advance_on_circle(total_radius + biggest, in_ring[-1] + self.spacing + in_ring[0])
        
        # Create the new ring with every selected followers
        ring = self.get_ring(ring_i)
        ring.radius = total_radius + biggest
        extra = (PI2 - angle) / len(in_ring)
        ring.angles = [0]
        for i in range(1, len(in_ring)):
          ring.angles.append(ring.angles[-1] + extra + advance_on_circle(ring.radius, in_ring[i-1] + self.spacing + in_ring[i]))
        
        # Progress
        total_radius += 2*biggest + self.gap
        ring_i += 1
        
        # Clean up variables
        angle = biggest = last_biggest = 0
        in_ring.clear()
    
    # Remove empty rings
    self.rings = self.rings[:ring_i]
  
  def adapt_fast(self):
    """
    Place followers with even spacing between their centers.
    This mode is the faster.
    """
    
    # Tracking variables
    ring_i: int = 0
    total_radius: float = self.gap + self.leader.size
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
        longest_side = max(longest_side, current_size + in_ring[-2] + self.spacing)
      
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
        total_radius += 2*biggest + self.gap
        ring_i += 1
        
        # Clean up variables
        in_ring.clear()
        biggest = 0
        previous_biggest = 0
        longest_side = 0
    
    # Remove empty rings
    self.rings = self.rings[:ring_i]

  adapt_rings = adapt_compact

  def check_rings(self):
    """Recalculate the rings if .radius, .distance or a follower size has been changed"""
    total = sum(map(lambda f: f.size, self.followers))
    if (self.gap != self.__last_gap or 
        self.spacing != self.__last_spacing or 
        total != self.__total_size
    ):
      self.gap = max(self.gap, 1)
      self.__last_gap = self.gap
      self.spacing = max(self.spacing, 0)
      self.__last_spacing = self.spacing
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
  
  # FIXME Unused
  # def get_distance(self, i: int, between: int):
  #   return self.followers[i].size + self.spacing + self.followers[i+between].size