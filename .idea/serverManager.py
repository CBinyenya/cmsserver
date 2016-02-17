import os
import wx
import sys
import cPickle as pickle
from contextlib import closing
from twisted.internet import reactor
from twisted.spread import pb
from twisted.python import log
from twisted.cred import credentials
from twisted.cred.credentials import Anonymous
from functions import GroupClassFunctions
from functions import InboxManager
fun = GroupClassFunctions()
clients = []
def runKlass(details):        
        username, password = details
        creds = credentials.UsernamePassword(username, password)
        tester = Messanger(creds)
        tester.runEngine()       
        try:              
                reactor.run()
        except:
            print "More Server Error"


class Messanger(object):
    def __init__(self, credentials):
        self.credentials = credentials
        self.server = None
        self.clients = []
        self.host=self.hostGetter()
        
    def hostGetter(self):
        if os.path.exists("AppDetails.data"):
            with open("AppDetails.data","r") as f:
                return f.readline().rstrip()
        else:return "localhost"
    
    def runEngine(self):
        self.connect().addCallback(
            lambda _: self.get_company_details()).addCallback(
            lambda _: self.get_clients_with_balance()).addCallback(
            lambda _: self.get_clients_with_renewal()).addCallback(
            lambda _: self.get_clients_with_expiry()).addCallback(
            lambda _: self.get_all_clients()).addCallback(
            lambda _: self.getGroupClients()).addCallback(
            lambda _: self.getUsers()).addErrback(
            self._catchFailure).addCallback(
            lambda _: reactor.stop())
        # lambda _: self.get_clients_with_extensions()).addCallback(

    def connect(self):    
        factory = pb.PBClientFactory()
        reactor.connectTCP(self.host,13333,factory)
        return factory.login(self.credentials).addCallback(self._connect)

    def _connect(self,rootObj):
        self.server = rootObj

    def _catchFailure(self, failure):
        log.msg(failure)
        msg ="The server application cannot be reached. Check you network connection"
        msg = str(failure)
        self._messageBox(msg,"CONNECTION ERROR",wx.ICON_ERROR)       

    def get_clients_with_balance(self):
        print >>sys.stderr,"Calling for clients with balance from server.."
        return self.server.callRemote("postBalance").addCallback(self._got_clients_with_balance)

    def get_clients_with_renewal(self):
        print >>sys.stderr,"Calling for clients with renewals from server.."
        return self.server.callRemote("postRenewals").addCallback(self._got_clients_with_renewal)

    def get_clients_with_expiry(self):
        print >>sys.stderr,"Calling for clients with expiry from server.."
        return self.server.callRemote("postExpiry").addCallback(self._got_clients_with_expiry)

    def get_clients_with_extensions(self):
        print >>sys.stderr,"Calling for clients with extensions from server.."
        return self.server.callRemote("postExtensions").addCallback(self._got_clients_with_extensions)

    def get_all_clients(self):
        print >>sys.stderr,"Calling for clients from server.."
        return self.server.callRemote("postClients").addCallback(self._got_all_clients)

    def get_company_details(self):        
        return self.server.callRemote("getCompanyDetails").addCallback(self._getCompanyDetails)

    def getUsers(self):        
        return self.server.callRemote("getUsers","allusers").addCallback(self._getusersFeedback)

    def getGroupClients(self):
        return self.server.callRemote("getGroupClients","all").addCallback(self._getgclientsFeedback)

    def _got_clients_with_balance(self,clients_with_balance):
        with open("bin/balance.dat",'wb') as newfile:
            pickle.dump(clients_with_balance,newfile)
        print >>sys.stderr,"loading "+str(len(clients_with_balance))+" clients with balance"

    def _got_clients_with_renewal(self,clients_with_renewal):        
        with open("bin/renewal.dat",'wb') as newfile:
            pickle.dump(clients_with_renewal,newfile)
        print >>sys.stderr,"loading "+str(len(clients_with_renewal))+" clients with renewal"
        
    def _got_clients_with_expiry(self,clients_with_expiry):
        
        with open("bin/expiry.dat",'wb') as newfile:
            pickle.dump(clients_with_expiry,newfile)
        print >>sys.stderr,"loading "+str(len(clients_with_expiry))+" clients with expiry"

    def _got_clients_with_extensions(self,clients_with_extensions):
        
        with open("bin/extensions.dat",'wb') as newfile:
            pickle.dump(clients_with_extensions,newfile)
        print >>sys.stderr,"loading "+str(len(clients_with_extensions))+" clients with extensions"
        
    def _got_all_clients(self,clients):
        
        with open("bin/allclients.dat",'wb') as newfile:
            pickle.dump(clients,newfile)
        print >>sys.stderr,"loading "+str(len(clients))+"clients"

    def _getCompanyDetails(self,details):                
        if not os.path.exists("bin"):
            os.mkdir("bin")
        with open("bin/compdetails",'wb') as newfile:
            pickle.dump(details,newfile)

    def _getusersFeedback(self,response):
        if not os.path.exists("bin/admin"):
            os.mkdir("bin/admin")
        with open("bin/admin/allusers.dat",'wb') as newfile:
           pickle.dump(response,newfile)
        msg = "Recieved %d users from server"%len(response)
        style = (msg,"INFORMATION",wx.ICON_INFORMATION)
        
    def _getgclientsFeedback(self,response):        
        with open("bin/groupclients.dat",'wb') as newfile:
                pickle.dump(response,newfile)
        # fun.update_gclients()
        
    def _messageBox(self,msg,title,icon):
        app = wx.App(True)
        wx.MessageBox(msg,title,icon)
        app.MainLoop()
        return

    
class classClient(object):
    def __init__(self,credentials,details):
        self.credentials = credentials
        self.server = None
        self.details = details
        self.host = self.hostGetter()

    def hostGetter(self):
        if os.path.exists("AppDetails.data"):
            with open("AppDetails.data","r") as f:
                return f.readline().rstrip()
        else:return "localhost"

    def runEngine(self):
        self.connect().addCallback(
            lambda _: self.send_sms_list()).addErrback(
                self.catchFailure)

    def connect(self):    
        factory = pb.PBClientFactory()
        reactor.connectTCP(self.host, 13333, factory)
        return factory.login(self.credentials).addCallback(self._connect)

    def _connect(self,rootObj):
        self.server = rootObj

    def catchFailure(self, failure):
        print  failure
        style = (failure.getErrorMessage(),"Connection Error",wx.ICON_ERROR)       
        box = Printer(style)
        box.messageBox()

    def send_sms_list(self):        
        return self.server.callRemote("sendMessage", self.details).addCallback(self._requestFeedback)

    def _requestFeedback(self,response):        
        inbox = InboxManager()        
        if response[0] == "Failure":
            inbox.update(response[2],Identity=["requestFeedback","failed"])            
            wx.MessageBox(response[1],"FeedBack",wx.ICON_WARNING)
        else:            
            inbox.update(response[2],Identity=["requestFeedback","sent"])
            wx.MessageBox("%d sent messages"%(len(response[2])),
                                                     "FeedBack",wx.ICON_INFORMATION)
        
        
class Authorization(object):
    def __init__(self,details):        
        self.server = None
        self.details = details
        self.host = self.hostGetter()

    def hostGetter(self):
        try:
            os.mkdir("bin")
        except:
            pass
        
        if os.path.exists("AppDetails.data"):
            with open("AppDetails.data","r") as f:
                return f.readline().rstrip()
        else:return "calbinyex"

    def runEngine(self):
        self.connect().addCallback(
            lambda _:self.authorize()).addErrback(
                self.catchFailure)

    def connect(self):    
        factory = pb.PBClientFactory()
        reactor.connectTCP(self.host,13333,factory)
        return factory.login(Anonymous()).addCallback(self._connect)

    def _connect(self,rootObj):
        self.server = rootObj

    def catchFailure(self, failure):
        style = (failure.getErrorMessage( ),"Authentification Error",wx.ICON_ERROR)       
        box = Printer(style)
        box.messageBox()

    def authorize(self):        
        return self.server.callRemote("authorizeUser", self.details).addCallback(self._requestFeedback)

    def _requestFeedback(self,users):
        myinfo = users
        with open("bin/authorization.dat",'wb') as newfile:
            pickle.dump(myinfo,newfile)

            
class Administration(object):
    def __init__(self, credentials, Type, details, **keywords):
        self.server = None
        self.details = details
        self.type = Type
        self.host = self.hostGetter()
        self.credentials = credentials
        try:
            self.crit = keywords["crit"]
        except KeyError, e:
            pass
        
    def hostGetter(self):
        if os.path.exists("AppDetails.data"):
            with open("AppDetails.data","r") as f:
                return f.readline().rstrip()
        else:return "localhost"

    def runEngine(self):
        if self.type == "restart":
                self.connect().addCallback(
                        lambda _:self.restart()).addErrback(self.catchFailure)
        elif self.type == "resend":
                self.connect().addCallback(
                        lambda _:self.resendMessages()).addErrback(self.catchFailure)
        elif self.type == "add user":
                self.connect().addCallback(
                        lambda _:self.addUser()).addErrback(self.catchFailure)
        elif self.type == "add check":
                self.connect().addCallback(
                        lambda _:self.addCheck()).addErrback(self.catchFailure)
        elif self.type == "add bank":
                self.connect().addCallback(
                        lambda _:self.addBank()).addErrback(self.catchFailure)
        elif self.type == "add settings":
                self.connect().addCallback(
                        lambda _:self.addSettings()).addErrback(self.catchFailure)
        elif self.type == "get users":
                self.connect().addCallback(
                        lambda _:self.getUsers()).addErrback(self.catchFailure)
        elif self.type == "update user":
                self.connect().addCallback(
                        lambda _:self.updateUser()).addErrback(self.catchFailure)
        elif self.type == "delete user":
                self.connect().addCallback(
                        lambda _:self.deleteUser()).addErrback(self.catchFailure)
        elif self.type == "add group":
                self.connect().addCallback(
                        lambda _:self.addGroup()).addErrback(self.catchFailure)
        elif self.type == "get gname":
                self.connect().addCallback(
                        lambda _:self.getGroupNames()).addErrback(self.catchFailure)        
        elif self.type == "add client":
                self.connect().addCallback(
                        lambda _:self.addGroupClient()).addErrback(self.catchFailure)
        elif self.type == "search client":
                self.connect().addCallback(
                        lambda _:self.searchGroupsClients()).addErrback(self.catchFailure)
        elif self.type == "get clients":
                self.connect().addCallback(
                        lambda _:self.getGroupClients()).addErrback(self.catchFailure)
        elif self.type == "delete client":
                self.connect().addCallback(
                        lambda _:self.deleteGroupClient()).addErrback(self.catchFailure)
        elif self.type == "delete group":
                self.connect().addCallback(
                        lambda _:self.deleteGroup()).addErrback(self.catchFailure)
        elif self.type == "save compd":
                self.connect().addCallback(
                        lambda _:self.saveCompanyDetails()).addErrback(self.catchFailure)
        elif self.type == "update protocol":
                self.connect().addCallback(
                        lambda _:self.updateSmsProtocol()).addErrback(self.catchFailure)

        elif self.type == "audit trail":
                self.connect().addCallback(
                        lambda _:self.getAuditTrail()).addErrback(self.catchFailure)
        elif self.type == "get messages":
                self.connect().addCallback(
                        lambda _:self.getMessages()).addErrback(self.catchFailure)
        elif self.type == "delete messages":
                self.connect().addCallback(
                        lambda _:self.deleteMessages()).addErrback(self.catchFailure)
        else:
            pass
                
    def connect(self):    
        factory = pb.PBClientFactory()
        reactor.connectTCP(self.host,13333,factory)
        return factory.login(self.credentials).addCallback(self._connect)

    def _connect(self,rootObj):
        self.server = rootObj

    def catchFailure(self, failure):
        print failure
        style = (failure.getErrorMessage( ),"Network Error",wx.ICON_ERROR)       
        box = Printer(style)
        box.messageBox()

    def restart(self):        
        return self.server.callRemote("restartServer")

    def resendMessages(self):        
        return self.server.callRemote("restartSendingThread")

    def addCheck(self):
        return self.server.callRemote("addCheck", self.details).addCallback(self._requestFeedback)

    def addBank(self):
        return self.server.callRemote("addBank", self.details).addCallback(self._requestFeedback)

    def addSettings(self):
        return self.server.callRemote("addSettings", self.details).addCallback(self._requestFeedback)

    def addUser(self):        
        return self.server.callRemote("addUser",self.details).addCallback(self._requestFeedback)

    def getUsers(self):        
        return self.server.callRemote("getUsers",self.details).addCallback(self._requestFeedback)

    def updateUser(self):
        return self.server.callRemote("updateUser",self.details).addCallback(self._requestFeedback)

    def deleteUser(self):        
        return self.server.callRemote("deleteUser",self.details).addCallback(self._requestFeedback)

    def addGroup(self):
        return self.server.callRemote("addGroup",self.details).addCallback(self._requestFeedback)

    def getGroupNames(self):
        return self.server.callRemote("getGroupNames",self.details).addCallback(self._requestFeedback)

    def addGroupClient(self):
        return self.server.callRemote("addGroupClient",self.details).addCallback(self._requestFeedback)

    def searchGroupsClients(self):
        return self.server.callRemote("searchGroupsClients",self.details,self.crit).addCallback(self._requestFeedback)

    def getGroupClients(self):
        return self.server.callRemote("getGroupClients",self.details).addCallback(self._requestFeedback)

    def deleteGroupClient(self):
        return self.server.callRemote("deleteGroupClient",self.details).addCallback(self._requestFeedback)

    def deleteGroup(self):
        return self.server.callRemote("deleteGroup",self.details).addCallback(self._requestFeedback)

    def saveCompanyDetails(self):
        return self.server.callRemote("saveCompanyDetails",self.details).addCallback(self._requestFeedback)

    def updateSmsProtocol(self):
        return self.server.callRemote("updateSmsProtocol",self.details).addCallback(self._requestFeedback)

    def getAuditTrail(self):
        return self.server.callRemote("postAudit",self.details).addCallback(self._requestFeedback)

    def getMessages(self):
        return self.server.callRemote("postMessages",self.details).addCallback(self._requestFeedback)

    def deleteMessages(self):
        return self.server.callRemote("deleteMessages",self.details).addCallback(self._requestFeedback)

    def deleteCheck(self):
        return self.server.callRemote("deleteMessages",self.details).addCallback(self._requestFeedback)

    def deleteBank(self):
        return self.server.callRemote("deleteMessages",self.details).addCallback(self._requestFeedback)
    
    def _requestFeedback(self,response):
        if self.type == "get users":
            if not os.path.exists("bin/admin"):
                os.mkdir("bin/admin")            
            with open("bin/admin/allusers.dat",'wb') as newfile:
                pickle.dump(response,newfile)
        elif self.type == "update user":
            if response:
                wx.MessageBox("%s"%"Update Successful","Server Response",wx.ICON_INFORMATION)
            else:
                wx.MessageBox("%s"%"Update could not be made","Server Response",wx.ICON_ERROR)                
        elif self.type == "get gname":
            if not os.path.exists("bin/admin"):
                os.mkdir("bin/admin")            
            for i in response[2]:
                fun.add_new_group(i)
            with open("bin/admin/gnames.dat",'wb') as newfile:
                pickle.dump(response[2],newfile)
            
        elif self.type == "get clients":
            response = pickle.loads(response)
            with open("bin/groupclients.dat",'wb') as newfile:
                pickle.dump(response,newfile)            
            style = (response[1],"INFORMATION",wx.ICON_INFORMATION)
            fun.update_gclients()
            box = Printer(style)
            box.messageBox()
        elif self.type == "audit trail":
            response = pickle.loads(response)
            with open("bin/admin/audit.dat",'wb') as newfile:
               pickle.dump(response,newfile)
        elif self.type == "update protocol":
            wx.MessageBox("%s details have been updated"%response,"Server Response",wx.ICON_INFORMATION)
        elif self.type == "get messages":
            if response[0] == "Failure":
                wx.MessageBox("No messeges found","Server Response",wx.ICON_INFORMATION)
            else:
                inbox = InboxManager()
                data1 = {'current':response[1]}
                inbox.write(data1)
                
        elif self.type == "delete messages":
                if response[0] == "Failure":
                    wx.MessageBox("No messages to delete","Server Response",wx.ICON_ERROR)
                else:
                    wx.MessageBox("%s message(s) deleted"%len(response[1]),"Server Response",wx.ICON_INFORMATION)
        elif self.type == "save compd":
                if response:
                    style = ("Success","SERVER RESPONSE",wx.ICON_INFORMATION)
                else:
                    style = ("Failed","SERVER RESPONSE",wx.ICON_ERROR)
                box = Printer(style)
                box.messageBox()
        elif self.type == "add user":
                if response:
                    style = ("Succesfully added new user","SERVER RESPONSE",wx.ICON_INFORMATION)
                else:
                    style = ("Failed to add new user","SERVER RESPONSE",wx.ICON_ERROR)
                box = Printer(style)
                box.messageBox()
        elif self.type == "add check":
                if response:
                    style = ("Success", "SERVER RESPONSE", wx.ICON_INFORMATION)
                else:
                    style = ("Failed to add new user","SERVER RESPONSE",wx.ICON_ERROR)
                box = Printer(style)
                box.messageBox()

        else:        
             if response[0] == "Error":
                     style = (response[1],"ERROR",wx.ICON_ERROR)
             elif response[0] == False:
                     style = (response[1],"ERROR", wx.ICON_ERROR)
             else:
                print response
                style = (response[1],"INFORMATION", wx.ICON_INFORMATION)
             box = Printer(style)
             box.messageBox()

class ServerAccess:
    def __init__(self, args=None):
        self.username = None
        self.password = None
        self.details = args
        self._initialize()

    def _initialize(self):
        with closing(open("bin/authorization.dat", "rb")) as confidential:
            details = pickle.load(confidential)
            if not details:
                return False
            for user, passwd in details.items():
                self.username = user
                self.password = passwd
            self.creds = credentials.UsernamePassword(self.username, self.password)

    def add_check(self):
        task = Administration(self.creds, "add check", self.details)
        task.runEngine()
        try:
            reactor.run()
        except:
            pass

    def add_bank(self):
        task = Administration(self.creds, "add bank", self.details)
        task.runEngine()
        try:
            reactor.run()
        except:
            pass

    def add_settings(self):
        task = Administration(self.creds, "add settings", self.details)
        task.runEngine()
        try:
            reactor.run()
        except:
            pass


class EasyAccess:    
    def __init__(self, details):
        self.details = details

    def get_group_clients(self):
        username, password = self.details
        creds = credentials.UsernamePassword(username, password)        
        classs = Administration(creds, "get clients", "all")
        classs.runEngine()
        try:
            reactor.run()
        except:
            pass

    def get_Messages(self):
        username, password = self.details
        creds = credentials.UsernamePassword(username, password)        
        classs = Administration(creds, "get messages", "")
        classs.runEngine()
        try:
            reactor.run()
        except:
            pass

    def restart_server(self):
        username, password = self.details
        creds = credentials.UsernamePassword(username, password)        
        classs = Administration(creds,"restart","")
        classs.runEngine()
        try:
            reactor.run()
        except:
            pass

    def resend_messages(self):
        username, password = self.details
        creds = credentials.UsernamePassword(username, password)        
        classs = Administration(creds,"resend","")
        classs.runEngine()
        try:
            reactor.run()
        except:
            pass
        
        
class Printer(object):
    def __init__(self,style):
        self.style = style

    def messageBox(self):
        msg = self.style[0];title = self.style[1];icon = self.style[2]
        wx.MessageBox(msg,title,icon)
        return
                
#runKlass(['guest','asswd1'])
