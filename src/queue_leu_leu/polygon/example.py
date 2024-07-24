try: from .polygon import PolygonFollow, PolygonFollower, Polygon
except ImportError:
  from polygon import PolygonFollow, PolygonFollower, Polygon
import pygame, random


def get_closest_point(pos: pygame.Vector2, points: list[pygame.Vector2]|dict[int, pygame.Vector2]) -> tuple[int, float]:
  """Returns (index, distance_squared)"""
  closest_i: int = 0
  closest_distance_squared: float = points[closest_i].distance_squared_to(pos) if isinstance(points, list) else float("inf")
  for i in range(1, len(points)) if isinstance(points, list) else points:
    distance_squared: float = points[i].distance_squared_to(pos)
    if distance_squared < closest_distance_squared:
      closest_i = i
      closest_distance_squared = distance_squared
  
  return closest_i, closest_distance_squared


class PolygonDrawer():
  def __init__(self, polygon: Polygon, position: pygame.Vector2 = pygame.Vector2(0, 0), color: pygame.Vector3 = pygame.Vector3(255, 0, 255)) -> None:
    self.polygon: Polygon = polygon
    self.position: pygame.Vector2 = position
    self.color: pygame.Vector3 = color
  
  def draw(self, draw_growed: float = 10) -> None:
    global_points: list[pygame.Vector2] = list(map(self.to_global, self.polygon.points))
    
    pygame.draw.circle(window, (255, 255, 255), self.position, 5)
    
    # if draw_growed:
    #   mp: pygame.Vector2 = self.to_local(pygame.mouse.get_pos())
    #   for i in range(len(self.polygon._vectors)):
    #     # if point != mp:
    #     pygame.draw.circle(window, (255, 255, 100), self.to_global(self.polygon.project(mp, i)), 3)
    
    for point in global_points:
      pygame.draw.circle(window, self.color, point, 2)
    
    if len(global_points) >= 2:
      pygame.draw.lines(window, self.color, True, global_points)
    
    # for start, direction in zip(global_points, self.polygon._vectors):
    #   pygame.draw.line(window, (0, 0, 255), start, start + direction)
    
    if not draw_growed:
      for start, vector in zip(global_points, self.polygon._growth_vectors):
        pygame.draw.line(window, (255, 0, 0), start, start + vector * 10)
    
    if draw_growed:
      PolygonDrawer(self.polygon.growed(draw_growed), self.position, self.color * 0.5).draw(0)
  
  def to_local(self, position: pygame.Vector2) -> pygame.Vector2:
    return position - self.position
  
  def to_global(self, position: pygame.Vector2) -> pygame.Vector2:
    return self.position + position


class PolygonEditor(PolygonDrawer):
  def __init__(self, polygon: Polygon, position: pygame.Vector2 = pygame.Vector2(0, 0)) -> None:
    super().__init__(polygon, position)
    self._handle_size: float = 10
    self._handle_size_squared: float = self._handle_size**2
    self.dragging_i: int = -1
  
  @property
  def handle_size(self) -> float:
    return self._handle_size
  @handle_size.setter
  def handle_size(self, new_value: float):
    self._handle_size = new_value
    self._handle_size_squared = new_value**2
  
  def handle_mouse_down(self, event) -> None:
    local_pos: pygame.Vector2 = self.to_local(event.pos)
    if event.button == pygame.BUTTON_LEFT:
      if self.polygon.points:
        point_i, distance_squared = get_closest_point(local_pos, self.polygon.points)
        if distance_squared < self._handle_size_squared:
          self.dragging_i = point_i
          return
        
        if self.polygon._vectors:
          projections: dict[int, pygame.Vector2] = {
            i: projection
            for i, projection in enumerate(self.polygon.project_all(local_pos))
            if 0 < self.polygon.get_segment_progress(projection, i) < 1
          }
          segment_i, distance_squared = get_closest_point(local_pos, projections)
          if distance_squared < self._handle_size_squared:
            self.dragging_i = segment_i + 1
            self.polygon.points.insert(self.dragging_i, local_pos)
            self.polygon.bake()
            return
      self.polygon.points.append(local_pos)
      self.polygon.bake()
      self.dragging_i = len(self.polygon.points) - 1
    elif event.button == pygame.BUTTON_RIGHT and self.polygon.points:
      point_i, distance_squared = get_closest_point(local_pos, self.polygon.points)
      if distance_squared < self._handle_size_squared:
        self.polygon.points.pop(point_i)
        self.polygon.bake()
  
  def handle_mouse_up(self, event) -> None:
    self.dragging_i = -1
  
  def handle_mouse_motion(self, event) -> None:
    if self.dragging_i == -1:
      return
    
    new_pos: pygame.Vector2 = self.polygon.points[self.dragging_i] + event.rel
    if self.polygon.points[self.dragging_i - 1] == new_pos or self.polygon.points[(self.dragging_i + 1)%len(self.polygon.points)] == new_pos:
      return
    self.polygon.points[self.dragging_i] += event.rel
    self.polygon.bake()
  
  def draw(self, draw_growed: float = 10) -> None:
    super().draw(draw_growed)
    number_offset = pygame.Vector2(1, 1)
    number_offset.scale_to_length(self._handle_size)
    for i, point in enumerate(self.polygon.points):
      pygame.draw.circle(window, self.color, self.to_global(point), self._handle_size, 1)
      window.blit(font.render(str(i), False, 0xffffffff), self.to_global(point) + number_offset)
    
    pygame.draw.circle(window, (80, 0, 0), self.position, self.polygon._incircle_radius, 2)


class PolygonFollowExample(PolygonFollow):
  """Inherit the Arc class to draw elements and handle keyboard and mouse"""
  def __init__(self, spacing: float, gap: float, polygon: Polygon, leader: PolygonFollower):
    super().__init__(spacing, gap, polygon, leader)
    
    self._editing_polygon: bool = False
    self._polygon_editor: PolygonEditor = PolygonEditor(polygon, pygame.Vector2(window.get_width(), window.get_height()) / 2)
  
  @property
  def editing_polygon(self) -> bool:
    return self._editing_polygon
  
  @editing_polygon.setter
  def editing_polygon(self, new_value) -> None:
    if new_value == self.editing_polygon:
      return
    self._editing_polygon = new_value
  
  def draw(self, debug=True) -> None:
    if self._editing_polygon:
      self._polygon_editor.draw()
      return
    
    fsize = len(self.followers)

    if debug:
      things = (
        "Followers  "+str(fsize),
        "Spacing    "+str(self.spacing),
        "Gap        "+str(self.gap),
        "Rotation≈  "+str(int(self.rotation_deg))+"°",
      )
      for i, t in enumerate(things):
        window.blit(font.render(t, False, 0xffffffff), (10, 10+20*i))
    
    for i, f in enumerate(self.followers):
      pygame.draw.circle(window, (0, 255*i/fsize, 255), f.pos, f.size)
      if debug:
        pygame.draw.circle(window, (255, 0, 0), f.pos, 3)
    
    pygame.draw.circle(window, (255, 0, 0), self.leader.pos, self.leader.size)

  def handle_keyboard(self, keys) -> bool:
    if keys[pygame.K_RETURN]:
      poly.add_follower(PolygonFollower(pygame.Vector2(100, 100), random.randint(6, 60)))
      return True

    elif keys[pygame.K_BACKSPACE]:
      if poly.followers:
        poly.pop_follower(random.randint(0, len(poly.followers)-1))
      return True

    elif keys[pygame.K_RSHIFT]:
      for f in poly.followers:
        f.size = random.randint(6, 60)
      return True

    elif keys[pygame.K_EQUALS]:
      poly.spacing += 1
      return True

    elif keys[pygame.K_6]:
      poly.spacing -= 1
      return True

    elif keys[pygame.K_UP]:
      poly.gap += 1
      return True

    elif keys[pygame.K_DOWN]:
      poly.gap -= 1
      return True

    elif keys[pygame.K_e]:
      self.editing_polygon = not self._editing_polygon
      return True

    elif self.editing_polygon:
      if keys[pygame.K_r]:
        self.polygon.points = []
        self.polygon.bake()
        return True
      elif keys[pygame.K_s]:
        self.polygon.sort_by_angle()
        return True

    return False

  def handle_mouse_motion(self, event) -> None:
    if self._editing_polygon:
      self._polygon_editor.handle_mouse_motion(event)

  def handle_mouse_down(self, event) -> None:
    if self._editing_polygon:
      self._polygon_editor.handle_mouse_down(event)

  def handle_mouse_up(self, event) -> None:
    if self._editing_polygon:
      self._polygon_editor.handle_mouse_up(event)

  def handle_mouse_wheel(self, event) -> None:
    poly.rotation_deg += event.y * 5


pygame.init()
window = pygame.display.set_mode((500, 500), pygame.RESIZABLE)
clock = pygame.time.Clock()
font = pygame.font.SysFont('Consolas', 16)

poly = PolygonFollowExample(16, 24, Polygon(), PolygonFollower(pygame.Vector2(100, 100), 5))
run = True
while run:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.MOUSEWHEEL:
          poly.handle_mouse_wheel(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
          poly.handle_mouse_down(event)
        elif event.type == pygame.MOUSEBUTTONUP:
          poly.handle_mouse_up(event)
        elif event.type == pygame.MOUSEMOTION:
          poly.handle_mouse_motion(event)
        elif event.type == pygame.VIDEORESIZE:
          poly._polygon_editor.position = pygame.Vector2(event.w, event.h) / 2

    if poly.handle_keyboard(pygame.key.get_pressed()):
      pygame.time.delay(100)

    poly.update_pos(pygame.Vector2(pygame.mouse.get_pos()))
    window.fill(0)
    poly.draw()
    pygame.display.flip()

pygame.quit()
