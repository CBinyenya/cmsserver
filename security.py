__author__ = 'Monte'
import os
import hashlib
import cPickle as Pickle
from contextlib import closing
from appmanager import log

class Security(object):
    def __init__(self):
        self.private = "insurance"
        self.data = self.read()
        self.password = self.get_password()
        self.user = self.get_user()
        self.dialect = self.get_dialect()
        self.database = self.get_database()

    def read(self):
        if not os.path.exists("bin/config.conf"):
            log.warning("Configuration file missing")
            from cron import FileManager
            FileManager()

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
            self.data['security'] = {'user': "server2",
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

