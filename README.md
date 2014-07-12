db.py
=====
db.py is a human-readable, magic database implemented in Python. The database presents a dictionary of first column value to entry and each entry is represented by an object where each column is an attribute. If any attribute of object is changed, the database file is automatically updated to represent it. The database is formatted in a human-readable table and can store most built-in Python data structures. This project is not designed for large amounts of data or when speed is a top priority, but when you need, for example, an easy way to store text data or metadata.

Usage
-----
Below is an example for a user database that demonstrates all features of the module.

```python
import db

users = db.Database('users.db', [ 'username', 'password', 'age', 'admin', 'friends' ])

users.add('testuser', 'supersecretpassword', None, False, [ 'olduser' ])
users.add('xkcd', 'correcthorsebatterystaple', 9, False, [ 'alice', 'bob' ])
admin_user = users.add('admin', 'admin', 30, True, [])

with open('users.db', 'r') as file:
	print(file.read())

print(str(len(users)) + '\n')

xkcd_user = users.get('xkcd')
xkcd_user.admin = True
print(xkcd_user.username + ' (' + str(xkcd_user.age) + ') - ' + ', '.join(xkcd_user.friends) + '\n')

admin_user.friends.append(xkcd_user.username)

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
