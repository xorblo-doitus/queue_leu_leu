try: from .joint import JointFollow, JointFollowElement
except ImportError:
  from joint import JointFollow, JointFollowElement
import pygame, random


class JointFollowExample(JointFollow):
  """Inherit the JointFollow class to draw elements and handle keyboard"""

  def draw(self, debug=True):
    fsize = len(self.followers)

    if debug:
      things = (
        "Followers "+str(fsize),
        "Distance  "+str(self.distance),
      )
      for i, t in enumerate(things):
        window.blit(font.render(t, False, 0xffffffff), (10, 10+20*i))

    for i, f in enumerate(self.followers):
      pygame.draw.circle(window, (0, 255*i/fsize, 255), f.pos, f.size)
      if debug:
        pygame.draw.circle(window, (255, 0, 0), f.pos, 3)
        last = self.leader.pos if i == 0 else self.followers[i - 1].pos
        pygame.draw.line(window, (255, 0, 0), f.pos, last, 2)
        
    pygame.draw.circle(window, (255, 0, 0), self.leader.pos, self.leader.size)

  def handle_keyboard(self, keys):
    if keys[pygame.K_RETURN]:
      self.add_follower(JointFollowElement(pygame.Vector2(100, 100), random.randint(6, 60)))
      return True

    elif keys[pygame.K_BACKSPACE]:
      if self.followers:
        self.pop_follower(random.randint(0, len(self.followers)-1))
      return True

    elif keys[pygame.K_RSHIFT]:
      for f in self.followers:
        f.size = random.randint(6, 60)
      return True

    elif keys[pygame.K_EQUALS]:
      self.distance += 1
      return True

    elif keys[pygame.K_6]:
      self.distance -= 1
      return True

    return False


pygame.init()
window = pygame.display.set_mode((500, 500), pygame.RESIZABLE)
clock = pygame.time.Clock()
font = pygame.font.SysFont('Consolas', 16)

joint = JointFollowExample(16, JointFollowElement(pygame.Vector2(100, 100), 5))
run = True
while run:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    if joint.handle_keyboard(pygame.key.get_pressed()):
      pygame.time.delay(100)

    joint.update_pos(pygame.Vector2(pygame.mouse.get_pos()))
    window.fill(0)
    joint.draw()
    pygame.display.flip()

pygame.quit()
