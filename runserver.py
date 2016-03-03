__author__ = 'Monte'
import os
import sys
import time
import cPickle as Pickle
from contextlib import closing
from threading import Thread
from zope.interface import Interface, implements
from twisted.cred.checkers import ANONYMOUS, AllowAnonymousAccess
from twisted.enterprise import adbapi
from twisted.protocols import basic
from twisted.spread import pb
from twisted.cred import portal, checkers, credentials, error as credError
from twisted.internet import protocol, reactor, defer
from twisted.python import log
from twisted.python import logfile

from cron import main as Main
from security import Security
from database import DatabaseManager
from functions import FileManager, message_sender

DB_DRIVER = "MySQLdb"

security = Security()
DB_ARGS = {

    'db': security.database,

    'user': security.user,

    'passwd': security.password,

    }


class ServerFunctions:
    def __init__(self, users, passwords, db_manager):
        self.users = users
        self.passwords = passwords
        self.db_manager = db_manager
        self.user_id = ""

    def authorizeUser(self, details):
        """method to authorize users"""
        self.passwords = self.db_manager.get_user_details("passwords")
        diction = {}
        for user, passwd in self.passwords.items():
            if (details['username'] == user) and (details['password'] == passwd):
                diction[user] = passwd
        self.user_id = details['username']
        print >>sys.stderr, "%s asking for authentification"%self.user_id
        return diction

    def postClients(self):
        """method to return list of all clients """
        data = self.db_manager.all_clients()
        print >>sys.stderr, "Server responding to request with %d clients" % len(data)
        return data

    def postRenewals(self):
        """method to return list of clients with renewals """
        data = self.db_manager.clients_with_renewal()
        print >>sys.stderr, "Server responding to request with %d renewals" % len(data)
        return data

    def postExpiry(self):
        """method to return list of clients with expiry"""
        data = self.db_manager.clients_with_expiry()
        print >>sys.stderr, "Server responding to request with %d expiries" % len(data)
        return data

    def postBalance(self):
        """method to return list of clients with balance"""
        data = self.db_manager.clients_with_balance()
        print >>sys.stderr, "Server responding to request with %d balances" % len(data)
        return data

    def postExtensions(self):
        """method to return list of clients with extensions"""
        data = self.db_manager.clients_with_extension()
        print >>sys.stderr, "Server responding to request with %d extensions" % len(data)
        return data

    def add_user(self, args):
        """Method that adds new user to the system"""
        response = self.db_manager.add_user(args)
        print >>sys.stderr, "Admin adding new user to the system"
        return response


    def addGroup(self,name):
        response = self.db_manager.add_group(name)
        print >>sys.stderr, "Server responding to request"
        return response

    def add_group_member(self, data):
        response = self.db_manager.add_group_member(data)
        print >>sys.stderr, "Server responding to add member request"
        return response

    def searchGroupsClients(self, data, critic):
        response = self.db_manager.search_group_clients(data,critic)
        print >>sys.stderr, "Server responding to request"
        return response

    def get_group_members(self, name):
        data = self.db_manager.get_group_members(name)
        print >>sys.stderr, "Server responding to request with %d group clients" % len(data)
        return data

    def get_groups(self, crit):
        data = self.db_manager.get_group_names(crit)
        print >>sys.stderr, "Server responding to request with %d names" % len(data)
        return data

    def get_outbox(self, arg):
        response = self.db_manager.get_outbox()
        print >>sys.stdout, "Server responding to outbox request"
        return response

    def delete_group_member(self, phone):
        response = self.db_manager.delete_group_member(phone)
        print >>sys.stderr, "Server responding to request"
        return response

    def delete_group(self, name):
        response = self.db_manager.groups.delete_group(name)
        print >>sys.stderr, "Server responding to request"
        return response

    def getUsers(self, Type):
        data = self.db_manager.get_users(Type)
        print >>sys.stderr, "Server responding to request with %d users" % len(data)
        return data

    def updateUser(self,arg):
        response = self.db_manager.update_user(arg)
        return response

    def update_message(self, arg):
        response = self.db_manager.update_message(arg)
        print >>sys.stderr, "Server responding to update message request", arg
        return response

    def update_cheque(self, arg):
        response = self.db_manager.update_cheque(arg)
        return response

    def update_config(self, arg):
        flm = FileManager()
        response = flm.change_config(arg)
        return response

    def update_amount(self, arg):
        responses = list()
        for amount in arg:
            responses.append(self.update_config(amount))
        results = ""
        if len(arg) > 1:
            if responses[0][0] and responses[1][0]:
                results = (True, "Minimum and maximum amounts have been set")
            elif responses[0][0] or responses[1][0]:
                results = (False, "Error in updating either maximum or minimum amounts")
            else:
                results = (False, "Could not update minimum and maximum amount")
        else:
            return responses[0]
        return results

    def addCompanyDetails(self, args):
        response = self.db_manager.add_company_details(args)
        return response

    def addCheque(self, arg):
        response = self.db_manager.add_cheque(arg)
        return response

    def addBank(self, arg):
        response = self.db_manager.add_bank(arg)
        return response

    def addChequeType(self, arg):
        response = self.db_manager.add_cheque_type(arg)
        return response

    def addPayee(self, arg):
        response = self.db_manager.add_payee(arg)
        return response

    def addServerLog(self, args):
        response = self.db_manager.add_server_log(args)
        return response

    def deleteChequeType(self, arg):
        response = self.db_manager.delete_cheque_type(arg)
        return response

    def deletePayee(self, arg):
        response = self.db_manager.delete_payee(arg)
        return response

    def deleteBank(self, arg):
        response = self.db_manager.delete_bank(arg)
        return response

    def sendMessage(self, arg):
        for message in arg:
            self.db_manager.add_outbox(message)
        response = message_sender()
        return response

    def getChequeType(self):
        response = self.db_manager.get_chequetype()
        print >>sys.stderr, "Server responding to request with %d cheque types" % len(response)
        return response

    def getBank(self):
        response = self.db_manager.get_bank()
        print >>sys.stderr, "Server responding to request with %d bank" % len(response)
        return response

    def getPayee(self):
        response = self.db_manager.get_payee()
        print >>sys.stderr, "Server responding to request with %d payee" % len(response)
        return response

    def getCheques(self):
        response = self.db_manager.get_cheques()
        print >>sys.stderr, "Server responding to request with %d cheques" % len(response)
        return response

    def getMessages(self):
        response = self.db_manager.get_messages()
        print >>sys.stderr, "Server responding to request with %d messages" % len(response)
        return response

    def get_company_details(self):
        response = self.db_manager.get_company_details()
        print >>sys.stderr, "Server responding to request with company information"
        return response

    def set_default_message(self, arg):
        with closing(open("bin/messages", "rb")) as fl:
            msgs = Pickle.load(fl)
        if arg.lower() in msgs.keys():
            message = msgs[arg.lower()]
            return self.db_manager.update_message((arg.lower(), "message", message))
        else:
            return False, "Default message for %s  could not be found" % arg.capitalize()

    @staticmethod
    def read_file(file_name):
        file_ = "bin/%s.dat" % file_name
        with closing(open(file_, "rb")) as fl:
            data = Pickle.load(fl)
        return data

    @staticmethod
    def get_configurations():
        with closing(open("bin/config.conf")) as fl:
            data = Pickle.load(fl)
        return data

    def app_details(self):
        details = dict()
        details['renewal'] = self.postRenewals()
        details['balance'] = self.postBalance()
        details['allclients'] = self.postClients()
        details['expiry'] = self.postExpiry()
        """details['extensions'] = ServerFunctions.read_file("extensions")"""
        details['cheques'] = self.getCheques()
        details['banks'] = self.getBank()
        details['payee'] = self.getPayee()
        details['chequetype'] = self.getChequeType()
        details['users'] = self.getUsers("all")
        details['compdetails'] = self.get_company_details()
        details['groups'] = self.get_groups("all")
        details['members'] = self.get_group_members("all")
        details['messages'] = self.getMessages()
        details['outbox'] = self.get_outbox("")
        details['config'] = ServerFunctions.get_configurations()
        return details




##############################################################################

class UserPerspective(pb.Avatar):
    def __init__(self, todoList , user_id):
        self.todoList = todoList
        self.user_id = user_id

    def perspective_postClients(self):
        """perspective method to return list of clients"""
        log.msg("%s requesting for all clients" % self.user_id)
        return self.todoList.postClients()

    def perspective_postRenewals(self):
        """perspective method to return list of clients with renewals"""
        log.msg("%s requesting for all clients with renewal" % self.user_id)
        return self.todoList.postRenewals()

    def perspective_postExpiry(self):
        """perspective method to return list of clients with expiry"""
        log.msg("%s requesting for all clients with expiry" % self.user_id)
        return self.todoList.postExpiry()

    def perspective_postBalance(self):
        """perspective method to return list of clients with blalance"""
        log.msg("%s requesting for all clients with balance" % self.user_id)
        return self.todoList.postBalance()

    def perspective_postExtensions(self):
        """perspective method to return list of clients with extensions"""
        log.msg("%s requesting for all clients with extensions" % self.user_id)
        return self.todoList.postExtensions()

    def perspective_get_group_members(self, details):
        """perspective to return all group clients"""
        return self.todoList.get_group_members(details)

    def perspective_addGroup(self,details):
        print ("""perspective to add new group """)
        return self.todoList.addGroup(details)

    def perspective_add_group_member(self, details):
        """perspective to add new group client """
        return self.todoList.add_group_member(details)

    def perspective_searchGroupsClients(self, dat, crit):
        """perspective to search group client """
        return self.todoList.search_groups_clients(dat, crit)

    def perspective_get_groups(self, details):
        """Get group names"""
        return self.todoList.get_groups(details)

    def perspective_updateUser(self, arg):
        """Perspective to update user details"""
        return self.todoList.updateUser(arg)

    def perspective_addCheque(self, arg):
        """Perspective to update cheque details"""
        return self.todoList.addCheque(arg)

    def perspective_addBank(self, arg):
        """Perspective to update bank details"""
        return self.todoList.addBank(arg)

    def perspective_addServerLog(self, arg):
        """Perspective to update server log details"""
        return self.todoList.addServerLog(arg)

    def perspective_sendMessage(self, arg):
        """Perspective to send messages"""
        return  self.todoList.sendMessage(arg)

    def perspective_addChequeType(self, arg):
        """Perspective to add cheque types"""
        return self.todoList.addChequeType(arg)

    def perspective_addPayee(self, arg):
        """Perspective to add payee"""
        return self.todoList.addPayee(arg)

    def perspective_deleteChequeType(self, arg):
        """Perspective to delete cheque types"""
        return self.todoList.deleteChequeType(arg)

    def perspective_deletePayee(self, arg):
        """Perspective to delete payee"""
        return self.todoList.deletePayee(arg)

    def perspective_deleteBank(self, arg):
        """Perspective to delete bank"""
        return self.todoList.deleteBank(arg)

    def perspective_getChequeType(self):
        """Perspective to get cheque types"""
        return self.todoList.getChequeType()

    def perspective_get_company_details(self):
        """Perspective to get company information"""
        return self.todoList.get_company_details()

    def perspective_app_details(self):
        """Perspective to get all app details"""
        return self.todoList.app_details()

    def perspective_get_outbox(self, arg):
        """Perspective to send outbox messages"""
        return self.todoList.get_outbox(arg)

    def perspective_update_message(self, arg):
        """Perspective to update message"""
        return self.todoList.update_message(arg)

    def perspective_update_config(self, args):
        """Perspective to update configuration file"""
        return self.todoList.update_config(args)

    def perspective_update_amount(self, arg):
        """Perspective to update minimum and maximum amounts"""
        return self.todoList.update_amount(arg)

    def perspective_update_cheque(self, args):
        """Perspective to update cheque details"""
        return self.todoList.update_cheque(args)

    def perspective_set_default_message(self, arg):
        """Resets a perticular message type to its default message"""
        return self.todoList.set_default_message(arg)

    def perspective_delete_group_member(self, arg):
        """Deletes group member from database"""
        return self.todoList.delete_group_member(arg)

    def perspective_delete_group(self, arg):
        """Perspective to delete a group """
        return self.todoList.delete_group(arg)


class AdminPerspective(UserPerspective):
    def __init__(self, todoList):
        self.user_id = "admin"
        UserPerspective.__init__(self, todoList, self.user_id)

    def perspective_getUsers(self,details):
        """perspective to get all system users """
        return self.todoList.getUsers(details)

    def perspective_saveCompanyDetails(self, args):
        """Perspective to change and add company details"""
        return self.todoList.addCompanyDetails(args)

    def perspective_add_user(self, args):
        """Perspective to add new User to the system"""
        return self.todoList.add_user(args)


class DbPasswordChecker(object):
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword, credentials.IUsernameHashedPassword)

    def __init__(self, dbconn):
        self.dbconn = dbconn

    def requestAvatarId(self, credentials):
        query = "select id, password from user where username = '%s'" % credentials.username
        return self.dbconn.runQuery(query).addCallback(self._gotQueryResults, credentials)

    def _gotQueryResults(self, rows, userCredentials):
        if rows:
            userid, password = rows[0]
            return defer.maybeDeferred(
                userCredentials.checkPassword, password).addCallback(
                self._checkedPassword, userid)
        else:
            raise credError.UnauthorizedLogin, "No such user"

    def _checkedPassword(self, matched, userid):
        if matched:
            return userid
        else:
            raise credError.UnauthorizedLogin("Bad password")

class INamedUserAvatar(Interface):
    """should have attributes username and fullname"""

class NamedUserAvatar:
    implements(INamedUserAvatar)

    def __init__(self, username, fullname):
        self.username = username
        self.fullname = fullname


class AnonymousPerspective(pb.Avatar):

    def __init__(self, ServerFunctions, user_id):
        self.ServerFunctions = ServerFunctions

    def perspective_authorizeUser(self, details):
        return self.ServerFunctions.authorizeUser(details)


class ClassRealm:
    implements(portal.IRealm)

    def __init__(self, server_functions, conn):
        self.ServerFunctions = server_functions
        self.dbconn = conn
        self.username = ""

    def requestAvatar(self, avatarId, mind, *interfaces):
        if pb.IPerspective not in interfaces:
            raise NotImplementedError
        else:
            if avatarId:
                query = "select username, firstname, lastname from user where id = '%d'" % int(avatarId)
                return self.dbconn.runQuery(query).addCallback(self._gotQueryResults)
            elif avatarId is ANONYMOUS:
                avatarId = "Anonymous"
                avatar = AnonymousPerspective(self.ServerFunctions, avatarId)
                return pb.IPerspective, avatar, lambda: None

    def _gotQueryResults(self, rows):
        username, firstname, lastname = rows[0]
        if username == 'admin' or username == 'Admin' or username == 'root':
                avatar = AdminPerspective(self.ServerFunctions)
        elif username is ANONYMOUS:
            print "Anonymous", username
            avatarId = "Anonymous"
            avatar = AnonymousPerspective(self.ServerFunctions, avatarId)
        else:
            avatar = UserPerspective(self.ServerFunctions, username)
        return pb.IPerspective, avatar, lambda: None


class LoginProtocol(basic.LineReceiver):
    pass


class LoginFactory(protocol.ServerFactory):
    protocol = LoginProtocol

    def __init__(self, portal):
        self.portal = portal


def initialize_users(db):
    users = db.get_birthmark_users()
    for user in users:
        db.add_user((user["username"], user["password"], user["firstname"], user["lastname"], ""))

def main():
    db_access = DatabaseManager()
    db_access.connect(dialect="mysql", user=security.user, passwd=security.password, database=security.database)
    initialize_users(db_access)
    connection = adbapi.ConnectionPool(DB_DRIVER, **DB_ARGS)
    users = db_access.get_user_details("users")
    passwords = db_access.get_user_details("passwords")
    p = portal.Portal(ClassRealm(ServerFunctions(users, passwords, db_access), connection))
    p.registerChecker(DbPasswordChecker(connection))
    c2 = AllowAnonymousAccess()
    p.registerChecker(c2)
    if not os.path.exists('tmp'):
        os.mkdir('tmp')
    f = logfile.LogFile("tmp\serverLog.log", "", rotateLength=100)
    log.startLogging(f)
    reactor.listenTCP(13333, pb.PBServerFactory(p))
    reactor.run()

if __name__ == "__main__":        
    application = Thread(name="SMS Lite Application", target=Main)    
    main()
    time.sleep(90)
    application.start()
