# You can use any other library that includes standard Vector things
from pygame import Vector2
import math


SPEED_SCALE = 1 / 8


def advance_on_circle(radius: float, chord: float, fallback: float=math.tau) -> float:
  alpha = chord / (2*radius)
  if not -1 <= alpha <=1: return fallback
  return 2 * math.asin(alpha)

def regular_polygon_radius(sides: int, side: float) -> float:
  return side / (2 * math.sin(math.pi/sides))


class OrbitFollowRing:
  def __init__(self):
    self.angle = 0
    self.radius = 1
    self.angles: list[float] = []

  def add_angle(self, degree: int):
    self.angle += math.radians(degree)
    self.angle %= math.tau


class OrbitFollowElement:
  def __init__(self, pos: Vector2, size: float):
    self.pos = pos
    self.size = size


class OrbitFollow:
  def __init__(self, spacing: float, gap: float, speed: float, leader: OrbitFollowElement, adapter: 'function'=None):
    """
    :param spacing: distance between followers
    :param gap: minimum distance between rings
    :param speed: angle (in deg) to add each updates
    :param leader: the leader
    :param adapter: Set to :py:meth:`adapt_rings_even_spacing`, :py:meth:`adapt_rings_even_placement` or :py:meth:`adapt_rings_even_spacing_no_retrocorrection`.
    """
    self.leader = leader
    self.followers: list[OrbitFollowElement] = []
    self.rings: list[OrbitFollowRing] = []
    self.gap = gap
    self.spacing = spacing
    self.speed = speed
    self.__last_gap = self.gap
    self.__last_spacing = self.spacing
    self.__last_speed = self.speed
    self.__total_size = 0

    if adapter: self.adapt_rings = adapter
    
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
        shift = ring.angle + angle
        self.followers[i].pos = self.leader.pos + Vector2(math.cos(shift), math.sin(shift)) * ring.radius
        i += 1
  
  def adapt_compact_approx(self):
    """
    Place followers with even spacing between them.
    This mode is faster than :py:meth:`adapt_compact`. \n
    WARNING: this method can create overlapping followers.
    """
    in_ring = ring = angle = 0
    biggest = self.leader.size
    total_radius = self.gap + biggest
    max_i = len(self.followers) - 1    
    # Cache
    chords = [self.followers[i].size + self.spacing + self.followers[i+1].size 
              for i in range(max_i)] 

    for i, f in enumerate(self.followers):
      in_ring += 1
      radius = total_radius + biggest
      
      if f.size > biggest:
        biggest = f.size
        radius = total_radius + biggest
        # Recalculate previous angles
        angle = 0
        for ii in range(i-in_ring+1, i-1):
          angle += advance_on_circle(radius, chords[ii])

      if in_ring >= 2: angle += advance_on_circle(radius, chords[i-1])
      
      total_angle = angle + advance_on_circle(radius, f.size + self.spacing + self.followers[i-in_ring+1].size)
      if (in_ring > 2 and total_angle > math.tau) or i >= max_i:
        angle = total_angle
        
        r = self.get_ring(ring)
        r.radius = radius
        extra = (math.tau - angle) / in_ring
        r.angles = [0]
        for ii in range(i-in_ring+1, i):
          r.angles.append(r.angles[-1] + extra + advance_on_circle(r.radius, chords[ii]))
        
        total_radius += self.gap + 2*biggest
        ring += 1
        in_ring = angle = biggest = 0
        
    # Remove empty rings
    self.rings = self.rings[:ring]
  
  def adapt_compact(self):
    """
    Place followers with even spacing between them.
    This mode is slower than :py:meth:`adapt_compact_approx`.
    """
    # Caches
    to_add = [f.size for f in self.followers]
    chords = [to_add[i] + self.spacing + to_add[i+1] for i in range(len(to_add)-1)] # at i is stored chord between follower i and i+1.

    ring_i = start_i = angle = biggest = last_biggest = 0
    end_i = -1
    total_radius = self.gap + self.leader.size
    
    while end_i < len(to_add) - 1:
      end_i += 1
      size = to_add[end_i]
      radius = total_radius + biggest
      
      if size > biggest:
        last_biggest = biggest
        biggest = size
        radius = total_radius + biggest
        
        # Recalculate previous angles
        angle = 0
        for i in range(start_i, end_i - 1):
          angle += advance_on_circle(radius, chords[i])
      
      if end_i - start_i >= 1:
        angle += advance_on_circle(radius, chords[end_i-1])
      
      overfits = (
        end_i - start_i > 1
        and angle + advance_on_circle(radius, size + self.spacing + to_add[start_i]) > math.tau
      )
      
      if overfits or end_i >= len(to_add) - 1:
        if overfits:
          # Remove the follower who is overflowing
          end_i -= 1
          
          if to_add[end_i+1] > size: # Don't use min() it won't work in every case
            biggest = last_biggest
            radius = total_radius + biggest
            angle = 0
            for i in range(start_i, end_i - 1):
              angle += advance_on_circle(radius, chords[i])
          elif end_i - start_i >= 0:
            angle -= advance_on_circle(radius, chords[end_i])
        
        angle += advance_on_circle(radius, to_add[end_i] + self.spacing + to_add[start_i])
        
        # Create the new ring with every selected followers
        ring = self.get_ring(ring_i)
        ring.radius = radius
        extra = (math.tau - angle) / (end_i - start_i + 1)
        angles = [0]
        for i in range(start_i, end_i):
          angles.append(angles[-1] + extra + advance_on_circle(radius, chords[i]))
        ring.angles = angles
        
        # Progress
        total_radius += 2*biggest + self.gap
        ring_i += 1
        
        # Clean up variables
        angle = biggest = last_biggest = 0
        start_i = end_i + 1
    
    # Remove empty rings
    self.rings = self.rings[:ring_i]
  
  def adapt_fast(self):
    """
    Place followers with even spacing between their centers.
    This mode is the faster.
    """
    ring_i = longest_side = biggest = last_biggest = 0
    total_radius = self.gap + self.leader.size
    to_add = [f.size for f in self.followers[::-1]]
    in_ring = []
  
    while to_add:
      in_ring.append(to_add.pop())
      size = in_ring[-1]
      
      if size > biggest:
        last_biggest = biggest
        biggest = size
      
      if len(in_ring) > 1:
        longest_side = max(longest_side, size + in_ring[-2] + self.spacing)
      
      overfits = (
        len(in_ring) > 2
        and regular_polygon_radius(len(in_ring), longest_side) > total_radius + biggest
      )
      
      if overfits or not to_add:
        if overfits:
          # Remove the follower who is overflowing
          to_add.append(in_ring.pop())
          
          if to_add[-1] > size: # Don't use min() it won't work in every case
            biggest = last_biggest
            # Don't need to update longest_side.
        
        # Create the new ring with every selected followers
        ring = self.get_ring(ring_i)
        ring.radius = total_radius + biggest
        step = math.tau / len(in_ring)
        ring.angles = [step * i for i in range(len(in_ring))]
        
        # Progress
        total_radius += 2*biggest + self.gap
        ring_i += 1
        
        # Clean up variables
        in_ring.clear()
        biggest = last_biggest = longest_side = 0
    
    # Remove empty rings
    self.rings = self.rings[:ring_i]

  adapt_rings = adapt_compact

  def check_rings(self):
    """Recalculate the rings if .gap, .spacing or a follower size has been changed"""
    total = sum(f.size for f in self.followers)
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
