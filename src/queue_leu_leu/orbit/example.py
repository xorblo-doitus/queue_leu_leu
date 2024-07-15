try: from .orbit import OrbitFollow, OrbitFollowElement, SPEED_SCALE
except ImportError:
  from orbit import OrbitFollow, OrbitFollowElement, SPEED_SCALE
import pygame, random, math

SPEED_SCALE_RATIO = SPEED_SCALE.as_integer_ratio()


class OrbitFollowExample(OrbitFollow):
  """Inherit the OrbitFollow class to draw elements and handle keyboard"""

  def draw(self, debug=True):
    fsize = len(self.followers)

    if debug:
      things = (
        "Followers         "+str(fsize),
        "Follower spacing  "+str(self.follower_spacing),
        "Fing spacing      "+str(self.ring_spacing),
        "Mode              "+str(OrbitFollow.mode_names[self.mode]),
        "Speed             "+str(self.speed)+" / "+str(SPEED_SCALE_RATIO[1]),
        "Angles            "+", ".join(str(int(math.degrees(i.angle))).rjust(3) for i in self.rings),
        "Rings             "+", ".join(str(i.radius).rjust(3) for i in self.rings),
      )
      for i, t in enumerate(things):
        window.blit(font.render(t, False, 0xffffffff), (10, 10+20*i))

    for i, f in enumerate(self.followers):
      pygame.draw.circle(window, (0, 255*i/fsize, 255), f.pos, f.size)
      if debug:
        pygame.draw.circle(window, (255, 0, 0), f.pos, 3)
    
    if debug:
      for ring in self.rings:
        pygame.draw.circle(window, (255, 255, 0), self.leader.pos, ring.radius, 1)
        
    pygame.draw.circle(window, (255, 0, 0), self.leader.pos, self.leader.size)

  def handle_keyboard(self, keys):
    if keys[pygame.K_RETURN]:
      orbit.add_follower(OrbitFollowElement(pygame.Vector2(100, 100), random.randint(6, 60)))
      return True

    elif keys[pygame.K_BACKSPACE]:
      if orbit.followers:
        orbit.pop_follower(random.randint(0, len(orbit.followers)-1))
      return True

    elif keys[pygame.K_RSHIFT]:
      for f in orbit.followers:
        f.size = random.randint(6, 60)
      return True

    elif keys[pygame.K_EQUALS]:
      orbit.follower_spacing += 1
      return True

    elif keys[pygame.K_6]:
      orbit.follower_spacing -= 1
      return True

    elif keys[pygame.K_UP]:
      orbit.speed += 2
      return True

    elif keys[pygame.K_DOWN]:
      orbit.speed -= 2
      return True

    elif keys[pygame.K_RIGHT]:
      orbit.ring_spacing += 2
      return True
    
    elif keys[pygame.K_LEFT]:
      orbit.ring_spacing -= 2
      return True
    
    elif keys[pygame.K_m]:
      orbit.mode = OrbitFollow.MODE_EVEN_PLACEMENT if orbit.mode == OrbitFollow.MODE_EVEN_SPACING else OrbitFollow.MODE_EVEN_SPACING
      orbit.adapt_rings()
      return True

    return False


pygame.init()
window = pygame.display.set_mode((500, 500), pygame.RESIZABLE)
clock = pygame.time.Clock()
font = pygame.font.SysFont('Consolas', 16)

orbit = OrbitFollowExample(16, 24, 1, OrbitFollowElement(pygame.Vector2(100, 100), 5))
run = True
while run:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    if orbit.handle_keyboard(pygame.key.get_pressed()):
      pygame.time.delay(100)

    orbit.update_pos(pygame.Vector2(pygame.mouse.get_pos()))
    window.fill(0)
    orbit.draw()
    pygame.display.flip()

pygame.quit()
