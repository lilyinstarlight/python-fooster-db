import io
import json
import os

name = 'db.py'
version = '0.3'

class HeadersError(Exception):
    pass

class HeadersMismatchError(Exception):
    pass

class Entry(object):
    db = None

    def __init__(self, *args, **kwargs):
        if self.db != None:
            # use embedded db to intelligently update __dict__ with database headers
            if len(args) + len(kwargs) < len(self.db.headers):
                # missing first header
                self.__dict__.update(dict(zip(self.db.headers[1:], args)))
            else:
                # have all headers
                self.__dict__.update(dict(zip(self.db.headers, args)))
        else:
            # use numbers as position placeholders
            self.__dict__.update(dict(enumerate(args)))

        # add kwargs to added args
        self.__dict__.update(kwargs)

    def __getattr__(self, key):
        # only get known attributes
        if key not in self.db.headers:
            raise AttributeError('attribute not in entry')

        # read database to get possible changes
        self.db.read()

        # read from object's dictionary
        return self.__dict__[key]

    def __setattr__(self, key, value):
        # only set known attributes
        if key not in self.db.headers:
            raise AttributeError('attribute not in entry')

        # don't let database index attribute be changed
        if key == self.db.headers[0]:
            raise AttributeError('index attribute is read-only')

        # read for potential database changes
        self.db.read()

        # assign it to the object's dictionary
        self.__dict__[key] = value

        # write database changes
        self.db.write()

    def __delattr__(self, key):
        # don't allow deleting attributes
        raise AttributeError('attributes cannot be deleted')

    def __repr__(self):
        return 'db.Entry(**' + repr(self.__dict__) + ')'

class Database(object):
    def __init__(self, filename, headers=None, mkdir=True):
        self.filename = filename
        self.headers = headers
        self.mkdir = mkdir

        self.entries = {}

        self.mtime = 0

        class GenEntry(Entry):
            db = self

        self.Entry = GenEntry

        # if database is found, read it
        if os.path.exists(self.filename):
            self.read()
        # else, write an empty one
        else:
            # need headers if making empty database
            if not self.headers:
                raise HeadersError()

            # make parent directories if necessary
            if mkdir:
                dirname = os.path.dirname(self.filename)
                if dirname:
                    os.makedirs(dirname, exist_ok=True)

            self.write()

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, key):
        self.read()

        return self.entries[key]

    def __setitem__(self, key, value):
        # add this database if necessary
        if not isinstance(value, self.Entry):
            # if numbers were used as placeholders, replace those with actual headers
            if 0 in value.__dict__:
                # if index value is skipped
                if len(value.__dict__) < len(self.headers):
                    values = {self.headers[index + 1]: value for index, value in value.__dict__.items()}
                else:
                    values = {self.headers[index]: value for index, value in value.__dict__.items()}
            # else, use existing dictionary
            else:
                values = value.__dict__

            # make a proper entry
            value = self.Entry(**values)

        # fix index header if it is either missing or is wrong
        value.__dict__[self.headers[0]] = key

        # make sure headers are correct
        for ref in self.headers:
            for header in value.__dict__.keys():
                if ref == header:
                    break
            else:
                raise HeadersMismatchError()

        # read for potential database changes
        self.read()

        # store it in the database
        self.entries[key] = value

        # write the database changes
        self.write()

    def __delitem__(self, key):
        del self.entries[key]

        self.write()

    def __iter__(self):
        return iter(self.entries.values())

    def __contains__(self, key):
        return key in self.entries

    def __repr__(self):
        return 'db.Database(' + repr(self.filename) + ', ' + repr(self.headers) + ')'

    def read(self):
        # if there has been no update, do not read
        mtime = os.path.getmtime(self.filename)
        if mtime <= self.mtime:
            return

        # new entries to read into
        entries = {}

        with open(self.filename, 'r') as db:
            # get header list while removing the newline
            headers = db.readline()[:-1].split('|')

            # check headers to be sure this is the database we want or set them if not set already
            if self.headers:
                if headers != self.headers:
                    raise HeadersMismatchError()
            else:
                self.headers = headers

            # skip divider line
            db.readline()

            # read entries
            for line in db:
                # magic for removing newline, splitting line by '|', using json to parse each entry, and add it to self
                values = [json.loads(value) for value in line[:-1].split('|')]
                entries[values[0]] = self.Entry(**dict(zip(self.headers, values)))

        # safely update entries and mtime
        self.entries = entries
        self.mtime = mtime

    def write(self):
        # buffer for database output
        database = io.StringIO()

        # write header list
        headers = '|'.join(self.headers)
        database.write(headers + '\n')

        # write divider line
        database.write('-' * len(headers) + '\n')

        # write entries
        for entry in self:
            # magic for going through each header in this entry, getting the entry's value for the header, using json to dump it to a string, and joining by '|'
            line = '|'.join(json.dumps(getattr(entry, header)) for header in self.headers)
            database.write(line + '\n')

        # safely write database and update mtime
        with open(self.filename, 'w') as db:
            db.write(database.getvalue());
        self.mtime = os.path.getmtime(self.filename)

    def get(self, key, default=None):
        return self.entries.get(key, default)

    def keys(self):
        return self.entries.keys()

    def values(self):
        return self.entries.values()

    def add(self, *args, **kwargs):
        # must have index value
        if self.headers[0] in kwargs:
            key = kwargs[self.headers[0]]
        elif args:
            key = args[0]
        else:
            raise HeadersMismatchError()

        self[key] = self.Entry(*args, **kwargs)

        return self[key]

    def remove(self, key):
        del self[key]
