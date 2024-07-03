import math, pygame, random

class TrailElement:
  def __init__(self, xy: pygame.Vector2, size: float):
    self.xy = xy
    self.size = size

class Trail:
  def __init__(self, distance, leader_pos, leader_size):
    self.leader = TrailElement(leader_pos, leader_size)
    self.followers: list[TrailElement] = []
    self.distance = distance
    self._i = 0
    self.trail: list[pygame.Vector2] = [self.leader.xy]
    
    self._increase_trail(0, self._get_lenght(self.leader.size), self.leader.xy)

  def update_pos(self, new_position):
    self.leader.xy = new_position
    
    current_pos = self.trail[self._i]
    while self.trail[self._i].distance_to(new_position) >= self.distance:
      current_pos = current_pos.move_towards(new_position, self.distance)
      self._i = self._wrapped(self._i - 1)
      self.trail[self._i] = current_pos
      
    self.update_trail()
    
  def update_trail(self):
    i = self._i + self._get_lenght(self.leader.size)
    tsize = len(self.trail)
    
    for follower in self.followers:
      i += self._get_lenght(follower.size)
      follower.xy = self.trail[self._wrapped(i % tsize)]
      i += self._get_lenght(follower.size)

  def add_follower(self, xy, size):
    self.followers.append(TrailElement(xy, size))
    total = self.get_total_size()
    self._increase_trail(
      self._wrapped(self._i - 1),
      2 * self._get_lenght(size),
      #(total + 2 * (size + self.distance)) // self.distance - total // self.distance,
      self.trail[self._wrapped(self._i - 1)]
    )

  def remove_follower(self, index=-1):
    if self.followers:
      element = self.followers.pop(index)
      to_remove = 2 * self._get_lenght(element.size)

      self.trail = [
        self.trail[i] for i in range(self._i - len(self.trail), self._i - to_remove)
      ]
      self._i = 0

      self.update_trail()
      
  def _wrapped(self, i):
    return i % len(self.trail)

  def _increase_trail(self, at, amount, position):
    for _ in range(amount): self.trail.insert(at, position)
    if self._i > at: self._i += amount

  def _get_lenght(self, size):
    return int((size + self.distance) / self.distance)

  def get_total_size(self):
    return self.leader.size + sum(map(lambda element: element.size, self.followers))
  
  def draw(self):
    #debug
    window.blit(font.render(str(len(self.trail)), False, 0xffffffff), (10, 10))
    window.blit(font.render(str(len(self.followers)), False, 0xffffffff), (10, 30))
    for i, t in enumerate(self.followers):
      pygame.draw.circle(window, (0, 255*i/len(self.followers), 255), t.xy.xy, t.size)

    #followers
    for p in self.trail:
      pygame.draw.circle(window, (255, 0, 0), p.xy, 3)


pygame.init()
window = pygame.display.set_mode((500, 500), pygame.RESIZABLE)
clock = pygame.time.Clock()
trail = Trail(10, pygame.Vector2(100, 100), 5)
font = pygame.font.SysFont('Arial', 16)


run = True
while run:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_RETURN]:
      trail.add_follower(pygame.Vector2(100, 100), random.randint(6, 30))
      pygame.time.delay(100)
    if keys[pygame.K_BACKSPACE] and trail.followers:
      trail.remove_follower(random.randint(0, len(trail.followers)-1))
      pygame.time.delay(100)

    trail.update_pos(pygame.Vector2(pygame.mouse.get_pos()))
    window.fill(0)
    trail.draw()
    pygame.draw.circle(window, (255, 0, 0), pygame.mouse.get_pos(), 5)
    pygame.display.flip()

pygame.quit()
