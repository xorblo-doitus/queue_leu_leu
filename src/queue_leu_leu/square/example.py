try: from .square import SquareFollow, SquareFollowElement, SPEED_SCALE
except ImportError:
  from square import SquareFollow, SquareFollowElement, SPEED_SCALE
import pygame, random, math

SPEED_SCALE_RATIO = SPEED_SCALE.as_integer_ratio()


class SquareFollowExample(SquareFollow):
  """Inherit the OrbitFollow class to draw elements and handle keyboard"""

  def draw(self, debug=True):
    fsize = len(self.followers)

    if debug:
      things = (
        "Followers "+str(fsize),
        "Distance  "+str(self.distance),
        "Radius    "+str(self.radius),
        "Speed     "+str(self.speed)+" / "+str(SPEED_SCALE_RATIO[1]),
        "Rings     "+", ".join(str(int(math.degrees(i.angle))) for i in self.rings),
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
      square.add_follower(SquareFollowElement(pygame.Vector2(100, 100), random.randint(6, 60)))
      return True

    elif keys[pygame.K_BACKSPACE]:
      if square.followers:
        square.pop_follower(random.randint(0, len(square.followers)-1))
      return True

    elif keys[pygame.K_RSHIFT]:
      for f in square.followers:
        f.size = random.randint(6, 60)
      return True

    elif keys[pygame.K_EQUALS]:
      square.distance += 1
      return True

    elif keys[pygame.K_6]:
      square.distance -= 1
      return True

    elif keys[pygame.K_UP]:
      square.speed += 1
      return True

    elif keys[pygame.K_DOWN]:
      square.speed -= 1
      return True

    elif keys[pygame.K_RIGHT]:
      square.radius += 1
      return True
    
    elif keys[pygame.K_LEFT]:
      square.radius -= 1
      return True

    return False


pygame.init()
window = pygame.display.set_mode((500, 500), pygame.RESIZABLE)
clock = pygame.time.Clock()
font = pygame.font.SysFont('Consolas', 16)

square = SquareFollowExample(16, 24, SquareFollowElement(pygame.Vector2(100, 100), 5))
run = True
while run:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    if square.handle_keyboard(pygame.key.get_pressed()):
      pygame.time.delay(100)

    square.update_pos(pygame.Vector2(pygame.mouse.get_pos()))
    window.fill(0)
    square.draw()
    pygame.display.flip()

pygame.quit()
