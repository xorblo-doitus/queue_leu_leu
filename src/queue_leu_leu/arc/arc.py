# You can use any other library that includes standard Vector things
from pygame import Vector2
import math

PI2 = 2 * math.pi


def advance_on_circle(radius: float, chord: float, fallback: float=PI2) -> float:
  alpha: float = chord / (2*radius)
  if not -1 <= alpha <=1: return fallback
  return 2 * math.asin(alpha)

def Vector2_polar(magnitude: float, angle_rad: float) -> Vector2:
  return magnitude * Vector2(math.cos(angle_rad), math.sin(angle_rad))

def get_edge_angle(radius: float, distance: float, fallback: float=0) -> float:
  alpha = distance/radius
  if not -1<=alpha<=1: return fallback
  return math.asin(alpha)


class ArcFollowRing:
  def __init__(self):
    self.radius = 1
    self.angles: list[float] = []


class ArcFollowElement:
  def __init__(self, pos: Vector2, size: float):
    self.pos = pos
    self.size = size


class ArcFollow:
  def __init__(self, spacing: float, gap: float, max_angle_deg: float, leader: ArcFollowElement, strong: bool=False, uniform: bool=True):
    """
    :param spacing: distance between followers
    :param gap: minimum distance between rings
    :param max_angle: max angle each side, at back of the leader
    :param leader: the leader
    """
    self.leader = leader
    self.followers: list[ArcFollowElement] = []
    self.rings: list[ArcFollowRing] = []
    self.spacing = spacing
    self.gap = gap
    self.max_angle_deg = max_angle_deg
    self.rotation = 0
    self.strong = strong
    self.uniform = uniform
    self.__last_max_angle = self.max_angle
    self.__last_gap = self.gap
    self.__last_spacing = self.spacing
    self.__total_size = 0

  @property
  def max_angle_deg(self) -> float:
    """WARNING: The arc angle is twice this angle"""
    return self.max_angle / math.pi * 90
  
  @max_angle_deg.setter
  def max_angle_deg(self, new: float):
    self.max_angle = new / 90 * math.pi

  @property
  def rotation_deg(self) -> float:
    return math.degrees(self.rotation)
  
  @rotation_deg.setter
  def rotation_deg(self, new: float):
    self.rotation = math.radians(new)

  def update_pos(self, new_pos: Vector2):
    """Update the position of the leader"""
    self.check_rings()
    self.leader.pos = new_pos
    
    # Update followers
    i = 0
    for ring in self.rings:
      for angle in ring.angles:
        self.followers[i].pos = self.leader.pos + Vector2_polar(ring.radius, angle + self.rotation)
        i += 1
  
  def adapt_rings(self):
    """Update arcs and follower placement"""
    # Caches
    to_add = [f.size for f in self.followers]
    chords = [to_add[i] + self.spacing + to_add[i+1] for i in range(len(to_add)-1)] 
    
    ring_i = start_i = last_biggest = 0
    end_i = -1
    total_radius = max(1, self.gap + self.leader.size)
    biggest = to_add[0]
    angle = get_edge_angle(total_radius + biggest, to_add[start_i])
    
    while end_i < len(to_add) - 1:
      end_i += 1
      size = to_add[end_i]
      new_radius = total_radius + biggest
      
      if size > biggest:
        last_biggest = biggest
        biggest = size
        new_radius = total_radius + biggest
        
        # Recalculate previous angles
        angle = get_edge_angle(new_radius, to_add[start_i])
        for i in range(start_i, end_i - 1):
          angle += advance_on_circle(new_radius, chords[i])
      
      if end_i - start_i >= 1:
        angle += advance_on_circle(new_radius, chords[end_i-1])
      
      overfits = (
        end_i - start_i > 0
        and angle + get_edge_angle(new_radius, to_add[end_i]) > self.max_angle
      )
      
      if overfits or end_i >= len(to_add) - 1:
        if overfits:
          # Remove the follower who is overflowing
          end_i -= 1
          
          if to_add[end_i+1] > size: # Don't use min() it won't work in every case
            biggest = last_biggest
            new_radius = total_radius + biggest
            angle = advance_on_circle(new_radius, to_add[start_i])
            for i in range(start_i, end_i - 1):
              angle += advance_on_circle(new_radius, chords[i])
          elif end_i - start_i >= 0:
            angle -= advance_on_circle(new_radius, chords[end_i])
        
        angle += get_edge_angle(new_radius, to_add[end_i])
        
        # Create the new ring with every selected followers
        ring = self.get_ring(ring_i)
        
        # Choose ring radius
        if self.strong and start_i == end_i and 2*get_edge_angle(new_radius, to_add[end_i]) > self.max_angle:
          ring.radius = biggest / math.sin(self.max_angle/2) # Non infinity is ensured by the fact that 0 < max_angle < 180
        else:
          ring.radius = new_radius
        
        # Choose repartition
        if end_i == start_i:
          ring.angles = [self.max_angle/2]
        elif self.uniform:
          extra = (self.max_angle - angle) / (end_i - start_i)
          ring.angles = [get_edge_angle(new_radius, to_add[start_i])]
          for i in range(start_i, end_i):
            ring.angles.append(ring.angles[-1] + extra + advance_on_circle(ring.radius, chords[i]))
        else:
          ring.angles = [(self.max_angle - angle) / 2 + advance_on_circle(ring.radius, to_add[start_i])]
          for i in range(start_i, end_i):
            ring.angles.append(ring.angles[-1] + advance_on_circle(ring.radius, chords[i]))
        
        # Progress
        total_radius = ring.radius + biggest + self.gap
        ring_i += 1
        
        # Clean up variables
        start_i = end_i + 1
        if start_i < len(to_add):
          biggest = to_add[start_i]
          last_biggest = 0
          angle = advance_on_circle(total_radius + biggest, to_add[start_i])
    
    # Remove empty rings
    self.rings = self.rings[:ring_i]
  
  def check_rings(self):
    """Recalculate the rings if .max_angle, .gap, .spacing or a follower size has been changed"""
    total = sum(map(lambda f: f.size, self.followers))
    if (self.max_angle != self.__last_max_angle or
        self.gap != self.__last_gap or 
        self.spacing != self.__last_spacing or 
        total != self.__total_size
    ):
      self.max_angle = max(min(self.max_angle, PI2), 0.03)
      self.gap = max(self.gap, 1)
      self.spacing = max(self.spacing, 0)
      self.__last_max_angle = self.max_angle
      self.__last_gap = self.gap
      self.__last_spacing = self.spacing
      self.__total_size = total
      self.adapt_rings()
      
    if self.rotation > math.pi: self.rotation = -math.pi
    elif self.rotation < -math.pi: self.rotation = math.pi

  def add_follower(self, follower: ArcFollowElement):
    """Add a new follower"""
    self.followers.append(follower)

  def pop_follower(self, index: int=-1):
    self.followers.pop(index)

  def remove_follower(self, follower: ArcFollowElement):
    """Remove a follower of the trail"""
    self.pop_follower(self.followers.index(follower))
  
  def get_ring(self, i: int) -> ArcFollowRing:
    """Create missing rings if needed and return the requested one"""
    for _ in range(i-len(self.rings)+1):
      self.rings.append(ArcFollowRing())
    return self.rings[i]
