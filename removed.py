class Trail:
	@staticmethod
	def _sliced_with_wrap(array: list, start: int, stop: int):
		start %= len(array)
		stop %= len(array)
		if start > stop:
			return (array[:stop] + array[start:], True)
		else:
			return (array[start:stop], False)