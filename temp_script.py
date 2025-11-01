from django.db import connection

print('Connection settings:')
print(connection.settings_dict)
