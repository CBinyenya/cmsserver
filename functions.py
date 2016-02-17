import os
import re
import wx
import sys
import pyodbc
import sqlite3
import MySQLdb
from time import strftime, strptime, ctime
import cPickle as pickle
from contextlib import closing





class Configuration(object):
    """
    Manages application settings
    """
    def __init__(self):
        self.filename = 'bin/config'
        self.init()

    def init(self):
        now = ctime()
        self.write("install", [now])

    def read(self):
        try:
            os.mkdir('bin')
            return {}
        except WindowsError:
            try:
                with closing(open(self.filename, 'rb')) as fl:
                    try:
                        data = pickle.load(fl)
                        return data
                    except EOFError:
                        print >>sys.stderr, "Empty file!"
                        return {}
            except IOError:
                print >>sys.stderr, "Configuration file is missing"
                with closing(open(self.filename, 'wb')) as fl:
                    pass
                return {}

    def write(self, name, value):
        data = self.read()
        if name == "queries":
            try:
                if data[name][0] == value[0]:
                    data[name].append(value[1])
                    print data[name]
            except KeyError:
                data["queries"] = value
        else:
            data[name] = value
        with closing(open(self.filename, 'wb')) as fl:
            pickle.dump(data, fl)

        return True


class Filemanagement(object):

    def __init__(self,name):
        self.filename = 'data/%s' % name

    def read(self):
        print "reading data from", self.filename
        try:
            os.mkdir('data')
            return []
        except WindowsError:
            try:
                with closing(open(self.filename, 'rb')) as fl:
                    try:
                        data = pickle.load(fl)
                        return data
                    except EOFError:
                        print >>sys.stderr, "Empty file!"
                        return []
            except IOError:
                print >>sys.stderr, "Configuration %s is missing" % self.filename
                return []

    def write(self, data):
        with closing(open(self.filename, 'wb')) as fl:
            pickle.dump(data, fl)
        return True


class Database(Configuration):
    """Manages all database connections and transactions"""

    def __init__(self):
        self.DSN = ''
        self.odbc_passwd = ''
        self.mysql_database = ''
        self.user = ''
        self.mysql_passwd = ''
        self.mysql_port = "localhost"
        self.sqlite_database = "qtmdatabase"
        Configuration.__init__(self)

    def Init(self):
        try:
            self.DSN, self.odbc_passwd = self.read()['pyodbc']
        except KeyError:
            self.write("pyodbc", ("BirthMarkdb", "linet"))
            self.DSN, self.passwd = ("BirthMarkdb", "linet")
        try:
            self.mysql_port, self.user, self.mysql_passwd, self.mysql_database = self.read()['mysql']
        except KeyError:
            self.write("mysql", ("localhost", "qtminsu", "creawib", "qtmdatabase"))
            self.mysql_port, self.user, self.mysql_passwd, self.mysql_database = self.read()['mysql']

    def testConnection(self, db, conn_string):
        print >>sys.stdout, "Testing database connection"
        if db == "MYSQL":
            try:
                all_tables = []
                if conn_string[-1]:
                    try:
                        conn = MySQLdb.connect(conn_string[0], conn_string[1], conn_string[2], conn_string[-1])
                    except MySQLdb.OperationalError:
                        conn = MySQLdb.connect(conn_string[0], conn_string[1], conn_string[2])
                        cursor = conn.cursor()
                        cursor.execute("CREATE DATABASE IF NOT EXISTS dbquicktime")
                        conn.close()
                        print "Connect without db"
                    self.write("mysql", (conn_string[0], conn_string[1], conn_string[2], conn_string[-1]))
                    cursor = conn.cursor()
                    string = "mysql://%s:%s@%s/%s" % (conn_string[0], conn_string[1], conn_string[2], conn_string[-1])
                    self.write("connect", string)
                    tables = self.getTables(conn_string[-1], cursor)
                    conn.close()
                    return [table[0] for table in tables]
                else:
                    MySQLdb.connect(conn_string[0], conn_string[1], conn_string[2])
                return True
            except IOError:
                return False
        elif db == "ODBC":
            try:
                conn = pyodbc.connect(DSN=conn_string[-1], PWD=conn_string[-2])
                cursor = conn.cursor()
                tables = self.getTables(conn_string[-1], cursor)
                conn.close()
                print tables
                return tables
            except IOError:
                return False
            except pyodbc.Error, e:
                print >>sys.stderr, e[1]
                return False

    def getTables(self, db, cursor):
        if db != "BirthMarkdb":
            print db
            cursor.execute("use %s" % db)
        cursor.execute("SHOW TABLES")
        return cursor.fetchall()

    def getColumns(self, type, table):
        if type == "ODBC":
            conn, cursor = self.pyodbConnection()
        else:
            conn, cursor = self.mysqlConnection()
        cursor.execute("DESCRIBE %s" % table)
        columns = cursor.fetchall()
        return columns

    def saveQuery(self, db, content):
        """Saves a tuple of a list of query name,a list of columns and the query string"""
        self.write(db, content)

    def createQuicktimedb(self):
        conn = MySQLdb.connect(self.mysql_port, self.user, self.mysql_passwd)
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE quicktimedb")
        conn.close()

    def pyodbConnection(self):
        """Returns the conn, and cursor connection objects of ODBC connection"""
        try:
            conn = pyodbc.connect(DSN=self.DSN, PWD=self.odbc_passwd)
            cursor = conn.cursor()
            response = (conn, cursor)
        except:
            response = False
        return response

    def mysqlConnection(self):
        """Returns the conn, and cursor connection objects of Mysql connection"""
        con = self.read()['mysql']
        try:
            conn = MySQLdb.connect(con[0], con[1], con[2], con[3])
            cursor = conn.cursor()
            response = (conn, cursor)
        except MySQLdb.OperationalError:
            print >>sys.stderr, "Database Does Not Exist"

            response = False
        return response

    def executeOdbcQueries(self):
        """executes all ODBC querries and saves the dictionary list into a file"""
        try:
            conn,cursor = self.pyodbConnection()
        except TypeError:
            print >>sys.stderr, "ODBC Connection Error"
            return
        for odbc in self.read()['ODBC']:
            content = []
            cursor.execute(odbc[-1])
            for data in cursor.fetchall():
                dict = dict()
                for name, value in zip(odbc[-2], data):
                    dict[name] = value
                    content.append(dict)
            obj = Filemanagement(odbc[0])
            obj.write(content)
        conn.commit()
        cursor.close()

    def executeMysqlQueries(self):
        """executes all Mysql querries and saves the dictionary list into a file"""
        try:
            conn, cursor = self.mysqlConnection()
        except TypeError:
            print >>sys.stderr, "Mysql Connection Error"
            return

        queries = []
        for each in self.getRecipients():
            if each[0] == "MYSQL":
                queries.extend(each[1:])
                break
        for query in queries:
            content = []
            try:
                cursor.execute(str(query[-1]))
            except:
                continue
            counter = 0
            for data in cursor.fetchall():
                counter += 1
                dict = dict()
                for name, value in zip(query[1], data):
                    dict[name] = value
                content.append(dict)
            obj = Filemanagement(query[0])
            obj.write(content)
        conn.commit()
        cursor.close()

    def getRecipients(self):
        data = self.read()
        recipients = []
        for key, value in data.items():
            if key == "queries":
                recipients.append(value)
        return recipients

    def getRecipientname(self):
        recipients = []
        try:
            data = self.getRecipients()[0]
        except:
            print "There are no recipients"
            return recipients
        for name in data[1:]:
            recipients.append((name[0], name[1], name[-1]))
        return recipients

class InboxManager(object):
    def __init__(self):
        self.inbox = self.assing_name()

    def assing_name(self):
        name = "appfiles/inbox.dat"
        if os.path.exists(name):
            return name
        else:
            try:
                os.mkdir("appfiles")
            except WindowsError:
                pass
            with closing(open(name, "w")) as fl:
                pickle.dump({'current': []}, fl)
            return name

    def update(self, data, **keyword):
        dict_list = self._format_data(data, keyword)
        data1 = self.read()
        if len(dict_list) != 0:
            data1['current'] = dict_list
        if not self.write(data1):
            return False

        return True

    def _format_data(self, data1, kargs):
        identity, status = kargs["Identity"][0], kargs["Identity"][1]

        class nonlocal(object):
            dict_list = []
        data2 = self.read()

        def insert(date,status):
            def into():
                dict = dict()
                dict['name'] = i[0][0]; dict['recipient'] = i[0][1]
                dict['sender'] = sender; dict['status'] = status
                dict['message'] = i[1]; dict['date'] = date
                nonlocal.dict_list.append(dict)
            for i in data1:
                sender = "Admin"
                into()
            if len(data2) > 0:
                data2['current'].extend(nonlocal.dict_list)

        if identity == "cleaner":
            date = strftime('%a,%b %H:%M:%S', strptime(ctime()))
            status = "waiting"
            insert(date, status)
            return data2["current"]
        elif identity == "requestFeedback":
            for tuples in data1:
                new_dict = {'name': tuples[0][0], 'message': tuples[1], 'status': status}
                for all_list in data2["current"]:
                    rec2, msg2 = all_list['name'], all_list['message']
                    if (new_dict['name'] == rec2) and (new_dict['message'] == msg2):
                        all_list.update(new_dict)
            return data2["current"]
        else:
            pass

    def backup(self):
        data1 = self.read()
        data1['backup'] = data1['current']
        data1['current'] = []
        self.write(data1)

    def read(self):
        try:
            with closing(open(self.inbox, "rb")) as fl:
                data1 = pickle.load(fl)
        except EOFError:
            data1 = {'current': []}
        return data1

    def write(self, data):
        try:
            with closing(open(self.inbox, "wb")) as fl:
                pickle.dump(data, fl)
        except WindowsError:
            return False
        return True


class Datahandler(object):
    def __init__(self):
        pass
    def allClients(self):
        try:
            with open("appfiles/allclients.dat","rb") as newfile:
                data = pickle.load(newfile)
                return data
        except IOError, e:
            wx.MessageBox("All clients file is missing!!","System Error",wx.ICON_ERROR)


    def renewalClients(self):
        try:
            with open("bin/renewal.dat","rb") as newfile:
                data = pickle.load(newfile)
        except IOError, e:
            wx.MessageBox("Renewal file missing!!","System Error",wx.ICON_ERROR)
        return data

    def extensionClients(self):
        try:
            with open("bin/extensions.dat","rb") as newfile:
                data = pickle.load(newfile)
                print len(data)
        except IOError, e:
            wx.MessageBox("Extension file is missing!!","System Error",wx.ICON_ERROR)
        return data

    def balanceClients(self):

        clients = []
        try:
            with open("bin/balance.dat","rb") as newfile:
                data = pickle.load(newfile)
        except IOError ,e:
            wx.MessageBox("Balance file is missing!!","System Error",wx.ICON_ERROR)
        for i in data:
            try:
                if float(i['Amount']) >500.00:
                    clients.append(i)
                else:pass
            except:pass
        return clients
    def expiryClients(self):
        try:
            with open("bin/expiry.dat","rb") as newfile:
                data = pickle.load(newfile)
            return data
        except IOError, e:
            wx.MessageBox("Expiry file is missing!!","System Error",wx.ICON_ERROR)
    def fun_get_location(self):
        try:
            with open("bin/allclients.dat","rb") as newfile:
                data = pickle.load(newfile)
        except IOError, e:
            wx.MessageBox("Important system file is missing!!","System Error",wx.ICON_ERROR)

        lists=[]
        for i in data:
            if i['Town'] in lists:pass
            else:
                if i['Town']=="":pass
                else:lists.append(str(i['Town']))
        return lists
    def fun_get_occupation(self):
        try:
            with open("bin/allclients.dat","rb") as newfile:
                data = pickle.load(newfile)
        except IOError, e:
            wx.MessageBox("Important system file is missing!!","System Error",wx.ICON_ERROR)
        lists=[]
        for i in data:
            if i['Occ'] in lists:pass
            else:
                if i['Occ']==None:pass
                else:lists.append(str(i['Occ']))
        return lists
    def birthdayClients(self):
        lists = []
        try:
            with open("bin/allclients.dat","rb") as newfile:
                data = pickle.load(newfile)
        except IOError,e:
            wx.MessageBox("Birthday file is missing!!","System Error",wx.ICON_ERROR)
        for i in data:
            if i['dob'] != None:
                lists.append(i)
        return lists

    def fun_get_clients_by_location(self,location,Type,crit=""):
        lists = []
        if Type == "renewal":
            self.clients = self.expiryClients()
        if Type == "general":
            self.clients = self.allClients()
        if Type == "balance":
            self.clients = self.balanceClients()
        if Type == "newinvoice":
            self.clients = self.renewalClients()
        if Type == "extensions":
            self.clients = self.extensionClients()

        if crit:
            for i in self.clients:
                if (i['Town'] == location) and (i['Occ'] == crit):
                    lists.append(i)
        else:
            for i in self.clients:
                if i['Town'] == location:
                    lists.append(i)
        return lists

    def fun_get_clients_by_occupation(self,occupation,Type,crit=""):
        lists = []
        if Type == "renewal":
            self.clients = self.expiryClients()
        if Type == "general":
            self.clients = self.allClients()
        if Type == "balance":
            self.clients = self.balanceClients()
        if Type == "newinvoice":
            self.clients = self.renewalClients()
        if Type == "extensions":
            self.clients = self.extensionClients()
        if crit:
            for i in self.clients:
                if (i['Occ'] == occupation) and (i['Town'] == crit):
                    lists.append(i)

        else:
            for i in self.clients:
                if i['Occ'] == occupation:
                    lists.append(i)
        return lists
    def fun_get_active_clients(self,domant,Type):
        lists=[]
        if Type == "renewal":
            self.clients = self.expiryClients()
        if Type == "general":
            self.clients = self.allClients()
        if Type == "balance":
            self.clients = self.balanceClients()
        if Type == "newinvoice":
            self.clients = self.renewalClients()
        if Type == "extensions":
            self.clients = self.extensionClients()

        if domant == True:
            for x in self.clients:
                if x['Domant']==True:
                    lists.append(x)
        else:
            for x in self.clients:
                if x['Domant']!=True:
                    lists.append(x)
        return lists

    def fun_search_clients(self,pattern):
        lists=[];clients = self.allClients()
        try:
            int(str(pattern))
            for x in clients:
                if x['Phone'] == None:
                    continue
                if len(x['Phone']) == 9:
                    phnNo = "0"+str(x['Phone'])
                else:phnNo = str(x['Phone'])
                search_list = re.compile(str(pattern),re.IGNORECASE)
                for match in search_list.findall(phnNo):
                    lists.append(x)
            return lists
        except ValueError:
            for x in clients:
                text =  x['Name']
                search_list = re.compile(pattern,re.IGNORECASE)
                for match in search_list.findall(text):
                    lists.append(x)
            return lists

class GroupClassFunctions(object):
    def __init__(self):
        self.dbname = "databases/groups.db"
    def add_new_group(self,name):
        """Create new group in the database"""
        try:
            conn = sqlite3.connect(self.dbname)
            cursor = conn.cursor()
            sql = "select * from cgroups where gName LIKE '%s'"%(name)
            if any(cursor.execute(sql)) == True:
                return
            sql = "INSERT INTO cgroups(gName) VALUES('%s')"%(name)
            cursor.execute(sql)
            conn.commit()
            conn.close()
            wx.MessageBox("Succesfully saved new Group","Database Status",wx.ICON_INFORMATION)
            return True
        except:wx.MessageBox("Group Has Not been Added","Database Error",wx.ICON_ERROR);return False

    def add_group_client(self,details):
        """Inserting new client to the goup_t table"""
        First_name,Middle_Name,Surname,phone,email,address,city,group=details
        if First_name == "":
            return False
        if (phone or address or email) == "":
            return False
        if self._checker(phone) == True:
            return False
        conn = sqlite3.connect(self.dbname)
        cursor = conn.cursor()
        sql = "INSERT INTO group_t VALUES(null,?,?,?,?,?,?,?,?)"
        fields = (First_name,Middle_Name,Surname,phone,email,address,city,group)
        cursor.execute(sql,fields)
        conn.commit()
        conn.close()
        return True

    def update_gclients(self):
        self.create_table()
        try:
            with open("bin/groupclients.dat","rb") as newfile:
                data = pickle.load(newfile)
        except IOError,e:
            wx.MessageBox("Important system file is missing!!","System Error",wx.ICON_ERROR)

        for i in data[2]:
            tuple = (i["Name"],"","",str(i["Phone"]),"",i["Address"],i["City"],i["Group"])
            self.add_group_client(tuple)


    def delete_group_client(self,phn):
        conn = sqlite3.connect(self.dbname)
        cursor = conn.cursor()
        sql = "DELETE  from group_t where phone = '%s'"%phn
        cursor.execute(sql)
        conn.commit()
        msg = "Deleted %d Member(s)"%conn.total_changes
        wx.MessageBox(msg,"Delete Transaction",wx.ICON_INFORMATION)

    def search_group_clients(self,data,crit):
        conn = sqlite3.connect(self.dbname)
        cursor = conn.cursor();newlist=[]
        if crit != "phone":
            sql = "select * from group_t where fname LIKE '%s'"%(data)
        else:
            sql = "select * from group_t where Phone LIKE '%s'"%(data)
        cursor.execute(sql)
        for i in cursor.fetchall():
            collect = {}
            collect['Name'],collect['Phone'],collect['Group'] = [i[1],i[4],i[8]]
            newlist.append(collect)
        conn.commit();conn.close()
        return newlist
    def delete_group(self,name):
        conn = sqlite3.connect(self.dbname)
        cursor = conn.cursor()
        sql = "DELETE  from group_t where groups='%s'"%name
        cursor.execute(sql)
        sql = "DELETE  from cgroups where gName='%s'"%name
        cursor.execute(sql)
        conn.commit()
    def create_table(self):
        conn = sqlite3.connect(self.dbname)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS group_t")
        conn.execute('''CREATE TABLE group_t(
                        Id_no integer primary key,
                        fname text,
                        mname text,
                        sname text,
                        phone integer,
                        email text,
                        address text,
                        city text,
        groups text);''')
        conn.commit()
        conn.close()

    def get_group_clients(self,group):
        conn = sqlite3.connect(self.dbname)
        cursor = conn.cursor();newlist=[]
        if group == "all":
            sql = "select * from group_t"
            cursor.execute(sql)
        else:
            sql = "select * from group_t where groups = ?"
            cursor.execute(sql,(group,))
        for i in cursor.fetchall():
            collect = {}
            names = "%s %s %s"%(i[1],i[2],i[3])
            collect['Name'],collect['Phone'],collect['Address'],collect['City'],collect["Group"] = [names,i[4],i[6],i[7],i[8]]
            newlist.append(collect)
        conn.commit();conn.close()
        return newlist
    def get_group_names(self,group=""):
        group = "groups"
        conn = sqlite3.connect(self.dbname)
        cursor = conn.cursor();groupnames=[]
        query = "SELECT DISTINCT %s from group_t"%group
        cursor.execute(query)
        for names in cursor.fetchall():
            if not names[0]:
                pass
            else:
                groupnames.append(names[0])
        conn.close()
        return groupnames

    def _checker(self,phn):
        str(phn)
        if len(phn) > 10:
            if ((phn[:4] == "+254") or (phn[:3]=="254")):
                pass
            else:
                wx.MessageBox("incorrect number or digits in the phone number","Value Error",wx.ICON_ERROR)
                return True
        elif (len(phn) == 9) and (phn[0]=="0"):
            wx.MessageBox("incorrect number or digits in the phone number","Value Error",wx.ICON_ERROR)
            return True
        elif len(phn) < 9:
            wx.MessageBox("incorrect number or digits in the phone number","Value Error",wx.ICON_ERROR)


        conn = sqlite3.connect(self.dbname)
        cursor = conn.cursor()
        sql = "select * from group_t where Phone LIKE %s"%(phn)
        cursor.execute(sql)
        if cursor.fetchone() == None:
            conn.commit();conn.close()
            return False
        else:
            conn.commit();conn.close()
            wx.MessageBox("This phone number exists in the database","Value Error",wx.ICON_ERROR)
            return True
class PhoneNumber(object):
    def __init__(self,phn):
        self.phn = phn
    def list_of_numbers(self):
        if isinstance(self.phn,list):
            return self.list_phoneno_formater(self.phn)
        elif isinstance(self.phn,long):
            return self.int_phoneno_formater(self.phn)
        elif isinstance(self.phn,int):
            return self.int_phoneno_formater(self.phn)
        elif isinstance(self.phn,str):
            return self.str_phoneno_formater(self.phn)
        else:
            return False


    def list_phoneno_formater(self,the_list):
        valid_list = []
        for number in the_list:
            if self.phone_no_validator(number) is not False:
                valid_list.append(self.phone_no_validator(number))
        if not valid_list:
            return []
        else:
            return valid_list
    def int_phoneno_formater(self,the_int):
        valid_list = []
        if self.phone_no_validator(the_int) is not False:
            valid_list.append(self.phone_no_validator(the_int))
            return valid_list
        else:
            return []

    def str_phoneno_formater(self,the_str):
        valid_list = []
        the_str.replace(' ',"")
        if self.phone_no_validator(the_str) is not False:
            valid_list.append(self.phone_no_validator(the_str))
            return valid_list

        else:
            return []



    def phone_no_validator(self,phnno):
        try:
            phnno = str(phnno)
            if (phnno[0] != "+"):
                int(phnno)
        except ValueError, err:
            return False
        phnno.replace(' ',"")
        length = len(phnno)
        if length < 9:
            return False
        elif length == 9:
            if phnno[:1] == "0":
                return False

            return "%s%s"%("+254",phnno)
        elif length == 10:
            return "%s%s"%("+254",phnno[1:])
        elif length == 12:
            if phnno[:3] == "254":

                return "%s%s"%("+",phnno)
            else:
                return False
        elif length == 13:
            if phnno[:4] == "+254":

                return phnno
            else:
                return False
        else:

            return False

def clearner(content):
    faulty_list = []
    valid_list = []
    inbox = InboxManager()
    inbox.update(content,Identity=["cleaner","waiting"])
    for i in content:
        inst = PhoneNumber(i[0][1])
        phone_no=inst.list_of_numbers()
        if not phone_no:
            faulty_list.append(i)
        else:
            i[0][1] = phone_no[0]
            valid_list.append(i)
    return valid_list
class InboxManager(object):
    def __init__(self):
        self.inbox = self.assing_name()
    def assing_name(self):
        name = "bin/inbox.dat"
        if os.path.exists(name):
            return name
        else:
            try:os.mkdir("bin")
            except:pass
            with closing(open(name,"w")) as fl:
                pickle.dump({'current':[]},fl)
            return name
    def update(self,data,**keyword):
        dict_list = self._format_data(data,keyword)
        data1 = self.read()
        if  len(dict_list) != 0:
            data1['current'] = dict_list
        if not self.write(data1):
            wx.MessageBox("Could not update","Error",wx.ICON_ERROR)
            return False

        return True
    def _format_data(self,data1,kargs):
        identity,status = kargs["Identity"][0],kargs["Identity"][1]
        class nonlocal(object):
            dict_list = []
        data2 = self.read()
        def insert(date,status):
            def into():
                dict = {}
                dict['name']= i[0][0];dict['recipient'] = i[0][1]
                dict['sender'] = sender;dict['status'] = status
                dict['message'] = i[1];dict['date'] = date
                nonlocal.dict_list.append(dict)
            for i in data1:
                sender = "Admin"
                into()
            if len(data2) > 0:
                data2['current'].extend(nonlocal.dict_list)

        if identity == "cleaner":
            date = strftime('%a,%b %H:%M:%S',strptime(ctime()))
            status = "waiting"
            insert(date,status)
            return data2["current"]
        elif identity == "requestFeedback":
            for tuples in data1:
                new_dict = {'name':tuples[0][0],'message':tuples[1],'status':status}
                for all_list in data2["current"]:
                    rec2,msg2 = all_list['name'],all_list['message']
                    if (new_dict['name'] == rec2) and (new_dict['message'] == msg2):
                        all_list.update(new_dict)
            return data2["current"]
        else:
            pass

    def backup(self):
        data1 = self.read()
        data1['backup'] = data1['current']
        data1['current'] = []
        self.write(data1)

    def read(self):
        try:
            with closing(open(self.inbox,"rb")) as fl:
                data1 = pickle.load(fl)
        except EOFError:
            data1 = {'current':[]}
        return data1

    def write(self,data):
        try:
            with closing(open(self.inbox,"wb")) as fl:
                pickle.dump(data,fl)
        except:
            return False
        return True


