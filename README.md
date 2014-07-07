db.py
=====
db.py is a human-readable, magic database implemented in Python. The database is in a simple table format indexed by the first column and the entries are utilized as objects with their database values as attributes. Supported attribute types are str, list of str, int, and bool. The database file is automatically kept up to date with all changes to the entry objects and any manipulation of the database.

Usage
-----
Below is usage for a user database that demonstrates all features of the module.

users.db:
```
username|password|age|admin|friends
-----------------------------------
"olduser"|"password"|100|false|[]
```

users.py:
```
import db

users = db.Database('users.db')

users.add('testuser', 'supersecretpassword', None, False, [ 'olduser' ])
users.add('xkcd', 'correcthorsebatterystaple', 9, False, [ 'alice', 'bob' ])
users.add('admin', 'admin', 30, True, [ 'xkcd' ])

with open('users.db', 'r') as file:
	print(file.read())

print(str(len(users)) + '\n')

user = users.get('xkcd')
user.admin = True
print(user.username + ' (' + str(user.age) + ') - ' + ', '.join(user.friends) + '\n')

with open('users.db', 'r') as file:
	print(file.read())

users.remove('testuser')

with open('users.db', 'r') as file:
	print(file.read())

for user in users:
	user.admin = False

with open('users.db', 'r') as file:
	print(file.read())
```
