from peewee import MySQLDatabase
import config

db = MySQLDatabase(
    database=config.MYSQL_DATABASE,
    host=config.MYSQL_HOST,
    user=config.MYSQL_USER,
    password=config.MYSQL_PASSWORD
)

