__author__ = 'Monte'
import os
import hashlib
import cPickle as Pickle
from contextlib import closing
from appmanager import log
from database import DatabaseManager

class Security(object):
    def __init__(self):
        self.initialize()
        self.database_file = "database/smslite.db"
        self.private = "insurance"
        self.data = self.read()
        self.password = self.get_password()
        self.user = self.get_user()
        self.database = self.get_database()

    def read(self):
        with closing(open("bin/config.conf", "rb")) as fl:
            self.data = Pickle.load(fl)
            return self.data

    def write(self):
        with closing(open("bin/config.conf", "wb")) as fl:
            Pickle.dump(self.data, fl)
        log.info("Configuration file successfully updated")

    def get_security_details(self):
        data = self.read()
        if "security" not in self.data.keys():
            log.debug("Creating security details")
            self.data['security'] = {'user': "server",
                                     'password': self.create_signature("secrete_key")}
            self.password = self.data['security']['password']
            self.user = self.data['security']['user']
            self.write()
        return data["security"]

    def get_password(self):
        try:
            return self.get_security_details()['password']
        except KeyError:
            log.warning("Configuration file missing database password")
            return self.create_signature("secrete_key")

    def get_user(self):
        try:
            return self.get_security_details()['user']
        except KeyError:
            log.warning("Configuration file missing database user name")
            return "server2"

    def create_signature(self, data):
        digest = hashlib.sha1(repr(data) + "," + self.private).hexdigest()
        return digest

    def verify_password(self, data):
        signature = self.password
        return signature == self.create_signature(data)

    def change_password(self, password):
        log.info("Changing password...")
        password = self.create_signature(password)
        self.data["security"]['password'] = self.password = password
        self.write()
        return True

    def change_username(self, username):
        log.info("Changing username...")
        self.data["security"]['user'], self.password = username
        self.write()
        return True

    def get_dialect(self):
        try:
            return self.data["connection"]["dialect"]
        except KeyError:
            log.warning("Database dialect missing")
            return "mysql"

    def get_database(self):
        try:
            return self.data["connection"]["database"]
        except KeyError:
            log.warning("Database name missing")
            return "bima"

    def initialize(self):
        dirs = ["bin", "database"]
        for dir_name in dirs:
            if not os.path.exists(dir_name):
                os.mkdir(dir_name)
        file_name = "bin/dialect"
        if not os.path.exists(file_name):
            if not Security.confirm():
                fl = file(file_name, "wb")
                fl.write("sqlite")
                fl.close()
                self.dialect = "sqlite"
            else:
                with open(file_name, "wb") as fl:
                    fl.writelines(["root\n", "creawib\n", "127.0.0.1\n"])
                    fl.seek(0)
                self.dialect = "mysql"
        else:
            fl = file(file_name, "rb")
            self.dialect = str(fl.readline())
            fl.close()

    @staticmethod
    def confirm():
        import wx
        app = wx.App(False)
        dlg = wx.MessageBox("Do you want to use MySQL Database?", "Connection", wx.ICON_INFORMATION | wx.YES_NO)
        if dlg == wx.YES:
            return True
        app.MainLoop()
        return False

    def database_connection(self):
        db = DatabaseManager()
        if self.dialect == "sqlite":
            if not os.path.exists("database/smslite.db"):
                fl = file("database/smslite.db", "wb")
                fl.close()
            db.connect(user=self.user, passwd=self.password)
        else:
            db.connect(dialect="mysql", user=self.user, passwd=self.password, database=self.database)
        return db
