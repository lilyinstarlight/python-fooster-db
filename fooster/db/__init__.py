import io
import json
import re
import os
import time


__all__ = ['HeadersError', 'HeadersMismatchError', 'KeyExistsError', 'Database', 'Entry']


__version__ = '0.10.0'


# inspired by https://stackoverflow.com/a/2787979
entry_separator = re.compile(r'''\|(?=(?:[^'"]|'[^']*'|"[^"]*")*$)''')


# inspired by https://github.com/dmfrey/FileLock
class Lock(object):
    def __init__(self, filename):
        self.filename = filename

        self.lock = self.filename + '.lock'
        self.lock_fd = -1
        self.lock_delay = 0.05

        self.locked = 0

    def acquire(self):
        if self.locked:
            self.locked += 1
            return

        while True:
            try:
                self.lock_fd = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                break
            except FileExistsError:
                time.sleep(self.lock_delay)

        self.locked = 1

    def release(self):
        if not self.locked:
            return

        if self.locked > 1:
            self.locked -= 1
            return

        os.close(self.lock_fd)
        os.unlink(self.lock)

        self.locked = False

    def __enter__(self):
        self.acquire()

        return self

    def __exit__(self, type, value, traceback):
        self.release()


class HeadersError(Exception):
    pass


class HeadersMismatchError(Exception):
    pass


class KeyExistsError(KeyError):
    pass


class Entry(object):
    def __init__(self, *args, _db=None, **kwargs):
        # save db value
        self.__dict__['_db'] = _db

        if self.__dict__['_db'] is not None:
            # use embedded db to intelligently add _entry with database headers
            if len(args) + len(kwargs) < len(self.__dict__['_db'].headers):
                # missing first header
                self.__dict__['_entry'] = dict(zip(self.__dict__['_db'].headers[1:], args))
            else:
                # have all headers
                self.__dict__['_entry'] = dict(zip(self.__dict__['_db'].headers, args))
        else:
            # use numbers as position placeholders
            self.__dict__['_entry'] = dict(enumerate(args))

        # add kwargs to added args
        self.__dict__['_entry'].update(kwargs)

    def __getattr__(self, key):
        # only get known attributes
        if key not in self.__dict__['_db'].headers:
            raise AttributeError('attribute not in entry')

        # read database to get possible changes
        self.__dict__['_db'].read()

        # read from object's dictionary
        return self.__dict__['_entry'][key]

    def __setattr__(self, key, value):
        # only set known attributes
        if key not in self.__dict__['_db'].headers:
            raise AttributeError('attribute not in entry')

        # don't let database index attribute be changed
        if key == self.__dict__['_db'].headers[0]:
            raise AttributeError('index attribute is read-only')

        # read for potential database changes
        self.__dict__['_db'].read()

        # ignore same assignment to avoid write
        if self.__dict__['_entry'][key] == value:
            return

        # assign it to the object's dictionary
        self.__dict__['_entry'][key] = value

        # write database changes
        self.__dict__['_db'].write()

    def __delattr__(self, key):
        # don't allow deleting attributes
        raise AttributeError('attributes cannot be deleted')

    def __iter__(self):
        # read database to get possible changes
        self.__dict__['_db'].read()

        # iterate over _entry
        return iter(self.__dict__['_entry'].items())

    def __repr__(self):
        return 'db.Entry({})'.format(', '.join('{}={}'.format(key, repr(value)) for key, value in self.__dict__['_entry'].items()))


class Database(object):
    def __init__(self, filename, headers=None, mkdir=True):
        self.filename = filename
        self.headers = headers
        self.mkdir = mkdir

        # make parent directories if necessary
        if mkdir:
            dirname = os.path.dirname(self.filename)
            if dirname:
                os.makedirs(dirname, exist_ok=True)

        self.lock = Lock(self.filename)

        self.entries = {}

        self.mtime = 0

        if os.path.exists(self.filename):
            # read existing database
            self.read()
        else:
            # need headers if making empty database
            if not self.headers:
                raise HeadersError()

            # write empty database
            self.write()

    def __len__(self):
        self.read()

        return len(self.entries)

    def __getitem__(self, key):
        self.read()

        return self.entries[key]

    def __setitem__(self, key, value):
        # add this database if necessary
        if value.__dict__['_db'] is None:
            # if numbers were used as placeholders, replace those with actual headers
            if 0 in value.__dict__['_entry']:
                # if index value is skipped
                if len(value.__dict__['_entry']) < len(self.headers):
                    values = {self.headers[index + 1]: value for index, value in value.__dict__['_entry'].items()}
                else:
                    values = {self.headers[index]: value for index, value in value.__dict__['_entry'].items()}
            # else, use existing dictionary
            else:
                values = values.__dict__['_entry'].copy()

            # make a proper entry
            value = self.Entry(**values)

        # fix index header if it is either missing or is wrong
        value.__dict__['_entry'][self.headers[0]] = key

        # make sure headers are correct
        if set(value.__dict__['_entry'].keys()) != set(self.headers):
            raise HeadersMismatchError()

        # read for potential database changes
        self.read()

        # store it in the database
        self.entries[key] = value

        # write the database changes
        self.write()

    def __delitem__(self, key):
        self.read()

        del self.entries[key]

        self.write()

    def __iter__(self):
        self.read()

        return iter(self.entries.values())

    def __contains__(self, key):
        self.read()

        return key in self.entries

    def __repr__(self):
        return 'db.Database({}, headers={}, mkdir={})'.format(repr(self.filename), repr(self.headers), repr(self.mkdir))

    def read(self):
        # if there has been no update, do not read
        mtime = os.path.getmtime(self.filename)
        if mtime <= self.mtime:
            return

        # new entries to read into
        entries = {}

        with self.lock:
            with open(self.filename, 'r') as db:
                # get header list while removing the newline
                headers = [header.strip() for header in entry_separator.split(db.readline()[:-1])]

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
                    values = json.loads('[{}]'.format(','.join(value.strip() for value in entry_separator.split(line[:-1]))))
                    entries[values[0]] = self.Entry(**dict(zip(self.headers, values)))

        # safely update entries and mtime
        self.entries = entries
        self.mtime = mtime

    def write(self):
        # buffer for database output
        database = io.StringIO()

        # magic for going through each header in this entry, getting the entry's value for the header, and using json to dump it to a string
        rows = [[json.dumps(getattr(entry, header)) for header in self.headers] for entry in self.entries.values()]

        # column sizes
        cols = [len(header) for header in self.headers]

        # find largest column size
        for row in rows:
            for idx, value in enumerate(row):
                size = len(value)
                if size > cols[idx]:
                    cols[idx] = size

        # write header list
        headers = ' ' + ' | '.join(header.ljust(cols[idx]) for idx, header in enumerate(self.headers))
        database.write(headers.rstrip() + '\n')

        # write divider line
        database.write('-' + '-+-'.join('-'*col for col in cols) + '-' + '\n')

        # write entries
        for entry in rows:
            line = ' ' + ' | '.join(value.ljust(cols[idx]) for idx, value in enumerate(entry))
            database.write(line.rstrip() + '\n')

        # safely write database and update mtime
        with self.lock:
            with open(self.filename, 'w') as db:
                db.write(database.getvalue())
            self.mtime = os.path.getmtime(self.filename)

    def get(self, key, default=None):
        self.read()

        return self.entries.get(key, default)

    def keys(self):
        self.read()

        return self.entries.keys()

    def values(self):
        self.read()

        return self.entries.values()

    def add(self, *args, **kwargs):
        # must have index value
        if self.headers[0] in kwargs:
            key = kwargs[self.headers[0]]
        elif args:
            key = args[0]
        else:
            raise HeadersMismatchError()

        with self.lock:
            if key in self:
                raise KeyExistsError(key)
            self[key] = self.Entry(*args, **kwargs)

        return self[key]

    def remove(self, key):
        del self[key]

    def Entry(self, *args, **kwargs):
        return Entry(*args, _db=self, **kwargs)
