fooster-db
==========

fooster-db is a human-readable, magic database implemented in Python. The database presents a dictionary of first column value to entry and each entry is represented by an object where each column is an attribute. If any attribute of the entry is changed, the database file is automatically updated to represent it. The database is formatted in a human-readable table and can store JSON-serializable data structures. This project is not designed for large amounts of data or when speed is a priority, but when you need, for example, an easy way to store text data or metadata.


Usage
-----

Below is an example for a user database that demonstrates all features of the module.

```python
import fooster.db

users = fooster.db.Database('users.db', ['username', 'password', 'favorite_number', 'admin', 'friends'])

print('Users:')
for user in users:
    print(user)
print()

users['test1'] = users.Entry(password='supersecretpassword', favorite_number=None, admin=False, friends=['olduser'])
users['test2'] = fooster.db.Entry('test3', 'correcthorsebatterystaple', 7, False, ['alice', 'bob'])
admin_user = users.add('admin', 'admin|nimda', 1337, True, [])

print('Length: {}\n'.format(len(users)))

test1_user = users['test1']
test1_user.favorite_number = 1
print('User: {} ({}) - {}\n'.format(test1_user.username, test1_user.favorite_number, ', '.join(test1_user.friends)))

test2_user = users.get('test2')
test2_user.admin = True
print('User: {} ({}) - {}\n'.format(test2_user.username, test2_user.favorite_number, ', '.join(test2_user.friends)))

admin_user.friends.append(test2_user.username)

print('Users:')
for user in users:
    print(user)
print()

del users['test1']

for user in users:
    user.admin = False

print('Usernames:')
for username in users.keys():
    print(username)
print()

print('User Dict: {}\n'.format(dict(users['test2'])))

print('User Test: {}\n'.format('test2' in users))

print('User Values: {}\n'.format(users.values()))

users.remove('admin')

print('Users:')
for user in users.values():
    print(user)
print()

print('Database:\n')
with open('users.db', 'r') as file:
    print(file.read())
```
