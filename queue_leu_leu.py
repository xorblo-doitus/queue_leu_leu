import math, pygame, random

class TrailElement:
	def __init__(self, xy: pygame.Vector2, size: float):
		self.xy = xy
		self.size = size

class Trail:
	def __init__(self, distance_between_pos, leader_pos, leader_size, spacing):
		self.leader = TrailElement(leader_pos, leader_size)
		self.followers: list[TrailElement] = []
		self.distance_between_pos = distance_between_pos
		self.spacing = spacing
		self._i = 0
		self.trail: list[pygame.Vector2] = [self.leader.xy]
		
		self._adapt_trail_len()
		# self._increase_trail(
		# 	0,
		# 	math.ceil(self.get_total_size() / self.distance_between_pos) + 1 - len(self.trail),
		# 	self.leader.xy
		# )

	def update_leader_pos(self, new_position):
		self.leader.xy = new_position
		
		current_pos = self.trail[self._i]
		while self.trail[self._i].distance_to(new_position) >= self.distance_between_pos:
			current_pos = current_pos.move_towards(new_position, self.distance_between_pos)
			self._i = self._wrapped(self._i - 1)
			self.trail[self._i] = current_pos
			
		self.update_trail()
		
	def update_trail(self):
		trail_advancment: float = self.leader.size + self.spacing - self.leader.xy.distance_to(self.trail[self._i])
		tsize = len(self.trail)
		
		for follower in self.followers:
			trail_advancment += follower.size
			i_advancement: float = self._i + trail_advancment / self.distance_between_pos
			follower.xy = pygame.Vector2.lerp(
				self.trail[self._wrapped(math.ceil(i_advancement % tsize))],
				self.trail[self._wrapped(int(i_advancement % tsize))] if trail_advancment >= 0 else self.leader.xy,
				1 - (i_advancement % 1)
			)
			trail_advancment += follower.size + self.spacing

	def add_follower(self, xy, size):
		self.followers.append(TrailElement(xy, size))
		
		self._adapt_trail_len()
		
		self.update_trail()
		# self._increase_trail(
		# 	self._wrapped(self._i - 1),
		# 	math.ceil(self.get_total_size() / self.distance_between_pos) + 1 - len(self.trail),
		# 	self.trail[self._wrapped(self._i - 1)]
		# )

	def remove_follower(self, index=-1):
		if self.followers:
			element = self.followers.pop(index)

			self._adapt_trail_len()
			# to_remove = len(self.trail) - 1 - math.ceil(self.get_total_size() / self.distance_between_pos)

			self.update_trail()
	
	def resize_follower(self, index: int, new_size: float):
		self.followers[index].size = new_size
		self._adapt_trail_len()
	
	def _wrapped(self, i):
		return i % len(self.trail)
	
	def _adapt_trail_len(self):
		delta = math.ceil(self.get_total_size() / self.distance_between_pos) + 1 - len(self.trail)
		
		if delta > 0:
			self._increase_trail(self._i - 1, delta, self.trail[self._wrapped(self._i - 1)])
		elif delta < 0:
			self._decrease_trail(-delta)
	
	def _increase_trail(self, at, amount, position):
		for _ in range(amount): self.trail.insert(at, position)
		if self._i > at: self._i += amount
	
	def _decrease_trail(self, amount):
		self.trail = [
			self.trail[i]
			for i in range(self._i - len(self.trail), self._i - amount)
		]
		self._i = 0
	
	def _get_lenght(self, size):
		return 2 * size + self.spacing
	
	def _get_lenght_in_trail(self, size):
		return self._get_lenght(size) / self.distance_between_pos
	
	def get_total_size(self):
		return self.leader.size + self.spacing * len(self.followers) + 2 * sum(map(lambda element: element.size, self.followers))
	
	def draw(self):
		#debug
		window.blit(font.render(f"_i: {self._i} / {len(self.trail)}", False, 0xffffffff), (10, 10))
		window.blit(font.render("len(_trail_elements): " + str(len(self.followers)), False, 0xffffffff), (10, 30))
		# window.blit(font.render("len(_trail_positions): " + str(self.trail_positions_count), False, 0xffffffff), (10, 50))
		
		for i, t in enumerate(self.followers):
			pygame.draw.circle(window, (255*i/len(self.followers), 100, 0), t.xy.xy, t.size)
		
		for pos in self.trail:
			pygame.draw.circle(window, (255, 0, 0), pos.xy, 3)


pygame.init()
window = pygame.display.set_mode((500, 500), pygame.RESIZABLE)
clock = pygame.time.Clock()
trail = Trail(100, pygame.Vector2(100, 100), 5, 25)
font = pygame.font.SysFont('Arial', 16)


run = True
while run:
		clock.tick(60)
		for event in pygame.event.get():
				if event.type == pygame.QUIT:
						run = False

		keys = pygame.key.get_pressed()
		if keys[pygame.K_RETURN]:
			trail.add_follower(pygame.Vector2(100, 100), random.randint(6, 30))
			pygame.time.delay(100)
		if keys[pygame.K_BACKSPACE] and trail.followers:
			trail.remove_follower(random.randint(0, len(trail.followers)-1))
			pygame.time.delay(100)
			pygame.time.delay(100)
		if keys[pygame.K_KP_PLUS] and trail.followers:
			trail.resize_follower(random.randint(0, len(trail.followers)-1), random.randint(32, 64))
			pygame.time.delay(100)
		if keys[pygame.K_KP_MINUS] and trail.followers:
			trail.resize_follower(random.randint(0, len(trail.followers)-1), random.randint(2, 4))
			pygame.time.delay(100)

		trail.update_leader_pos(pygame.Vector2(pygame.mouse.get_pos()))
		window.fill(0)
		trail.draw()
		pygame.draw.circle(window, (255, 0, 0), pygame.mouse.get_pos(), 5)
		pygame.display.flip()

pygame.quit()
