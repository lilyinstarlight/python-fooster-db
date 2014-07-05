name = 'db.py'
version = '0.1'

class Database(object):
	def __init__(self, filename):
		self.filename = filename
		self.headers = []
		self.entries = {}

		class Entry(object):
			db = self

			def __setattr__(self, key, value):
				object.__setattr__(self, key, value)
				if key in self.db.headers:
					self.db.write()

			def __delattr__(self, key):
				raise AttributeError()

		self.Entry = Entry

		self.read()

	def __iter__(self):
		return iter(self.entries.values())

	def __len__(self):
		return len(self.entries)

	def _add(self, *values):
		entry = self.Entry()
		entry.__dict__ = dict(zip(self.headers, values))
		self.entries[values[0]] = entry

	def _remove(self, key):
		del self.entries[key]

	def read(self):
		with open(self.filename, 'r') as db:
			#Get header list while removing the newline
			self.headers = db.readline()[:-1].split('|')
			#Skip divider line
			db.readline()
			#Clear the entry dictionary and load it
			self.entries.clear()
			for line in db:
				#Remove the newline before splitting
				line_values = line[:-1].split('|')
				values = []

				for value in line_values:
					if value[0] == '~':
						values.append(value[1:] == 'True')
					elif value[0] == '`':
						values.append(int(value[1:]))
					else:
						values.append(value)

				self._add(*values)

	def write(self):
		with open(self.filename, 'w') as db:
			#Write header list
			headers = '|'.join(self.headers)
			db.write(headers + '\n')
			#Write divider line
			db.write('-' * len(headers) + '\n')
			#Write entry dictionary
			for entry in self:
				values = []

				for header in self.headers:
					value = entry.__dict__[header]
					if isinstance(value, bool):
						values.append('~' + str(value))
					elif isinstance(value, int):
						values.append('`' + str(value))
					else:
						values.append(value)

				db.write('|'.join(values) + '\n')

	def get(self, key, default=None):
		return self.entries.get(key, default)

	def add(self, *values):
		self._add(*values)
		self.write()

	def remove(self, key):
		self._remove(key)
		self.write()
