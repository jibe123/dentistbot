from decouple import config
# MYSQL
MYSQL_DATABASE = config('MYSQL_DATABASE')
MYSQL_USER = config('MYSQL_USER')
MYSQL_PASSWORD = config('MYSQL_PASSWORD')
MYSQL_HOST = config('MYSQL_HOST')

# TELEGRAM BOT
ADMIN_USER_ID = config('ADMIN_USER_ID')
TOKEN = config('TOKEN')