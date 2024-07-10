try: from .arc import ArcFollow, ArcFollowElement
except ImportError:
  from arc import ArcFollow, ArcFollowElement
import pygame, random


class ArcFollowExample(ArcFollow):
  """Inherit the Arc class to draw elements and handle keyboard"""

  def draw(self, debug=True):
    fsize = len(self.followers)

    if debug:
      things = (
        "Followers "+str(fsize),
        "Radius    "+str(self.radius),
        "Angle     "+str(self.distance),
        "Sides     "+str(self.max_angle),
        "Rotation  "+str(self.rotation),
      )
      for i, t in enumerate(things):
        window.blit(font.render(t, False, 0xffffffff), (10, 10+20*i))

    for i, f in enumerate(self.followers):
      pygame.draw.circle(window, (0, 255*i/fsize, 255), f.pos, f.size)
      if debug:
        pygame.draw.circle(window, (255, 0, 0), f.pos, 3)
      
    pygame.draw.circle(window, (255, 0, 0), self.leader.pos, 5)

  def handle_keyboard(self, keys):
    if keys[pygame.K_RETURN]:
      arc.add_follower(ArcFollowElement(pygame.Vector2(100, 100), random.randint(6, 60)))
      return True

    elif keys[pygame.K_BACKSPACE]:
      if arc.followers:
        arc.pop_follower(random.randint(0, len(arc.followers)-1))
      return True

    elif keys[pygame.K_RSHIFT]:
      for f in arc.followers:
        f.size = random.randint(6, 60)
      return True

    elif keys[pygame.K_EQUALS]:
      arc.distance += 1
      return True

    elif keys[pygame.K_6]:
      arc.distance -= 1
      return True

    elif keys[pygame.K_UP]:
      arc.radius += 1
      return True

    elif keys[pygame.K_DOWN]:
      arc.radius -= 1
      return True

    elif keys[pygame.K_RIGHT]:
      arc.max_angle += 5
      return True
    
    elif keys[pygame.K_LEFT]:
      arc.max_angle -= 5
      return True

    return False

  def handle_mouse(self, event):
    arc.rotation += event.y * 5


pygame.init()
window = pygame.display.set_mode((500, 500), pygame.RESIZABLE)
clock = pygame.time.Clock()
font = pygame.font.SysFont('Consolas', 16)

arc = ArcFollowExample(16, 24, 90, ArcFollowElement(pygame.Vector2(100, 100), 5))
run = True
while run:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.MOUSEWHEEL:
          arc.handle_mouse(event)

    if arc.handle_keyboard(pygame.key.get_pressed()):
      pygame.time.delay(100)

    arc.update_pos(pygame.Vector2(pygame.mouse.get_pos()))
    window.fill(0)
    arc.draw()
    pygame.display.flip()

pygame.quit()
