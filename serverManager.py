import os
import sys
import cPickle as Pickle
from twisted.internet import reactor
from twisted.spread import pb
from twisted.cred import credentials
from appmanager import log
from twisted.internet.error import DNSLookupError, ReactorNotRestartable, ReactorAlreadyRunning

clients = []
def runKlass(details):        
        username, password = details
        creds = credentials.UsernamePassword(username, password)
        tester = Messanger(creds)
        tester.runEngine()
        try:
            reactor.run()
        except ReactorNotRestartable, e:
            print e
            factory = pb.PBClientFactory()
            reactor.connectTCP("server", 13333, factory)
        except ReactorAlreadyRunning, e:
            pass


class Messanger(object):
    def __init__(self, credentials):
        self.credentials = credentials
        self.server = None
        self.clients = []
        self.host = self.hostGetter()
        
    def hostGetter(self):
        if os.path.exists("bin/read"):
            with open("bin/read", "r") as f:
                try:
                    return f.readlines()[2].replace("\n", '')
                except IndexError:
                    return "server"
        else:
            return "server"
    
    def runEngine(self):
        self.connect().addCallback(
            lambda _: self.get_company_details()).addCallback(
            lambda _: self.get_clients_with_balance()).addCallback(
            lambda _: self.get_clients_with_renewal()).addCallback(
            lambda _: self.get_clients_with_expiry()).addCallback(
            lambda _: self.get_all_clients()).addCallback(            
            self._catchFailure).addCallback(
            lambda _: reactor.stop())

    def connect(self):    
        factory = pb.PBClientFactory()
        reactor.connectTCP(self.host, 13333, factory)
        return factory.login(self.credentials).addCallback(self._connect)

    def _connect(self, rootObj):
        self.server = rootObj

    def _catchFailure(self, failure):
        if not failure:
            return
        log.warning(failure.getErrorMessage)
        print failure.getErrorMessage()

    def get_clients_with_balance(self):
        print >>sys.stderr, "Calling for clients with balance from server.."
        return self.server.callRemote("postBalance").addCallback(self._got_clients_with_balance)

    def get_clients_with_renewal(self):
        print >>sys.stderr, "Calling for clients with renewals from server.."
        return self.server.callRemote("postRenewals").addCallback(self._got_clients_with_renewal)

    def get_clients_with_expiry(self):
        print >>sys.stderr, "Calling for clients with expiry from server.."
        return self.server.callRemote("postExpiry").addCallback(self._got_clients_with_expiry)

    def get_all_clients(self):
        print >>sys.stderr, "Calling for clients from server.."
        return self.server.callRemote("postClients").addCallback(self._got_all_clients)

    def get_company_details(self):        
        return self.server.callRemote("getCompanyDetails").addCallback(self._getCompanyDetails)

    def _got_clients_with_balance(self, arg):
        self.save_data(arg, "balance")

    def _got_clients_with_renewal(self, arg):
        self.save_data(arg, "renewal")

    def _got_clients_with_expiry(self, arg):
        self.save_data(arg, "expiry")

    def _got_all_clients(self, arg):
        self.save_data(arg, "allclients")

    def _getCompanyDetails(self, arg):
        self.save_data(arg, "compdetails")

    def save_data(self, data, type_):
        if isinstance(data, list) or isinstance(data, dict) or isinstance(data, tuple):
            length = len(data)
        elif isinstance(data, str):
            data = Pickle.loads(data)
            length = len(data)
        else:
            return
        msg = "Saving downloaded data for %s with length %d" % (type_, length)
        type_ = "bin/%s%s" % (type_, ".dat")

        def save():
            with open(type_, 'wb') as fl:
                Pickle.dump(data, fl)
            log.info(msg)
            print >>sys.stderr, msg
        save()

if __name__ == '__main__':
    runKlass(['admin', 'passwd'])
