from zeta import Trail, TrailElement
import pygame, random


class TrailExample(Trail):
  """Inherit the Trail class to draw elements and handle keyboard"""
  
  def draw(self, debug=True):
    fsize = len(self.followers)
    
    if debug:
      things = (
        "Trail     "+str(len(self.trail)), 
        "Followers "+str(fsize), 
        "Distance  "+str(self.distance),
        "Leader    "+str(self.get_leader_index())
      )
      for i, t in enumerate(things):
        window.blit(font.render(t, False, 0xffffffff), (10, 10+20*i))

    for i, t in enumerate(self.followers):
      pygame.draw.circle(window, (0, 255*i/fsize, 255), t.pos, t.size)
    pygame.draw.circle(window, (255, 0, 0), self.leader.pos, 5)

    if debug:
      for p in self.trail:
        pygame.draw.circle(window, (255, 0, 0), p, 3)

  def handle_keyboard(self, keys):
    if keys[pygame.K_RETURN]:
      trail.add_follower(TrailElement(pygame.Vector2(100, 100), random.randint(6, 60)))
      return True
      
    elif keys[pygame.K_BACKSPACE]:
      if trail.followers:
        trail.pop_follower(random.randint(0, len(trail.followers)-1))
      return True
      
    elif keys[pygame.K_RSHIFT]:
      for f in trail.followers:
        f.size = random.randint(6, 60)
      return True
      
    elif keys[pygame.K_EQUALS]:
      trail.distance += 1
      return True
      
    elif keys[pygame.K_6]:
      trail.distance -= 1
      return True
    
    return False


pygame.init()
window = pygame.display.set_mode((500, 500), pygame.RESIZABLE)
clock = pygame.time.Clock()
font = pygame.font.SysFont('Consolas', 16)

trail = TrailExample(16, TrailElement(pygame.Vector2(100, 100), 5), True)
run = True
while run:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    if trail.handle_keyboard(pygame.key.get_pressed()):
      pygame.time.delay(100)

    trail.update_pos(pygame.Vector2(pygame.mouse.get_pos()))
    window.fill(0)
    trail.draw()
    pygame.display.flip()

pygame.quit()
