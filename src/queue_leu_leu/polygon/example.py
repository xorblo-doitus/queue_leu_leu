try: from .polygon import PolygonFollow, PolygonFollower, Polygon
except ImportError:
  from polygon import PolygonFollow, PolygonFollower, Polygon
import pygame, random
from pygame import Vector2
from tkinter.simpledialog import askstring


def get_closest_point(pos: Vector2, points: list[Vector2]|dict[int, Vector2]) -> tuple[int, float]:
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
  def __init__(self, polygon: Polygon, position: Vector2 = Vector2(0, 0), color: pygame.Vector3 = pygame.Vector3(255, 255, 0)) -> None:
    self.polygon: Polygon = polygon
    self.position: Vector2 = position
    self.color: pygame.Vector3 = color
  
  def draw(self, debug: bool = False) -> None:
    global_points: list[Vector2] = list(map(self.to_global, self.polygon.points))
    
    pygame.draw.circle(window, (255, 255, 255), self.position, 5)
    
    # if draw_growed:
    #   mp: Vector2 = self.to_local(pygame.mouse.get_pos())
    #   for i in range(len(self.polygon._vectors)):
    #     # if point != mp:
    #     pygame.draw.circle(window, (255, 255, 100), self.to_global(self.polygon.project(mp, i)), 3)
    
    for point in global_points:
      pygame.draw.circle(window, self.color, point, 2)
    
    if len(global_points) >= 2:
      pygame.draw.lines(window, self.color, True, global_points)
    
    # for start, direction in zip(global_points, self.polygon._vectors):
    #   pygame.draw.line(window, (0, 0, 255), start, start + direction)
    
    if debug:
      for start, vector in zip(global_points, self.polygon._growth_vectors):
        pygame.draw.line(window, (255, 0, 0), start, start + vector * 10)
  
  def to_local(self, position: Vector2) -> Vector2:
    return position - self.position
  
  def to_global(self, position: Vector2) -> Vector2:
    return self.position + position


class PolygonEditor(PolygonDrawer):
  def __init__(self, polygon: Polygon, position: Vector2 = Vector2(0, 0)) -> None:
    super().__init__(polygon, position)
    self._handle_size: float = 10
    self._handle_size_squared: float = self._handle_size**2
    self._growth_previews: list[tuple[bool, int]] = [10, 20, 40, 70, 110]
    self.dragging_i: int = -1
  
  @property
  def handle_size(self) -> float:
    return self._handle_size
  @handle_size.setter
  def handle_size(self, new_value: float):
    self._handle_size = new_value
    self._handle_size_squared = new_value**2
  
  def update_growth_preview(self, input: str):
    self._growth_previews = []
    for part in input.split(","):
      part = part.strip()
      if part.startswith("="):
        self._growth_previews.append(int(part.removeprefix("=").strip()))
      else:
        self._growth_previews.append(int(part) + (self._growth_previews[-1] if self._growth_previews else 0))
  
  def handle_mouse_down(self, event) -> None:
    local_pos: Vector2 = self.to_local(event.pos)
    if event.button == pygame.BUTTON_LEFT:
      if self.polygon.points:
        point_i, distance_squared = get_closest_point(local_pos, self.polygon.points)
        if distance_squared < self._handle_size_squared:
          self.dragging_i = point_i
          return
        
        if self.polygon._vectors:
          projections: dict[int, Vector2] = {
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
    
    new_pos: Vector2 = self.polygon.points[self.dragging_i] + event.rel
    if self.polygon.points[self.dragging_i - 1] == new_pos or self.polygon.points[(self.dragging_i + 1)%len(self.polygon.points)] == new_pos:
      return
    self.polygon.points[self.dragging_i] += event.rel
    self.polygon.bake()
  
  def draw(self) -> None:
    super().draw(True)
    number_offset = Vector2(1, 1)
    number_offset.scale_to_length(self._handle_size)
    for i, point in enumerate(self.polygon.points):
      pygame.draw.circle(window, (255, 0, 255), self.to_global(point), self._handle_size, 3)
      window.blit(font.render(str(i), False, 0xffffffff), self.to_global(point) + number_offset)
    
    pygame.draw.circle(window, (80, 0, 0), self.position, self.polygon._incircle_radius, 2)
    
    for growth in self._growth_previews:
      PolygonDrawer(self.polygon.growed(growth), self.position, self.color * 0.5).draw()


class PolygonFollowExample(PolygonFollow):
  """Inherit the Arc class to draw elements and handle keyboard and mouse"""
  def __init__(self, spacing: float, gap: float, polygon: Polygon, leader: PolygonFollower):
    super().__init__(spacing, gap, polygon, leader)
    
    self._editing_polygon: bool = False
    self._polygon_editor: PolygonEditor = PolygonEditor(polygon, Vector2(window.get_width(), window.get_height()) / 2)
    self._polygon_drawers: list[PolygonDrawer] = []
  
  @property
  def editing_polygon(self) -> bool:
    return self._editing_polygon
  
  @editing_polygon.setter
  def editing_polygon(self, new_value) -> None:
    if new_value == self.editing_polygon:
      return
    self._editing_polygon = new_value
  
  def adapt(self):
    super().adapt()
    self._polygon_drawers = [
      PolygonDrawer(polygon, self.leader.pos, 0xffff00 if i%3==1 else 0x995500)
      for i, polygon in enumerate(self._debug_polygons)
    ]
  
  def draw(self, debug=True) -> None:
    if self._editing_polygon:
      self._polygon_editor.draw()
      return
    
    position = self.leader.pos
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
      
      for drawer in self._polygon_drawers:
        drawer.position = position
        drawer.draw()
    
    for i, f in enumerate(self.followers):
      pygame.draw.circle(window, (0, 255*i/fsize, 255), f.pos, f.size)
      if debug:
        pygame.draw.circle(window, (255, 0, 0), f.pos, 3)
    
    pygame.draw.circle(window, (255, 0, 0), position, self.leader.size)

  def handle_keyboard(self, keys) -> bool:
    if keys[pygame.K_RETURN]:
      poly.add_follower(PolygonFollower(Vector2(100, 100), random.randint(6, 60)))
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
      elif keys[pygame.K_g]:
        self._polygon_editor.update_growth_preview(
          askstring(
            "Configurate",
            "New growth previews:\t\t\t\t\t\t",
            initialvalue=", =".join(map(str, self._polygon_editor._growth_previews)),
          )
        )
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

square = Polygon([
  Vector2(-1, -1),
  Vector2(1, -1),
  Vector2(1, 1),
  Vector2(-1, 1),
]) * 20.0

poly = PolygonFollowExample(16, 24, square, PolygonFollower(Vector2(100, 100), 5))
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
          poly._polygon_editor.position = Vector2(event.w, event.h) / 2

    if poly.handle_keyboard(pygame.key.get_pressed()):
      pygame.time.delay(100)

    poly.update_pos(Vector2(pygame.mouse.get_pos()))
    window.fill(0)
    poly.draw()
    pygame.display.flip()

pygame.quit()
