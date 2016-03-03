__author__ = 'Monte'
"""
This module initializes the application's automated features that include sending of text messages and reminders to the
users.
"""
import sys
import math
import string
import datetime
import cPickle as Pickle
import serverManager
from appmanager import *
from threading import Thread
from contextlib import closing

from database import DatabaseManager
from messenger import Messenger
from security import Security
from functions import FileManager

# Setting up important system configurations
class MessageController(FileManager):
    def __init__(self, database_controller):
        FileManager.__init__(self)
        self.now = datetime.datetime.now()
        self.db = database_controller

    def central_command(self):
        with closing(open(self.config_file, "rb")) as fl:
            config = Pickle.load(fl)

        def message_creator(message_type, message_details, message_recipients, message_):
            deltas = list()
            try:
                interval = message_details["interval"]
            except KeyError:
                interval = []
            if interval:
                for days in interval:
                    if not isinstance(days, int):
                        continue
                    time_delta = datetime.timedelta(days=days)
                    delta = self.now + time_delta
                    deltas.append(delta)
            compiled_list = list()
            if message_type == "renewal":
                for recipient in message_recipients:
                    name, phone, policy, date = recipient['Name'], recipient['Phone'],\
                        recipient['Policy'], recipient['To']
                    try:
                        values = dict()
                        values['POLICY'] = policy
                        values['DATE'] = date.date()
                    except AttributeError:
                        continue
                    t = string.Template(message_)
                    for delta in deltas:
                        if delta.date() == date.date() and phone is not None:
                            phone = phone.replace(' ', "")
                            compiled = ([name, phone], t.substitute(values))
                            compiled_list.append(compiled)

            elif message_type == "newinvoice":
                for recipient in message_recipients:
                    phone, policy, amount = recipient['Phone'], recipient['Policy'],\
                        recipient['Amount']
                    name = recipient['Name']
                    amount = math.ceil(amount*100)/100
                    values = dict()
                    values['POLICY'] = policy
                    values['AMOUNT'] = amount
                    t = string.Template(message_)
                    if phone is not None:
                        phone = phone.replace(' ', "")
                        compiled = ([name, phone], t.substitute(values))
                        compiled_list.append(compiled)

            elif message_type == "balance":
                try:
                    balance = message_details["amount"]
                    if not isinstance(balance, int):
                        return
                except KeyError:
                    log.warning("Minimum balance amount is not specified")
                    self.reporter(("Error", "Minimum balance amount is not specified"))
                    return
                for recipient in message_recipients:
                    phone, amount = recipient['Phone'], recipient['Amount']
                    amount = math.ceil(amount*100)/100
                    name = recipient['Name']
                    values = dict()
                    values['AMOUNT'] = amount
                    t = string.Template(message_)
                    if int(amount) > balance and phone is not None:
                        phone = phone.replace(' ', "")
                        compiled = ([name, phone], t.substitute(values))
                        compiled_list.append(compiled)

            elif message_type == "cheque":
                for recipient in message_recipients:
                    due_date, name, amount, phone= recipient['Due'], recipient['Name'],\
                        recipient['Amount'], recipient['Phone']
                    values = dict()
                    values['NAME'] = name
                    values['DUE'] = due_date.date()
                    values['AMOUNT'] = amount
                    values['TYPE'] = recipient['Type']
                    values['NUMBER'] = recipient['Number']
                    values['BANK'] = recipient['Bank']
                    t = string.Template(message_)
                    for delta in deltas:
                        if delta.date() == due_date.date() and phone is not None:
                            phone = phone.replace(' ', "")
                            compiled = ([name, phone], t.substitute(values))
                            compiled_list.append(compiled)
            elif message_type == "birthday":
                for recipient in message_recipients:
                    name, dob, phone = recipient['Name'], recipient['dob'], recipient['Phone']
                    if phone is not None and dob is not None:
                        if self.now.month == dob.date().month and self.now.day == dob.date().day:
                            phone = phone.replace(' ', "")
                            compiled = ([name, phone], message_)
                            compiled_list.append(compiled)
            else:
                print "Cannot find the type specified"
            return compiled_list

        for key, type_ in self.files.items():
            print "this is the type %s" % key
            message_type_ = config[key]
            if not message_type_['status']:
                print "%s has been disabled" % key
                log.warning("%s has been disabled" % key)
                continue
            try:
                message = [x for x in self.db.get_messages() if x['Type'] == key]
                message = message[0]['Message']
                print message
            except IndexError:
                with closing(open(self.message_file, "rb")) as fl:
                    messages = Pickle.load(fl)
                message = messages[key]
            except KeyError:
                log.warning("Controller cannot find %s messages" % key)
                continue
            try:
                details = config[key]
            except KeyError:
                log.warning("Configurations for %s is missing" % key)
                continue
            get_recipients = self.read_file(key)
            if key == "cheque":
                get_recipients = (True, self.db.get_cheques())
            if get_recipients[0]:
                recipients = get_recipients[1]
                msg = "Collecting %s files" % key
                log.debug(msg)
                print >>sys.stdout, msg
                if isinstance(message_creator(key, details, recipients, message), list):
                    complete_list = message_creator(key, details, recipients, message)
                    for every_msg in complete_list:
                        inst = PhoneNumber(every_msg[0][1])
                        phn = inst.list_of_numbers()
                        if phn:
                            print [every_msg[0][0], phn[0], "waiting", every_msg[1], self.now]
                            self.db.add_outbox([every_msg[0][0], phn[0], "waiting", every_msg[1], self.now])
                else:
                    msg = "Error in collecting %s details" % key
                    log.warning(msg)
                    print >>sys.stdout, msg
                    continue
            else:
                log.warning("Cant get recipients for %s" % key)


class PhoneNumber(object):
    def __init__(self, phn):
        self.phn = phn

    def list_of_numbers(self):
        if isinstance(self.phn, list):
            return self.list_phoneno_formater(self.phn)
        elif isinstance(self.phn, long):
            return self.int_phoneno_formater(self.phn)
        elif isinstance(self.phn, int):
            return self.int_phoneno_formater(self.phn)
        elif isinstance(self.phn, str):
            return self.str_phoneno_formater(self.phn)
        else:
            return "Wrong format"

    def list_phoneno_formater(self, the_list):
        valid_list = []
        for number in the_list:
            if self.phone_no_validator(number) is not False:
                valid_list.append(self.phone_no_validator(number))
        if not valid_list:
            return []
        else:
            return valid_list

    def int_phoneno_formater(self, the_int):
        valid_list = []
        if self.phone_no_validator(the_int) is not False:
            valid_list.append(self.phone_no_validator(the_int))
            return valid_list
        else:
            return []

    def str_phoneno_formater(self, the_str):
        valid_list = []
        the_str.replace(' ', "")
        if self.phone_no_validator(the_str) is not False:
            valid_list.append(self.phone_no_validator(the_str))
            return valid_list

        else:
            return []

    def phone_no_validator(self, phnno):
        try:
            phnno = str(phnno)
            if phnno[0] != "+":
                int(phnno)

        except ValueError:
            return False
        phnno.replace(' ', "")
        length = len(phnno)
        if length < 9:
            return False
        elif length == 9:
            if phnno[:1] == "0":
                print phnno, "has less values"
                return False

            return "%s%s" % ("+254", phnno)
        elif length == 10:
            return "%s%s" % ("+254", phnno[1:])
        elif length == 12:
            if phnno[:3] == "254":
                return "%s%s" % ("+", phnno)
            else:
                return False
        elif length == 13:
            if phnno[:4] == "+254":
                return phnno
            else:
                return False
        else:
            return False



class Initializer:
    def __init__(self):
        self.nothing = ""
        self.folder_handler()

    def folder_handler(self):
        folders = ["bin", "database"]
        for folder in folders:
            try:
                os.mkdir(folder)
            except OSError:
                continue

    def important_files(self):
        self.nothing = ""
        if os.path.exists("bin/details.txt"):
            return
        with closing(open("bin/details.txt", "w")) as fl:
            fl.write(time.ctime())
        return True


class Controller(object, Initializer):
    def __init__(self):
        self.now = datetime.datetime.today()
        self.latter = datetime.timedelta(hours=24) + self.now
        self.db = DatabaseManager()
        self.sec = Security()
        self.user = self.sec.user
        self.password = self.sec.password
        self.dialect = self.sec.dialect
        self.database = self.sec.database
        self.db.connect(dialect=self.dialect, user=self.user, passwd=self.password, database=self.database)
        self.waiting_messages = list()
        Initializer.__init__(self)

    def daily_messenger(self):
        """
                Manages the application clock
        """
        seconds = 30
        while True:
            time.sleep(seconds)
            if self.now.hour < 8:
                hour = (8 - self.now.hour) + 24
            elif self.now.hour > 8:
                hour = (24 - self.now.hour)
            else:
                hour = 24
            self.latter = datetime.timedelta(hours=hour) + self.now
            seconds = hour * 60 * 60
            self.now = datetime.datetime.now()
            msg = "Daily Thread initiating messenger"
            log.info(msg)
            print >>sys.stdout, msg
            if self.time_checker():
                log.debug("Daily Thread system update")
                message_controller = MessageController(self.db)
                message_controller.central_command()
            self.message_sender()
            with closing(open("bin/details.txt", "w")) as fl:
                fl.write(time.ctime())
            
    def hourly_messenger(self):
        while True:
            time.sleep(3600)
            collect_data()
            self.message_collector()
            msg = "Hourly Thread initiating messenger"
            log.info(msg)
            print >>sys.stdout , msg
            self.message_sender()

    def hustler(self):
        daily_thread = Thread(target=self.daily_messenger, name="Daily Thread")
        hourly_thread = Thread(target=self.hourly_messenger, name="Hourly Thread")
        daily_thread.start()
        hourly_thread.start()

    def message_collector(self):
        self.waiting_messages = list()
        messages = self.db.get_outbox("waiting")
        if isinstance(messages, list) and messages:
            for message in messages:
                inst = PhoneNumber(message["phone"])
                phn = inst.list_of_numbers()
                if phn:
                    message_tuple = (message["phone"], message["message"])
                else:
                    continue
                self.waiting_messages.append(message_tuple)

    def time_checker(self):
        if not os.path.exists("bin/details.txt"):
            return True
        with closing(open("bin/details.txt", "rb")) as fl:
            start_date = fl.readline()
            if start_date[:10] == time.ctime()[:10]:
                print False, start_date[:10], time.ctime()[:10]
                return False
            else:
                print True, start_date[:10], time.ctime()[:10]
                return True

    def message_sender(self):
        self.message_collector()
        msg = "%d messages waiting to be sent" % len(self.waiting_messages)
        log.info(msg)
        print >>sys.stdout, msg
        sent_list = []
        for message in self.waiting_messages:
            sender = Messenger([message])
            sender.check_config("smsleopard")
            sent_msg = sender.send_sms()[0]
            sent_list.extend(sent_msg)
        msg = "%d sent messages" % len(sent_list)
        log.info(msg)
        for sent in sent_list:
            self.db.update_outbox(sent)


def collect_data():
    security = Security()
    user = security.user
    passwd = security.password
    seconds = 0
    while True:
        time.sleep(seconds)
        serverManager.runKlass((user, passwd))
        seconds += 60



def main_function():
    FileManager()
    cont = Controller()
    cont.hustler()
    cont.db.add_server_log((cont.now, "Loop 1: Scrapping for messages"))


def main():
    log.info("Starting off the system")
    msg = "Starting off the system"
    print >>sys.stdout, msg
    thr1 = Thread(target=check_network_connection, name="Network Manager")
    t = Thread(target=main_function, name="Main thread")

    thr1.start()
    t.start()
    collect_data()


if __name__ == '__main__':
    main()
    
