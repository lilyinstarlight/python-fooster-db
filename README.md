db.py
=====
db.py is a human-readable, magic database implemented in Python. The database presents a dictionary of first column value to entry and each entry is represented by an object where each column is an attribute. If any attribute of object is changed, the database file is automatically updated to represent it. The database is formatted in a human-readable table and can store most built-in Python data structures. This project is not designed for large amounts of data or when speed is a top priority, but when you need, for example, an easy way to store text data or metadata.

Usage
-----
Below is an example for a user database that demonstrates all features of the module.

```python
import db

users = db.Database('users.db', ['username', 'password', 'age', 'admin', 'friends'])

for user in users.values():
    print(user)
print()

users['testuser'] = users.Entry('supersecretpassword', None, False, ['olduser'])
users['xkcd'] = db.Entry('xkcd', 'correcthorsebatterystaple', 9, False, ['alice', 'bob'])
admin_user = users.add('admin', 'admin|nimda', 30, True, [])

print('Length: ' + str(len(users)) + '\n')

xkcd_user = users['xkcd']
xkcd_user.admin = True
print('User: ' + xkcd_user.username + ' (' + str(xkcd_user.age) + ') - ' + ', '.join(xkcd_user.friends) + '\n')

test_user = users.get('testuser')
for user in users:
	print(user)
test_user.admin = True
print('User: ' + test_user.username + ' (' + str(test_user.age) + ') - ' + ', '.join(test_user.friends) + '\n')

admin_user.friends.append(xkcd_user.username)

users.remove('testuser')

for user in users:
    user.admin = False

for username in users.keys():
    print(username)

print('xkcd' in users)

print(users.values())
print()

del users['admin']

print('Database:\n')
with open('users.db', 'r') as file:
    print(file.read())
```
