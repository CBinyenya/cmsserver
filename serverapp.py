__author__ = 'Monte'
import os
import sys
import cPickle as pickle
from zope.interface import Interface, implements
from twisted.cred.checkers import ANONYMOUS, AllowAnonymousAccess
from twisted.protocols import basic
from twisted.spread import pb
from twisted.cred import portal, checkers, credentials, error as credError
from twisted.internet import protocol, reactor, defer
from twisted.python import log
from twisted.python import logfile

from database import DatabaseManager
from messenger import Messenger

class ServerFunctions:
    def __init__(self, users, passwords, db_manager):
        self.users = users
        self.passwords = passwords
        self.db_manager = db_manager
        self.user_id = ""

    def authorizeUser(self,details):
        """method to authorize users"""
        self.passwords = self.db_manager.get_user_details("passwords")
        diction = {}
        for user,passwd in self.passwords.items():
            print user,passwd
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

    def addUser(self, args):
        """Method that adds new user to the system"""
        response = self.db_manager.add_user(args)
        print >>sys.stderr, "%s adding new user to the system" % self.user_id
        return response

    def getCompanyDetails(self):
        data = {}
        if not os.path.exists("bin/compdetails"):
            return data
        try:
            with open("bin/compdetails","rb") as newfile:
                    data = pickle.load(newfile)
        except:
            pass
        finally:
            return data

    def addGroup(self,name):
        response = self.db_manager.add_group(name)
        print >>sys.stderr, "Server responding to request"
        return response

    def addGroupClients(self, data):
        response = self.db_manager.add_member(data)
        print >>sys.stderr, "Server responding to request"
        return response

    def searchGroupsClients(self, data, critic):
        response = self.db_manager.search_group_clients(data,critic)
        print >>sys.stderr, "Server responding to request"
        return response

    def getGroupClients(self, name):
        data = self.db_manager.get_group_members(name)
        print >>sys.stderr, "Server responding to request with %d group clients" % len(data)
        return data

    def getGroupNames(self, crit):
        data = self.db_manager.get_group_names(crit)
        print >>sys.stderr, "Server responding to request with %d names" % len(data)
        return data

    def deleteGroupClient(self, phone):
        response = self.db_manager.delete_group_client(phone)
        print >>sys.stderr, "Server responding to request"
        return response

    def deleteGroup(self, name):
        response = self.db_manager.groups.delete_group(name)
        print >>sys.stderr, "Server responding to request"
        return response

    def getUsers(self, Type):
        data = self.db_manager.get_user_details(Type)
        print >>sys.stderr, "Server responding to request with %d users" % len(data)
        return data

    def updateUser(self,arg):
        response = self.db_manager.update_user(arg)
        if response:
            register(arg[0],arg[2])
        return response

    def addCompanyDetails(self,args):
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
        send = Messenger(arg)
        print send.check_config()
        send.send_sms()

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

    def app_details(self):
        details = dict()
        details['renewal'] = self.postRenewals()
        details['balance'] = self.postBalance()
        details['allclients'] = self.postClients()
        details['expiry'] = self.postExpiry()
        details['extensions'] = self.postExtensions()
        details['cheques'] = self.getCheques()
        details['banks'] = self.getBank()
        details['payee'] = self.getPayee()
        details['chequetype'] = self.getChequeType()
        details['users'] = self.getUsers("all")
        details['compdetails'] = self.getCompanyDetails()
        details['groups'] = self.getGroupNames("all")
        details['gnames'] = self.getGroupClients("all")
        details['messages'] = self.getMessages()
        return details



##############################################################################

class UserPerspective(pb.Avatar):
    def __init__(self, todoList , user_id):
        self.todoList = todoList
        self.user_id = user_id

    def perspective_getCompanyDetails(self):
        return self.todoList.getCompanyDetails()

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

    def perspective_getGroupClients(self, details):
        """perspective to return all group clients"""
        return self.todoList.getGroupClients(details)

    def perspective_addGroup(self,details):
        print ("""perspective to add new group """)
        return self.todoList.addGroup(details)

    def perspective_addGroupClient(self, details):
        """perspective to add new group client """
        return self.todoList.addGroupClients(details)

    def perspective_searchGroupsClients(self, dat, crit):
        """perspective to search group client """
        return self.todoList.search_groups_clients(dat, crit)

    def perspective_getGroupNames(self, details):
        """Get group names"""
        return self.todoList.getGroupNames(details)

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

    def perspective_app_details(self):
        """Perspective to get all app details"""
        return self.todoList.app_details()




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

    def perspective_addUser(self, args):
        """Perspective to add new User to the system"""
        return self.todoList.addUser(args)


class PasswordDictChecker(object):
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,credentials.IUsernameHashedPassword,)

    def __init__(self, passwords):
        "passwords: a dict-like object mapping usernames to passwords"
        self.passwords = passwords

    def requestAvatarId(self, credentials):
        username = credentials.username
        if self.passwords.has_key(username):
            realPassword = self.passwords[username]
            checking = defer.maybeDeferred(
                credentials.checkPassword, realPassword)
            checking.addCallback(self._checkedPassword, username)
            return checking
        else:
            return defer.fail(
                    credError.UnauthorizedLogin("Bad password"))

    def _checkedPassword(self, matched, username):
        try:
            if matched:
                return username
            else:
                raise credError.UnauthorizedLogin("Bad password")
        except credError.UnauthorizedLogin:
            print "Wrong password"

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

    def __init__(self, ServerFunctions, users):
        self.users = users
        self.ServerFunctions = ServerFunctions

    def requestAvatar(self, avatarId, mind, *interfaces):
        if pb.IPerspective not in interfaces:
            raise NotImplementedError
        else:
            if avatarId == 'admin' or avatarId == 'Admin' or avatarId == 'root':
                avatar = AdminPerspective(self.ServerFunctions)
            elif avatarId is ANONYMOUS:
                avatarId = "Anonymous"
                avatar = AnonymousPerspective(self.ServerFunctions, avatarId)
            else:
                avatar = UserPerspective(self.ServerFunctions, avatarId)
            return pb.IPerspective, avatar, lambda: None


class LoginProtocol(basic.LineReceiver):
    pass


class LoginFactory(protocol.ServerFactory):
    protocol = LoginProtocol

    def __init__(self, portal):
        self.portal = portal


db_access = DatabaseManager()
db_access.connect(dialect="mysql", user="monte", passwd="creawib", database="bima")
users = db_access.get_user_details("users")
passwords = db_access.get_user_details("passwords")
p = portal.Portal(ClassRealm(ServerFunctions(users, passwords, db_access), users))
p.registerChecker(PasswordDictChecker(passwords))
checker = checkers.InMemoryUsernamePasswordDatabaseDontUse()

def register(name, passwd):
    checker.addUser(name, passwd)
    p.registerChecker(checker)

def main():
    c2 = AllowAnonymousAccess()
    p.registerChecker(c2)
    if not os.path.exists('tmp'):
        os.mkdir('tmp')
    f = logfile.LogFile("tmp\serverLog.log", "", rotateLength=100)
    # log.startLogging(f)
    factory = LoginFactory(p)
    reactor.listenTCP(13333, pb.PBServerFactory(p))
    reactor.run()
main()
























