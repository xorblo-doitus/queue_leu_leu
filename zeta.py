import pygame, random, math

class TrailElement:
  def __init__(self, xy: pygame.Vector2, size: float):
    self.xy = xy
    self.size = size

class Trail:
  def __init__(self, distance, leader_pos, leader_size):
    self.leader = TrailElement(leader_pos, leader_size)
    self.followers: list[TrailElement] = []
    self.distance = distance
    self._last_distance = self.distance
    self.total_size = 0
    self._i = 0
    self.trail: list[pygame.Vector2] = [self.leader.xy]

  def update_pos(self, new_position):
    if self.distance != self._last_distance:
      self._last_distance = self.distance
      self._adapt_trail()
    
    self.leader.xy = new_position
    current_pos = self.trail[self._i]
    if self.distance < 1: self.distance = 1 
    
    while self.trail[self._i].distance_to(new_position) >= self._get_distance():
      current_pos = current_pos.move_towards(new_position, self._get_distance())
      self._i = self._wrapped(self._i - 1)
      self.trail[self._i] = current_pos
      
    total = sum(map(lambda f: f.size, self.followers))
    if total != self.total_size: 
      self.total_size = total
      self._adapt_trail()
    self.update_trail()
    
  def update_trail(self):
    i = self._i + self._get_lenght(self.leader.size)/2
    tsize = len(self.trail)
    
    for follower in self.followers:
      size = self._get_lenght(follower.size)/2
      i += size
      follower.xy = self.trail[self._wrapped(int(i % tsize))]
      i += size

  def add_follower(self, xy, size):
    self.followers.append(TrailElement(xy, size))
    self.total_size += size
    self._adapt_trail(self._get_lenght(size))

  def remove_follower(self, index=-1):
    if self.followers:
      element = self.followers.pop(index)
      self.total_size -= element.size
      self._adapt_trail(-self._get_lenght(element.size))
      
  def _wrapped(self, i):
    return i % len(self.trail)
  
  def _adapt_trail(self, amout=0):
    delta = amout if amout != 0 else self._get_total_size() + 1 - len(self.trail)
    
    if delta > 0: 
      self._i = self._wrapped(self._i - 1)
      self._increase_trail(self._i, delta, self.trail[self._i], 
                           self.trail[self._wrapped(self._i - 2)] if len(self.trail) > 1 else self.leader.xy)
    elif delta < 0: self._decrease_trail(-delta)

  def _increase_trail(self, at, amount, position, away_from):
    if self._i > at: self._i += amount
    offset = position - away_from
    
    for i in range(amount): 
      position += offset
      self.trail.insert(at+i, position)

  def _decrease_trail(self, amount):
    self.trail = [
      self.trail[i] for i in range(self._i - len(self.trail), self._i - amount)
    ]
    self._i = 0

  def _get_lenght(self, size):
    return int((size + self._get_distance()) / self._get_distance() * 2)
  
  def _get_distance(self):
    if self.distance < 1: self.distance = 1
    return self.distance
  
  def _get_total_size(self):
    return self._get_lenght(self.leader.size) + sum(map(lambda f: self._get_lenght(f.size), self.followers))

  def draw(self, debug=True):
    fsize = len(self.followers)
    
    if debug:
      things = (
        "T "+str(len(self.trail)), 
        "F "+str(fsize), 
        "D "+str(self.distance),
        "I "+str(self._i)
      )
      for i, t in enumerate(things):
        window.blit(font.render(t, False, 0xffffffff), (10, 10+20*i))
    
    for i, t in enumerate(self.followers):
      pygame.draw.circle(window, (0, 255*i/fsize, 255), t.xy, t.size)

    if debug:
      for p in self.trail:
        pygame.draw.circle(window, (255, 0, 0), p, 3)


pygame.init()
window = pygame.display.set_mode((500, 500), pygame.RESIZABLE)
clock = pygame.time.Clock()
trail = Trail(16, pygame.Vector2(100, 100), 5)
font = pygame.font.SysFont('Arial', 16)


run = True
while run:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_RETURN]:
      trail.add_follower(pygame.Vector2(100, 100), random.randint(6, 60))
      pygame.time.delay(100)
    elif keys[pygame.K_BACKSPACE]:
      if trail.followers:
        trail.remove_follower(random.randint(0, len(trail.followers)-1))
      pygame.time.delay(100)
    elif keys[pygame.K_RSHIFT]:
      for f in trail.followers:
        f.size = random.randint(6, 50)
      pygame.time.delay(100)
    elif keys[pygame.K_EQUALS]:
      trail.distance += 1
      pygame.time.delay(100)
    elif keys[pygame.K_6]:
      trail.distance -= 1
      pygame.time.delay(100)

    trail.update_pos(pygame.Vector2(pygame.mouse.get_pos()))
    window.fill(0)
    trail.draw()
    pygame.draw.circle(window, (255, 0, 0), pygame.mouse.get_pos(), 5)
    pygame.display.flip()

pygame.quit()
