from database import DatabaseManager
from security import Security
security = Security()
dialect = security.dialect
user = security.user
passwd = security.password
db = security.database
db = DatabaseManager()
db.connect(dialect="mysql", user=security.user, passwd=security.password, database=security.database)

print db.get_outbox()
