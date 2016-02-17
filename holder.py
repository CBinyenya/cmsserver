from database import DatabaseManager
from security import Security

sec = Security()
user = sec.user
passwd = sec.password
dialect = sec.dialect
db = sec.database
database = DatabaseManager()
database.connect(dialect=dialect, user=user, passwd=passwd, database=db)
print database.get_messages()
#print database.add_payee("BRITAM")
# database.add_cheque_type("Type")
#database.add_bank("Equity")
# database.delete_cheque_type("Standard")
# database.delete_bank("Equity")
# database.delete_cheque("BRITAM")
# database.delete_payee("BRITAM")
print database.get_bank()
print database.get_payee()
print database.get_chequetype()