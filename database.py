import os
import sys
import datetime
from sqlalchemy import and_, create_engine, Column, Integer, DateTime, String, Text, LargeBinary, ForeignKey, Boolean
from sqlalchemy import exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from birthmark import BirthMarkFunctions
from security import Security
import MySQLdb as Mysql
from MySQLdb import ProgrammingError, OperationalError
from appmanager import *

Base = declarative_base()
class Cheques(Base):
    __tablename__ = "cheques"
    dt = datetime.datetime.now()
    cheque_id = Column(String(6), primary_key=True)
    cheque_number = Column(String(13))
    cheque_type = Column(String(30))
    client_name = Column(String(50), nullable=False)
    amount = Column(Integer, nullable=False)
    insu_recpt = Column(String(20))
    payee = Column(String(20))
    date = Column(DateTime, default=dt)
    due_date = Column(DateTime)
    kbima_recpt = Column(String(15))
    kbima_recpt_no = Column(String(15))
    bank = Column(String(20))
    phone = Column(String(13))

class Banks(Base):
    __tablename__ = "banks"
    bank_id = Column(Integer, primary_key=True)
    bank_name = Column(String(20), nullable=False)

class ChequeType(Base):
    __tablename__ = "cheque_type"
    type_id = Column(Integer, primary_key=True)
    type_name = Column(String(20), nullable=False)


class Payee(Base):
    __tablename__ = "payee"
    payee_id = Column(Integer, primary_key=True)
    payee_name = Column(String(20), nullable=False)


class Groups(Base):
    __tablename__ = "groups"
    group_id = Column(Integer, primary_key=True)
    group_name = Column(String(20), nullable=False)
    no_of_members = Column(Integer)
    members = relationship("Member", backref='groups')

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String(20), nullable=False)
    password = Column(String(50), nullable=False)
    firstname = Column(String(20), nullable=False)
    lastname = Column(String(20), nullable=False)
    phone = Column(String(13), nullable=False)


class Member(Base):
    __tablename__ = 'member'
    id = Column(Integer, primary_key=True)
    firstname = Column(String(20), nullable=False)
    lastname = Column(String(20))    
    phone = Column(String(13),nullable=False)
    location =  Column(String(50))
    address = Column(String(20))
    group_id = Column(Integer, ForeignKey('groups.group_id'))


class Message(Base):
    __tablename__ = "message"
    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    sender = Column(String(10), nullable=False)
    status = Column(Boolean)
    message = Column(Text)
    timedate = Column(DateTime)


class Outbox(Base):
    __tablename__ = "outbox"
    id = Column(Integer, primary_key=True)
    name = Column(String(30))
    recipient = Column(String(13), nullable=False)
    status = Column(String(10))
    message = Column(Text)
    timedate = Column(DateTime)


class Inbox(Base):
    __tablename__ = "inbox"
    id = Column(Integer, primary_key=True)
    sender = Column(String(10), nullable=False)
    status =  Column(String(10))
    message = Column(Text)
    timedate = Column(DateTime)


class BlackList(Base):
    __tablename__ = "blacklist"
    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False)
    phone = Column(String(13), nullable=False)


class Schedule(Base):
    __tablename__ = "schedule"
    schedule_id = Column(Integer, primary_key=True)
    task = Column(String(20))
    frequency = Column(Integer)
    time = Column(DateTime)
    msg_type = relationship("Config")


class Config(Base):
    __tablename__ = "config"
    config_id = Column(Integer, primary_key=True)
    msg_query = Column(String(200), nullable=False)
    recipient = Column(String(20), nullable=False)
    columns = Column(LargeBinary)
    message = Column(Text)
    schedule = Column(DateTime)      
    others = Column(LargeBinary)
    schedule_id = Column(Integer, ForeignKey("schedule.schedule_id"))


class Settings(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    company_name = Column(String(50), default="Company Messenger")
    head_quarters = Column(String(50), nullable=False, default="Nairobi")
    town = Column(String(50), nullable=False, default="Nairobi")
    mobile = Column(String(13), nullable=False)
    website = Column(String(100))
    address = Column(String(50))
    branch = Column(String(50))
    telephone = Column(String(50))
    fax = Column(String(30))
    email = Column(String(50))
    apptitle = Column(String(50))
    return_address = Column(String(50))


class ServerLog(Base):
    __tablename__ = "serverlog"
    dt = datetime.datetime.now()
    id = Column(Integer, primary_key=True)
    start_time = Column(DateTime, default=dt)
    message_loops = Column(Integer)

def create_database(con):
    try:
        con.execute("CREATE DATABASE bima")
    except ProgrammingError, e:
        pass
def default_user_details():
    path = "bin/read"
    if not os.path.exists(path):
        log.warning("Default user details are missing")
        sys.exit(1)
    with open(path, "r") as fl:
        details = fl.readlines()
        if len(details) < 2:
            log.warning("Read file is empty")
            sys.exit()
        user, password = details[:2]
    return str(user).replace('\n', ''), str(password).replace('\n', '')

def create_user(user, password):
    default = default_user_details()
    default_user, defaule_passwd = default
    con = Mysql.connect(host="localhost", user=default_user, passwd=defaule_passwd)
    cursor = con.cursor()
    query1 = "CREATE USER %s@localhost IDENTIFIED BY  '%s' " % (user, password)
    query2 = "GRANT ALL ON bima.* TO %s@localhost IDENTIFIED BY '%s'" % (user, password)
    try:
        cursor.execute(query1)
    except OperationalError, e:
        pass
    cursor.execute(query2)
    create_database(cursor)
    con.close()

    
class DatabaseManager(BirthMarkFunctions):
    def __init__(self):
        BirthMarkFunctions.__init__(self)

    def connect(self, **kwargs):
        self.conn = kwargs
        if not kwargs:            
            self.conn = {'dialect': "sqlite",
                         'database': "databases/dbquicktime.db",
                         'user': ""}
        self.user = kwargs['user']
        self.passwd = kwargs['passwd']
        create_user(self.conn["user"], self.passwd)
        self.create_database_engine()
        self.create_tables(Base)

    def create_database_engine(self):       
        
        """
        Function that creates an sqlalchemy database connection using...
            dialect,user,passwd,host,port and database arguments.
            By default the dialect of choice is the sqlite3 connection
        """

        default = {'dialect':"///",
                   'user': self.user,
                   'passwd': self.passwd,
                   'host': "localhost",
                   'port': "3306",
                   'database': ""
                   }
        dialects = {'sqlite': "///",
                    'mysql': "mysql+mysqldb",
                    'postgresql': "postgresql+psycopg2",
                    'oracle': ""}
        try:            
            dialect = dialects[self.conn['dialect']]
            
        except KeyError:
            print >>sys.stdout, "Switching to default dialect (sqlite3)"
            dialect = self.conn['dialect'] = "sqlite"
            
        default.update(self.conn)
        self.conn = default        
        passwd, host, port = self.conn['passwd'], self.conn['host'], self.conn['port']
        if self.conn['dialect'] == "sqlite":            
            string1 = "sqlite:///%s"%self.conn['database']
            self.engine = create_engine(string1)
            return self.engine
        string1 = r"%s://%s"%(dialect,self.conn['user'])    
        if self.conn['database']:
            database = "/" + self.conn['database']
        else:
            database = ""
        string = "%s:%s@%s:%s%s" % (string1, passwd, host, port, database)
        self.engine = create_engine(string)
        return self.engine

    def create_database(self):
        if self.conn['dialect'] == "sqlite":
            if os.path.exists(self.conn['database']):
                return
            try:
                with open(self.conn['database'], "w"):
                    pass
            except:
                print >>sys.stderr, "Database error, maybe the database already exists"
        else:
            self.create_database_engine()
            query = "CREATE DATABASE IF NOT EXISTS %s" % (self.conn['database'])
            self.engine.execute(query)
            
    def execute_query(self, query):
        try:
            self.engine.execute(query)
        except exc.ProgrammingError, e:
            pass

    def create_tables(self, base):
        Base = base
        Base.metadata.create_all(self.engine)
        if any(self.engine.execute("select * from user where username like 'Admin'")):
            return "Users available"
        else:
            self.add_user((self.user, self.passwd, "Monte", "Caleb", "+254704236788"))
            self.add_user(("admin", "passwd", "Harry", "Gathogo", "+254722341870"))
            
    def get_session(self):
        session = sessionmaker(bind=self.engine)
        session = session()
        return session

    def add_server_log(self, args):
        details = ServerLog(start_time=args[0], message_loops=0)
        session = self.get_session()
        session.add(details)
        session.commit()
        return True
    
    def add_company_details(self, args):
        details = Settings(company_name=args[0], head_quarters=args[1], town=args[2], mobile=args[3], website=args[4],
                           address=args[5], branch=args[6], telephone=args[7], fax=args[8], email=args[9],
                           apptitle=args[10], return_address=args[11])
        session = self.get_session()
        session.add(details)
        session.commit()
        return True

    def add_cheque(self, args):
        last_id = self.engine.execute("select cheque_id from cheques order by date")

        def cheque(id_):
            id_ = int(id_) + 1
            zeros = "0" * (6 - len(str(id_)))
            id_ = zeros + str(id_)
            return id_
        for _id in last_id:
            last_id = _id[0]
            last_id = cheque(last_id)
        if not isinstance(last_id, str):
            last_id = "000001"
        details = Cheques(cheque_id=last_id, cheque_type=args[11], client_name=args[0], cheque_number=args[1], amount=args[2], insu_recpt=args[3],
                         payee=args[4], date=args[5], due_date=args[6], kbima_recpt=args[7], kbima_recpt_no=args[8],
                         bank=args[9], phone=args[10])


        session = self.get_session()
        session.add(details)
        session.commit()
        return True

    def add_bank(self, arg):
        details = Banks(bank_name=arg)
        session = self.get_session()
        session.add(details)
        session.commit()
        return True

    def add_cheque_type(self, arg):
        details = ChequeType(type_name=arg)
        session = self.get_session()
        session.add(details)
        session.commit()
        return True

    def add_payee(self, arg):
        details = Payee(payee_name=arg)
        session = self.get_session()
        session.add(details)
        session.commit()
        return True

    def add_user(self,details):
        dt = details
        sql = "select * from user where username LIKE '%s'" % (dt[0])
        sql2 = "select * from user where password LIKE '%s'" % (dt[1])
        
        if any(self.engine.execute(sql)):
            response = ("Error", "Username is invalid")
            return response
        
        if any(self.engine.execute(sql2)):
            response = ("Error", "Password is invalid")
            return response
        
        new_user = User(username=dt[0], password=dt[1], firstname=dt[2], lastname=dt[3],
                        phone=dt[4])
        session = self.get_session()
        session.add(new_user)
        session.commit()
        return True
    
    def add_group(self, name):
        try:
            new_group = Groups(group_name=name)
            session = self.get_session()
            session.add(new_group)
            session.commit()
            return True,"New group created"
        except:
            return False, "Group could not be created"

    def add_member(self, dt):
        try:
            new_member = Member(firstname=dt[0], lastname=dt[1], phone=dt[2], location=dt[3],
                                address=dt[4], group_id=dt[5])
            session = self.get_session()
            session.add(new_member)
            session.commit()
            return True, "Server added new member"
        except:
            return False, "Member could not be added"

    def add_messages(self, dt):
        try:         
            new_message = Message(type=dt[0], sender=dt[1], status=dt[2], message=dt[3], timedate=dt[4])
            session = self.get_session()
            session.add(new_message)
            session.commit()
            return True
        except:
            return False

    def add_configurations(self, dt):
        try:         
            new_message = Config(msg_type=dt[0], msg_query=dt[1], recipient=dt[2], columns=dt[3],
                                message=dt[4], schedule=dt[5], others=dt[6])
            session = self.get_session()
            session.add(new_message)
            session.commit()
            return True
        except:
            return False

    def add_dict(self, dt):
        try:
            session = self.get_session()
            session.query(Config).filter_by(msg_type=dt[0]).update({dt[1]: dt[2]})
            session.commit()
            return True
        except:
            return False

    def add_schedule(self, dt):
        try:         
            new_schedule = Schedule(task=dt[0], frequency=dt[1], time=dt[2])
            session = self.get_session()
            session.add(new_schedule)
            session.commit()
            return True
        except:
            return False

    def add_outbox(self, dt):
        try:
            new_message = Outbox(name=dt[0], recipient=dt[1], status=dt[2], message=dt[3], timedate=dt[4])
            session = self.get_session()
            session.add(new_message)
            session.commit()
            return True
        except EOFError:
            return False

    def add_inbox(self, dt):
        try:
            new_message = Inbox(sender=dt[0], status=dt[1], message=dt[2], timedate=dt[3])
            session = self.get_session()
            session.add(new_message)
            session.commit()
            return True
        except:
            return False

    def add_blacklist(self, dt):
        try:
            black = BlackList(name=dt[0], phone=dt[1])
            session = self.get_session()
            session.add(black)
            session.commit()
            return True
        except:
            return False

    def update_user(self, dt):
        try:
            session = self.get_session()
            session.query(User).filter_by(username=dt[0]).update({dt[1]: dt[2]})
            session.commit()
            return True
        except:
            return False

    def update_group(self, dt):
        try:
            session = self.get_session()
            session.query(Groups).filter_by(group_name=dt[0]).update({dt[1]: dt[2]})
            session.commit()
            return True
        except:
            return False

    def update_member(self, dt):
        try:
            session = self.get_session()
            session.query(Member).filter_by(phone=dt[0]).update({dt[1]: dt[2]})
            session.commit()
            return True
        except:
            return False

    def update_message(self, dt):
        try:
            session = self.get_session()
            session.query(Message).filter(and_(
                Message.message == dt[0],
                Message.timedate == dt[1])).update({dt[2]: dt[3]})
            session.commit()
            return True
        except:
            return False

    def update_outbox(self, dt):
        session = self.get_session()
        session.query(Outbox).filter(and_(
            Outbox.recipient == dt[0],
            Outbox.message == dt[1])).update({Outbox.status: "sent"})
        session.commit()

    def get_users(self, who="all"):
        session = self.get_session()
        if who == "all":
            users = session.query(User).all()
        else:
            pass
            users = session.query(User)
        session.commit()
        users_list = []
        for user in users:
            diction = dict()
            diction['username'] = user.username
            diction['passwd'] = user.password
            diction['fname'] = user.firstname
            diction['lastname'] = user.lastname
            diction['phone'] = user.phone
            users_list.append(diction)
            
        return users_list

    def get_user_details(self, detail_type):
        all_users = {}
        try:
            if detail_type == "users":
                result = self.engine.execute("SELECT username,firstname,lastname  FROM user")
                
                for users in result:
                    all_users[users[0]]="%s %s"%(users[1],users[2])
            elif detail_type == "passwords":
                result = self.engine.execute("SELECT username,password  FROM user")
                for users in result:
                    all_users[users[0]] = "%s" % (users[1])
                    
            elif detail_type == "allusers":
                all_users = []
                result = self.engine.execute("SELECT username,firstname,lastname,password  FROM user")
                for users in result:
                    diction = dict()
                    diction["username"], diction["fname"], diction["lname"], diction["passwd"] = users[0], users[1],\
                                                                                                 users[2], users[3]
                    all_users.append(diction)
            
            else:
                pass
            
        except:
            pass
            
        finally:
            return all_users

    def get_group_members(self, who="all"):
        session = self.get_session()
        if who == "all":
            members = session.query(Member).all()
        else:
            return
        session.commit()
        member_list = []
        groups = self.get_groups()
        for i in members:
            diction = dict()
            diction['Id_no'] = i.id
            diction["Name"] = "%s %s"%(i.firstname,i.lastname)
            diction['Phone'] = i.phone
            diction['City'] = i.location
            diction['Address'] = i.address
            for group in groups:
                if int(group[0]) == int(i.group_id):
                       diction['Group'] = group[1]
            member_list.append(diction)
        
        return "Clients", "Found %d clients" % len(member_list), member_list

    def get_messages(self, which="all"):
        session = self.get_session()
        if which == "all":
            messages = session.query(Message).all()
        else:
            messages = session.query(Message).filter_by(Message.status == which)
        msgs = list()
        for msg in messages:
            msg_dict = dict()
            msg_dict['Type'] = msg.type
            msg_dict['Sender'] = msg.sender
            msg_dict['Status'] = msg.status
            msg_dict['Message'] = msg.message
            msg_dict['Time'] = msg.timedate
            msgs.append(msg_dict)
        session.commit()        
        return msgs

    def get_bank(self):
        session = self.get_session()
        banks = session.query(Banks).all()
        bank_list = list()
        for bank in banks:
            bank_list.append(bank.bank_name)
        session.commit()
        return bank_list

    def get_payee(self):
        session = self.get_session()
        payees = session.query(Payee).all()
        payee_list = list()
        for payee in payees:
            payee_list.append(payee.payee_name)
        session.commit()
        return payee_list

    def get_schedules(self, which="all"):
        session = self.get_session()
        if which == "all":
            schedules = session.query(Schedule).all()
        else:
            pass
            schedules = session.query(Schedule)
        session.commit()        
        return schedules

    def get_config(self, which="all"):
        session = self.get_session()
        if which == "all":
            messages = session.query(Config).all()
        else:
            messages = session.query(Config).filter(Config.recipient == which)
            messages = session.query(Config)
        session.commit()        
        return messages

    def get_groups(self, which="all"):
        session = self.get_session()
        if which == "all":
            groups = session.query(Groups).all()
        else:
            pass
            groups = session.query(Groups)
        session.commit()
        group_list = []
        for group in groups:            
            group_list.append((group.group_id, group.group_name))
        return group_list

    def get_settings(self):
        session = self.get_session()
        settings = session.query(Settings).all()
        session.commit()
        try:
            settings = settings[-1]
        except:
            return {}
        cd = dict()
        cd["Name:"] = settings.company_name
        cd["Address:"] = settings.address
        cd["H.Quarters:"] = settings.head_quarters
        cd["Branch:"] = settings.branch
        cd["Town:"] = settings.town
        cd["Telephone"] = settings.telephone
        cd["Mobile:"] = settings.mobile
        cd["Fax:"] = settings.fax
        cd["Website:"] = settings.website
        cd["E-mail:"] = settings.email
        cd["apptitle"] = settings.apptitle
        cd["return"] = settings.return_address
        
        return cd

    def get_group_names(self, groups=""):
        names = []
        for group in self.get_groups():
            names.append(group[1])
        return [True, "Found %d groups" % len(names), names]

    def get_outbox(self, sieve=False):
        messages = []
        session = self.get_session()
        if sieve:
            outbox = session.query(Outbox).filter(Outbox.status == "waiting")
        else:
            outbox = session.query(Outbox).all()        
        session.commit()        
        for msg in outbox:
            diction = dict()
            diction['name'] = msg.name
            diction['phone'] = msg.recipient
            diction['status'] = msg.status
            diction['message'] = msg.message
            diction['date'] = msg.timedate
            messages.append(diction)
        return messages

    def get_outbox_similar(self, dt):
        session = self.get_session()
        outbox = session.query(Outbox).filter(and_(
            Outbox.recipient == dt[0],
            Outbox.message == dt[1]))
        if len(outbox) > 1:
            for msg in outbox:
                pass
        session.commit()
    
    def get_blacklist(self):
        session = self.get_session()
        blacklist = session.query(BlackList).all()
        session.commit()
        black_list = []
        for black in blacklist:            
            diction = dict()
            diction['name'] = black.name
            diction['phone'] = black.phone
            black_list.append(diction)
        return black_list

    def get_cheques(self):
        session = self.get_session()
        cheques = session.query(Cheques).all()
        cheque_list = list()
        for cheque in cheques:
            cheque_dict = dict()
            cheque_dict['Id'] = cheque.cheque_id
            cheque_dict['Number'] = cheque.cheque_number
            cheque_dict['Type'] = cheque.cheque_type
            cheque_dict['Name'] = cheque.client_name
            cheque_dict['Amount'] = cheque.amount
            cheque_dict['Recpt'] = cheque.insu_recpt
            cheque_dict['Payee'] = cheque.payee
            cheque_dict['Date'] = cheque.date
            cheque_dict['Due'] = cheque.due_date
            cheque_dict['Kbimarecpt'] = cheque.kbima_recpt
            cheque_dict['Kbimarecptno'] = cheque.kbima_recpt_no
            cheque_dict['Bank'] = cheque.bank
            cheque_dict['Phone'] = cheque.phone
            cheque_list.append(cheque_dict)
        session.close()
        return cheque_list

    def get_chequetype(self):
        session = self.get_session()
        cheques = session.query(ChequeType).all()
        cheque_list = list()
        for cheque in cheques:
            cheque_list.append(cheque.type_name)
        session.commit()
        return cheque_list

    def delete_all(self, what):
        session = self.get_session()        
        if what == "users":
            session.query(User).delete()
        elif what == "members":
            session.query(Member).delete()
        elif what == "groups":
            session.query(Groups).delete()
        elif what == "messages":
            session.query(Message).delete()
        elif what == "outbox":
            session.query(Outbox).delete()
        elif what == "cheques":
            session.query(Cheques).delete()
        elif what == "banks":
            session.query(Banks).delete()
        session.commit()
        return

    def delete_bank(self, arg):
        session = self.get_session()
        session.query(Banks).filter(Banks.bank_name == arg).delete()
        session.commit()
        return True

    def delete_group(self, gname):
        session = self.get_session()
        session.query(Groups).filter(Groups.group_name == gname).delete()
        session.commit()
        return True
            
    def delete_member(self, phone):
        try:
            session = self.get_session()
            session.query(Member).filter(Member.phone == phone).delete()
            session.commit()
            return True
        except:
            return False

    def delete_config(self, name):
        session = self.get_session()
        session.query(Config).filter(Config.msg_type == name).delete()
        session.query(Schedule).filter(Schedule.task == name).delete()
        session.commit()
        return True
        
    def delete_blacklist(self, phone):
        try:                
            session = self.get_session()
            session.query(BlackList).filter(BlackList.phone == phone).delete()
            session.commit()
            return True
        except:
            return False

    def delete_cheque(self, arg):
        session = self.get_session()
        session.query(Cheques).filter(Cheques.cheque_number == arg).delete()
        session.commit()
        return True

    def delete_cheque_type(self, arg):
        session = self.get_session()
        session.query(ChequeType).filter(ChequeType.type_name == arg).delete()
        session.commit()
        return True

    def delete_payee(self, arg):
        session = self.get_session()
        session.query(Payee).filter(Payee.payee_name == arg).delete()
        session.commit()
        return True

    def queries(self, dt):
        if any(self.engine.execute("select * from user where username like 'Admin'")):
            return "Users available"
        else:
            return "Error"
    def get_appdetails(self):
        self.get_messages()

if __name__ == "__main__":
    db = DatabaseManager()
    sec = Security()
    username = sec.user
    password = sec.password
    db.connect(dialect="mysql", user=username, passwd=password, database="bima")