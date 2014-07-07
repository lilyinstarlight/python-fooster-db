import json
import os

name = 'db.py'
version = '0.1'

class HeadersError(Exception):
	pass

class HeadersMismatchError(Exception):
	pass

class Database(object):
	def __init__(self, filename, headers=None, mkdir=True):
		self.filename = filename
		self.headers = headers
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

		#If database is found, read it
		if os.path.exists(self.filename):
			self.read()
		#Else write a new (empty) one
		else:
			if not self.headers:
				raise HeadersError()

			if mkdir:
				os.makedirs(os.path.dirname(self.filename), exist_ok=True)

			self.write()

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
			headers = db.readline()[:-1].split('|')
			#Check headers to be sure this is the database we want or set them if not set already
			if self.headers:
				if headers != self.headers:
					raise HeadersMismatchError()
			else:
				self.headers = headers
			#Skip divider line
			db.readline()
			#Clear the entry dictionary and load it
			self.entries.clear()
			for line in db:
				#Magic for removing newline, splitting line by '|', using json to parse each entry, and add it to self
				self._add(*(json.loads(value) for value in line[:-1].split('|')))

	def write(self):
		with open(self.filename, 'w') as db:
			#Write header list
			headers = '|'.join(self.headers)
			db.write(headers + '\n')
			#Write divider line
			db.write('-' * len(headers) + '\n')
			#Write entry dictionary
			for entry in self:
				#Magic for going through each header in this entry, getting the entry's value for the header, using json to dump it to a string, and joining by '|'
				db.write('|'.join((json.dumps(entry.__dict__[header]) for header in self.headers)) + '\n')

	def get(self, key, default=None):
		return self.entries.get(key, default)

	def add(self, *values):
		self._add(*values)
		self.write()

	def remove(self, key):
		self._remove(key)
		self.write()
