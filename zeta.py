import pygame, random

class TrailElement:
  def __init__(self, pos: pygame.Vector2, size: float):
    self.pos = pos
    self.size = size

class Trail:
  def __init__(self, distance: float, leader: TrailElement):
    self.leader = leader
    self.followers: list[TrailElement] = []
    self.trail = [self.leader.pos]
    self.distance = distance
    self.__last_distance = self.distance
    self.__total_size = 0
    self.__i = 0

  def update_pos(self, new_pos: pygame.Vector2):
    self.check_trail()
    self.leader.pos = new_pos
    current_pos = self.trail[self.__i]
    
    while self.trail[self.__i].distance_to(new_pos) >= self.get_distance():
      current_pos = current_pos.move_towards(new_pos, self.get_distance())
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

  def increase_trail(self, at: int, amount: int, position: pygame.Vector2, away_from: pygame.Vector2):
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

  def _wrapped(self, i: int) -> int:
    return i % len(self.trail)
  
  def draw(self, debug=True):
    fsize = len(self.followers)
    
    if debug:
      things = (
        "T "+str(len(self.trail)), 
        "F "+str(fsize), 
        "D "+str(self.distance),
        "I "+str(self.__i)
      )
      for i, t in enumerate(things):
        window.blit(font.render(t, False, 0xffffffff), (10, 10+20*i))
    
    for i, t in enumerate(self.followers):
      pygame.draw.circle(window, (0, 255*i/fsize, 255), t.pos, t.size)

    if debug:
      for p in self.trail:
        pygame.draw.circle(window, (255, 0, 0), p, 3)


pygame.init()
window = pygame.display.set_mode((500, 500), pygame.RESIZABLE)
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 16)

trail = Trail(16, TrailElement(pygame.Vector2(100, 100), 5))

run = True
while run:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_RETURN]:
      trail.add_follower(TrailElement(pygame.Vector2(100, 100), random.randint(6, 60)))
      pygame.time.delay(100)
    elif keys[pygame.K_BACKSPACE]:
      if trail.followers:
        trail.pop_follower(random.randint(0, len(trail.followers)-1))
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
