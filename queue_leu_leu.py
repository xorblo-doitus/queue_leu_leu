import math, pygame, random

SUPERFLUOUS_LENGTH_FOR_APPROX_ERROR = 16.0

class TrailElement:
	def __init__(self, xy, radius):
		self.xy = xy
		self.radius = radius

class Trail:
	def __init__(self, initial_pos, leader_radius):
		self.positions: "list[pygame.Vector2]" = [initial_pos]
		self.trail_positions_count = -999
		self.minimum_distance = 20.0
		self._i = 0
		self._trail_elements = []
		self.leader_radius = leader_radius
		self._increase_positions_len(0, math.ceil(leader_radius / self.minimum_distance), initial_pos)
		self.trail_positions_count = 0

	def update_leader_pos(self, new_position):
		actual_pos = pygame.Vector2(self.positions[self._i])
		while self.positions[self._i].distance_to(new_position) >= self.minimum_distance:
			self._i = self._wrapped(self._i - 1)
			self.positions[self._i] = actual_pos.move_towards(new_position, self.minimum_distance)
			actual_pos = self.positions[self._i]
		self.update_trails_positions()

	def _wrapped(self, i):
		if i < 0:
			return len(self.positions) - abs(i) % len(self.positions)
		return i % len(self.positions)

	def add_trail_element(self, xy, radius):
		self._trail_elements.append(TrailElement(xy, radius))
		
		self._increase_positions_len(
			self._wrapped(self._i - 1),
			math.ceil((self.get_trail_length() + SUPERFLUOUS_LENGTH_FOR_APPROX_ERROR + 2 * radius) / self.minimum_distance) - self.trail_positions_count,
			self.positions[self._wrapped(self._i - 1)]
		)

	def remove_trail_element(self, i=-1):
		if self._trail_elements:
			element: TrailElement = self._trail_elements.pop(i)
			to_remove = self.trail_positions_count - math.ceil((self.get_trail_length() + SUPERFLUOUS_LENGTH_FOR_APPROX_ERROR - 2 * element.radius) / self.minimum_distance)
			# to_remove = math.ceil(2 * element.radius / self.minimum_distance)
			
			print(to_remove)
			print(len(self.positions))
			
			self.positions = [
				self.positions[i]
				for i in range(self._i - len(self.positions), self._i - to_remove)
			]
			print(len(self.positions))
			self._i = 0
			self.trail_positions_count -= to_remove
			
			self.update_trails_positions()

	def _increase_positions_len(self, at, amount, position):
		self.trail_positions_count += amount
		for _ in range(amount):
			self.positions.insert(at, position)
		if self._i > at:
			self._i += amount

	def update_trails_positions(self):
		i = self._i + self.leader_radius / self.minimum_distance
		_len = len(self.positions)
		for trail_element in self._trail_elements:
			i += trail_element.radius / self.minimum_distance
			trail_element.xy = pygame.Vector2.lerp(
				self.positions[self._wrapped(math.ceil(i % _len))],
				self.positions[self._wrapped(int(i % _len))],
				1 - (i % 1)
			)
			i += trail_element.radius / self.minimum_distance
	
	
	def get_trail_length(self):
		return 2 * sum(map(lambda element: element.radius, self._trail_elements))
	
	def get_total_length(self):
		return self.get_total_length() + self.leader_radius
	
	def draw(self):
		#debug
		window.blit(font.render(f"_i: {self._i} / {len(self.positions)}", False, 0xffffffff), (10, 10))
		window.blit(font.render("len(_trail_elements): " + str(len(self._trail_elements)), False, 0xffffffff), (10, 30))
		window.blit(font.render("len(_trail_positions): " + str(self.trail_positions_count), False, 0xffffffff), (10, 50))
		
		for i, t in enumerate(self._trail_elements):
			pygame.draw.circle(window, (255*i/len(self._trail_elements), 100, 0), t.xy.xy, t.radius)
		
		for pos in self.positions:
			pygame.draw.circle(window, (255, 0, 0), pos.xy, 3)

pygame.init()
window = pygame.display.set_mode((500, 500))
clock = pygame.time.Clock()
trail = Trail(pygame.Vector2(100, 100), 5)
font = pygame.font.SysFont('Arial', 16)

run = True
while run:
		clock.tick(60)
		for event in pygame.event.get():
				if event.type == pygame.QUIT:
						run = False
		
		keys = pygame.key.get_pressed()
		if keys[pygame.K_RETURN]:
			trail.add_trail_element(pygame.Vector2(100, 100), random.randint(5, 20))
			pygame.time.delay(100)
		if keys[pygame.K_BACKSPACE]:
			trail.remove_trail_element(-1)
			pygame.time.delay(100)
		
		trail.update_leader_pos(pygame.mouse.get_pos())
		window.fill(0)
		trail.draw()
		pygame.draw.circle(window, (255, 0, 0), pygame.mouse.get_pos(), 5)
		pygame.display.flip()

pygame.quit()