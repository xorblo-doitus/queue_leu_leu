try: from .polygon import PolygonFollow, PolygonFollower, Polygon
except ImportError:
  from polygon import PolygonFollow, PolygonFollower, Polygon
import pygame, random
from pygame import Vector2, Surface
from pygame._sdl2.video import Window, Renderer, Texture
from tkinter.simpledialog import askstring


BUILTIN_POLYGONS: dict[str, Polygon] = {
  "square": Polygon([
    Vector2(-1, -1),
    Vector2(1, -1),
    Vector2(1, 1),
    Vector2(-1, 1),
  ]) * 50,
  
  "test_align": Polygon([
    Vector2(-1, -1),
    Vector2(0, -1),
    Vector2(1, -1),
    Vector2(1.001, -1.001),
    Vector2(1.002, -1),
    Vector2(5, -1),
    Vector2(1, 1),
    Vector2(-1, 1),
  ]) * 200,

  # Glitchy configs:
  # 48, 37, 28, 58, 33 # FIXED
  # 21, 34, 11, 46, 44 # FIXED # Hhhhmm, this one seems caused by float precision limits
  "test_unalign_far": Polygon([
    Vector2(-1, -1),
    Vector2(1, -1),
    Vector2(1.01, -1),
    Vector2(1, 1),
    Vector2(-1, 1),
  ]) * 100,

  # Glitchy config: 10, 52, 29, 42, 26, 46, 36, 8, 46, 57, 30 # FIXED
  "test_angles": Polygon([
    Vector2(-0.4, 0.5),
    Vector2(-0.4, -1),
    Vector2(0, -0.2),
    Vector2(0.4, -1),
    Vector2(0.4, 0.5),
  ]) * 100,
}


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
  
  def draw(self, surface: Surface, debug: bool = False) -> None:
    global_points: list[Vector2] = list(map(self.to_global, self.polygon.points))
    
    pygame.draw.circle(surface, (255, 255, 255), self.position, 3)
    
    # if draw_growed:
    #   mp: Vector2 = self.to_local(pygame.mouse.get_pos())
    #   for i in range(len(self.polygon._vectors)):
    #     # if point != mp:
    #     pygame.draw.circle(surface, (255, 255, 100), self.to_global(self.polygon.project(mp, i)), 3)
    
    for point in global_points:
      pygame.draw.circle(surface, self.color, point, 2)
    
    if len(global_points) >= 2:
      pygame.draw.lines(surface, self.color, True, global_points)
    
    # for start, direction in zip(global_points, self.polygon._vectors):
    #   pygame.draw.line(surface, (0, 0, 255), start, start + direction)
    
    if debug:
      for start, vector in zip(global_points, self.polygon._growth_vectors):
        pygame.draw.line(surface, (255, 0, 0), start, start + vector * 10)
  
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
    
    if not input:
      return
    
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
  
  def draw(self, surface: Surface) -> None:
    super().draw(surface, True)
    number_offset = Vector2(1, 1)
    number_offset.scale_to_length(self._handle_size)
    for i, point in enumerate(self.polygon.points):
      pygame.draw.circle(surface, (255, 0, 255), self.to_global(point), self._handle_size, 3)
      surface.blit(font.render(str(i), False, 0xffffffff), self.to_global(point) + number_offset)
    
    pygame.draw.circle(surface, (80, 0, 0), self.position, self.polygon._incircle_radius, 2)
    
    for growth in self._growth_previews:
      PolygonDrawer(self.polygon.growed(growth), self.position, self.color * 0.5).draw(surface)


class LibraryIcon(PolygonDrawer):
  def __init__(self, polygon: Polygon, position: Vector2, color: pygame.Vector3, name: str, size = 32) -> None:
    self._size = size
    self._name = name
    self._icon_position = position
    
    farthest: float = 1
    for point in polygon.points:
      farthest = max(farthest, abs(point.x), abs(point.y))
    
    super().__init__(polygon * (size / farthest * 0.35), position + Vector2(size // 2, size // 2 - 10), color)
    
    self._result = polygon
  
  def draw(self, surface: Surface, debug: bool = False, hovered: bool = False) -> None:
    super().draw(surface, debug)
    
    pygame.draw.rect(
      surface,
      0xffffff if hovered else 0,
      pygame.Rect(self._icon_position, (self._size-4,)*2),
      1
    )
    
    surface.blit(font.render(self._name, False, 0xffffffff), self.position + Vector2(-self._size//2 + 4, self._size//2 - 14))


class Library():
  def __init__(self, follow: PolygonFollow) -> None:
    self._is_open = False
    self._position = Vector2(10, 10)
    self._columns: int = 4
    self._window: Window|None = None
    self.icon_size = 128
    self.follow: PolygonFollow = follow
    self._icons: list[LibraryIcon] = []
    self._hovered = -1
    self.debug = True
  
  @property
  def is_open(self) -> bool:
    return self._is_open
  
  @is_open.setter
  def is_open(self, new_value):
    if new_value == self._is_open:
      return
    
    self._is_open = new_value
    
    if new_value:
      self._window = Window("Polygon library", (self._columns * self.icon_size + 2*self._position.x, 480))
      self._renderer = Renderer(self._window)
      self._surface = Surface(self._window.size)
      self._texture = Texture(self._renderer, self._window.size)
      
      self._surface.fill(0)
      
      to_draw = BUILTIN_POLYGONS.keys()
      if not self.debug:
        to_draw = filter(lambda e: not e[0].starts_with("test_"), to_draw)
      
      for i, name in enumerate(to_draw):
        polygon = BUILTIN_POLYGONS[name]
        position = Vector2(self.icon_size * (i%self._columns), self.icon_size * (i//self._columns)) + self._position
        # print(pygame.Rect(position.x - self.icon_size//2, position.x - self.icon_size//2, self.icon_size, self.icon_size))
        # pygame.draw.rect(
        #   self._surface,
        #   0xffffff,
        #   pygame.Rect(position.x - self.icon_size//2, position.x - self.icon_size//2, self.icon_size, self.icon_size),
        #   1,
        # )
        self._icons.append(LibraryIcon(polygon, position, 0xff00ff if name.startswith("test_") else 0xffff00, name.removeprefix("test_"), self.icon_size))
        self._icons[-1].draw(self._surface, False, False)
      
      self._texture.update(self._surface)
      self._texture.draw()
      self._renderer.present()
    else:
      self._window.destroy()
      self._window = None
      self._renderer = None
      self._surface = None
      self._texture = None
      self._icons.clear()
      self._hovered = -1

  def update(self):
    if not self._is_open:
      return
    
    surface_modified = False
    mouse_pos = Vector2(pygame.mouse.get_pos()) - self._position
    hovered = int(mouse_pos.x//self.icon_size + (mouse_pos.y//self.icon_size) * self._columns)
    if hovered != self._hovered and self._hovered != -1:
      self._icons[self._hovered].draw(self._surface, False, False)
      surface_modified = True
    
    if 0 <= hovered < len(self._icons):
      self._hovered = hovered
      self._icons[hovered].draw(self._surface, False, True)
      surface_modified = True
    else:
      self._hovered = -1
    
    if surface_modified:
      self._texture.update(self._surface)
      self._texture.draw()
      self._renderer.present()
  
  def selected(self):
    if self._hovered == -1:
      return
    
    self.follow.polygon.points = [*self._icons[self._hovered]._result.points]
    self.follow.polygon.bake()


class PolygonFollowExample(PolygonFollow):
  """Inherit the Arc class to draw elements and handle keyboard and mouse"""
  def __init__(self, spacing: float, gap: float, polygon: Polygon, leader: PolygonFollower):
    super().__init__(spacing, gap, polygon, leader)
    
    self._editing_polygon: bool = False
    self._polygon_editor: PolygonEditor = PolygonEditor(polygon, Vector2(window.get_width(), window.get_height()) / 2)
    self._polygon_drawers: list[PolygonDrawer] = []
    self._draw_chord_circles: bool = True
  
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
  
  def draw(self, surface: Surface, debug=True) -> None:
    if self._editing_polygon:
      self._polygon_editor.draw(surface)
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
        surface.blit(font.render(t, False, 0xffffffff), (10, 10+20*i))
      
    
    for i, f in enumerate(self.followers):
      pygame.draw.circle(surface, (0, 255*i/fsize, 255), f.pos, f.size)
      if debug:
        pygame.draw.circle(surface, (255, 0, 0), f.pos, 3)
    
    if debug:
      for drawer in self._polygon_drawers:
        drawer.position = position
        drawer.draw(surface)
    
    if self._draw_chord_circles:
      for follower, next_ in zip(self.followers, self.followers[1:]):
        pygame.draw.circle(
          surface,
          (0, 150, 50),
          follower.pos, follower.size + next_.size + self.spacing,
          width=1
        )
    
    pygame.draw.circle(surface, (255, 0, 0), position, self.leader.size)

  def handle_keyboard(self, keys) -> bool:
    if keys[pygame.K_e]:
      self.editing_polygon = not self._editing_polygon
      return True
    
    if keys[pygame.K_p]:
      if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
        print(",\n".join(map(lambda p: repr(p)[1:-1], self.polygon.points)))
        return True
      
      result: str = askstring(
        "Configurate",
        "New points:\t\t\t\t\t\t",
        initialvalue=", ".join(map(lambda p: f"{str(p.x)};{str(p.y)}", self.polygon.points)),
      )
      
      self.polygon.points = [
        Vector2(*map(float, part.split(";")))
        for part in result.split(",")
      ] if result else []
      self.polygon.bake()
      
      return True
    
    if self._editing_polygon:
      return self.handle_keyboard_editing(keys)
    
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
    
    elif keys[pygame.K_c]:
      self._draw_chord_circles = not self._draw_chord_circles
      return True
    
    elif keys[pygame.K_s]:
      result: str = askstring(
        "Configurate",
        "New sizes:\t\t\t\t\t\t",
        initialvalue=", ".join(map(lambda f: str(f.size), self.followers)),
      )
      
      results = [
        int(float(part.strip()))
        for part in result.split(",")
      ] if result else []
      
      # Create the right amount of followers
      for _ in range(len(results) - len(self.followers)):
        self.followers.append(PolygonFollower(Vector2(), Vector2()))
      for _ in range(len(self.followers), len(results)):
        self.followers.pop()
      
      for f, size in zip(self.followers, results):
        f.size = size
      
      return True

    return False
  
  def handle_keyboard_editing(self, keys) -> bool:
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

poly = PolygonFollowExample(16, 24, Polygon(BUILTIN_POLYGONS["test_angles"].points), PolygonFollower(Vector2(100, 100), 5))
library = Library(poly)
# library.is_open = True
run = True
key_debounce: int = 0
while run:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
          run = False
        if library.is_open:
          if event.type == pygame.MOUSEBUTTONDOWN:
            library.selected()
        else:
          if event.type == pygame.MOUSEWHEEL:
            poly.handle_mouse_wheel(event)
          elif event.type == pygame.MOUSEBUTTONDOWN:
            poly.handle_mouse_down(event)
          elif event.type == pygame.MOUSEBUTTONUP:
            poly.handle_mouse_up(event)
          elif event.type == pygame.MOUSEMOTION:
            poly.handle_mouse_motion(event)
          elif event.type == pygame.VIDEORESIZE:
            poly._polygon_editor.position = Vector2(event.w, event.h) / 2
    
    if key_debounce <= 0:
      keys = pygame.key.get_pressed()
      
      key_pressed = poly.handle_keyboard(keys)
      
      if keys[pygame.K_l]:
        library.is_open = not library.is_open
        key_pressed = True
      
      if key_pressed:
        key_debounce = 1 if key_debounce == 0 else 12
    elif not any(pygame.key.get_pressed()):
      key_debounce = -1
    
    if key_debounce > -1:
      key_debounce -= 1
    
    poly.update_pos(Vector2(pygame.mouse.get_pos()))
    library.update()
    window.fill(0)
    poly.draw(window)
    pygame.display.flip()

pygame.quit()
