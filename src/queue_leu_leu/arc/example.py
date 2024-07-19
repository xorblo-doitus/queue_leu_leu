try: from .arc import ArcFollow, ArcFollowElement, Vector2_polar
except ImportError:
  from arc import ArcFollow, ArcFollowElement, Vector2_polar
import pygame, random, math

rainbow = [
  (255, 0, 0),
  (255, 125, 0),
  (255, 255, 0),
  (0, 255, 0),
  (0, 255, 255),
  (0, 0, 255),
  (125, 0, 125),
]
is_rainbow = False

class ArcFollowExample(ArcFollow):
  """Inherit the Arc class to draw elements and handle keyboard and mouse"""

  def draw(self, debug=True):
    fsize = len(self.followers)

    if debug:
      things = (
        "Followers  "+str(fsize),
        "Spacing    "+str(self.spacing),
        "Gap        "+str(self.gap),
        "Max Angle≈ "+str(int(round(self.max_angle_deg, 5)))+"°",
        "Rotation≈  "+str(int(self.rotation_deg))+"°",
        "Strong     "+str(self.strong),
        "Uniform    "+str(self.uniform),
      )
      for i, t in enumerate(things):
        window.blit(font.render(t, False, 0xffffffff), (10, 10+20*i))
    
    colors = []
    if is_rainbow:
      for i, r in enumerate(self.rings):
        colors += [rainbow[i%len(rainbow)]] * len(r.angles)
    
    for i, f in enumerate(self.followers):
      pygame.draw.circle(window, colors[i] if is_rainbow else (0, 255*i/fsize, 255), f.pos, f.size)
      if debug:
        pygame.draw.circle(window, (255, 0, 0), f.pos, 3)
    
    if debug:
      pygame.draw.line(window, (255, 0, 0), self.leader.pos, self.leader.pos + Vector2_polar((self.rings[-1].radius if self.rings else 0)+100, self.rotation), 2)
      pygame.draw.line(window, (255, 0, 0), self.leader.pos, self.leader.pos + Vector2_polar((self.rings[-1].radius if self.rings else 0)+100, self.rotation + self.max_angle), 2)
      
      for ring in self.rings:
        pygame.draw.circle(window, (100, 100, 0), self.leader.pos, ring.radius, 1)
        pygame.draw.arc(
          window,
          (255, 255, 0),
          pygame.Rect(self.leader.pos.x - ring.radius, self.leader.pos.y - ring.radius, 2*ring.radius, 2*ring.radius),
          -self.max_angle-self.rotation,
          -self.rotation,
          1
        )
    
    pygame.draw.circle(window, (255, 0, 0), self.leader.pos, self.leader.size)

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
      arc.spacing += 1
      return True

    elif keys[pygame.K_6]:
      arc.spacing -= 1
      return True

    elif keys[pygame.K_UP]:
      arc.gap += 1
      return True

    elif keys[pygame.K_DOWN]:
      arc.gap -= 1
      return True

    elif keys[pygame.K_RIGHT]:
      arc.max_angle_deg += 5
      return True
    
    elif keys[pygame.K_LEFT]:
      arc.max_angle_deg -= 5
      return True
    
    elif keys[pygame.K_u]:
      arc.uniform = not arc.uniform
      return True
    
    elif keys[pygame.K_s]:
      arc.strong = not arc.strong
      return True
    
    elif keys[pygame.K_r] and keys[pygame.K_a] and keys[pygame.K_i] and keys[pygame.K_n] and keys[pygame.K_b] and keys[pygame.K_o] and keys[pygame.K_w]:
      global is_rainbow
      is_rainbow = not is_rainbow
      return True

    return False

  def handle_mouse(self, event):
    arc.rotation_deg += event.y * 5


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
