__author__ = 'Monte'
"""
This module initializes the application's automated features that include sending of text messages and reminders to the
users.
"""
import os
import math
import time
import string
import datetime
import cPickle as Pickle
import serverManager
from threading import Thread
from contextlib import closing
from database import DatabaseManager
from messenger import Messenger


class FileManager(object):
    """
    Contains methods responsible for managing the crucial file components of the application
    This files include:
    allclients.dat
    balance.dat
    extensions.dat
    expiry.dat
    checks.dat
    config.conf
    etc.
    """
    def __init__(self):
        self.files = {
            "clients": "allclients.dat",
            "balance": "balance.dat",
            "renewal": "expiry.dat",
            "newinvoice": "renewal.dat",
            "extension": "extensions.dat",
            "check": "checks.dat",
            "birthday": "allclients.dat"

        }
        self.report_file = "bin/report"
        self.message_file = "bin/messages"
        self.config_file = "bin/config.conf"
        self.folders = ["bin"]
        self.initializer()
        self.configarations()

    def initializer(self):
        self.reporter(("server", "initializing the application"))
        for name in self.folders:
            if not os.path.exists(name):
                os.mkdir(name)
        for key, name in self.files.items():
            name = "bin/" + name
            if not os.path.exists(name):
                msg = key + " file missing"
                self.reporter((False, msg))

            else:
                msg = key + " file found"
                self.reporter(("server", msg))

    def configarations(self):
        """
         interval is the date differences that the messages should be sent.
         status determines if the messages are to be sent or not
         next means the next date general messages have to be sent
        """
        config_types = {
            "clients": {"interval": False, "status": False, "next": False},
            "balance": {"interval": False, "status": False, "amount": 500},
            "renewal": {"interval": [15, 5], "status": True},
            "newinvoice": {"interval": [15, 5], "status": False},
            "extension": {"interval": [15, 5], "status": False},
            "birthday": {"status": True},
            "check": {"interval": [15, 5], "status": True},
        }
        if not os.path.exists(self.config_file):
            with closing(open(self.config_file, "wb")) as fl:
                Pickle.dump(config_types, fl)
        if not os.path.exists(self.message_file):
            self.initialize_messages()

    def reporter(self, details):
        """
        Manages a report file that has details on errors and ho the application
        executes the most important steps.
        The details parameter is either a Tuple or a list of Tuples.
        The tuple has a type of message and the message itself. Error messages
        are represented by a False object while the rest have there specific names
        written out.
        """
        if not os.path.exists(self.report_file):
            with open(self.report_file, "wb") as fl:
                Pickle.dump([], fl)
        with closing(open(self.report_file, "rb")) as fl:
            data = Pickle.load(fl)
        with closing(open(self.report_file, "wb")) as fl:
            if isinstance(details, tuple):
                now = time.ctime()
                type_ = details[0]
                message = details[1]
                data.append((now, type_, message))
            elif isinstance(details, list):
                for detail in details:
                    now = time.ctime()
                    type_ = detail[0]
                    message = detail
                    data.append((now, type_, message))
            Pickle.dump(data, fl)

    def report_reader(self):
        """Returns the content of the report file which can then be written in a logfile"""
        if not os.path.exists(self.report_file):
            return "File does not exist"
        else:
            with closing(open(self.report_file, "rb")) as fl:
                data = Pickle.load(fl)
        return data

    def initialize_messages(self):
        """Creates the message file and initializes the default messages in it"""
        balance = """Dear client,your outstanding insurance premium balance is Ksh $AMOUNT.Kindly
         send your payments.For enquiries call 0714046604.Thanks for your support."""
        renewal = """Dear client your $POLICY policy expires on $DATE. Kindly send us the renewal
         instructions.For enquiries call 0714046604.Thank you"""
        newinvoice = """Dear client. We have renewed your $POLICY policy. Kindly let us have your
         payment of Ksh:$AMOUNT.For enquiries call 0714046604. Thank you."""
        general = ""
        quick = ""
	birthday = """Wishing you the very best as you celebrate your big day. Happy Birthday to you
		from K-BIMA"""
        default = {
            "balance": balance,
            "renewal": renewal,
            "newinvoice": newinvoice,
            "general": general,
            "quicktxt": quick,
            "birthday": birthday
        }
        with closing(open(self.message_file, "wb")) as fl:
                Pickle.dump(default, fl)
        return default

    def read_message(self, type_):
        """Returns the message of the type given in the parameter"""
        if not os.path.exists(self.message_file):
            messages = self.initialize_messages()
        else:
            with closing(open(self.message_file)) as fl:
                messages = Pickle.load(fl)
        try:
            message = messages[type_]
        except KeyError:
            return False
        return message

    def change_message(self, type_, message):
        """Changes the message specified in by the type parameter"""
        with closing(open(self.message_file, "rb")) as fl:
            data = Pickle.load(fl)
        with closing(open(self.message_file, "wb")) as fl:
            data[type_] = message
            Pickle.dump(data, fl)

    def read_file(self, name):
        """Returns the contents of the data files containing the client details eg the balance file"""
        try:
            file_name = "bin/" + self.files[name]
        except KeyError:
            return False, "Invalid file name request"
        try:
            with closing(open(file_name, "rb")) as fl:
                data = Pickle.load(fl)
            if isinstance(data, list):
                return True, data
            else:
                print file_name, type(data)
                return False, "The %s file has been corrupted" % name
        except EOFError:
            return False, "The %s file has been corrupted or cannot be found" % name
        except IOError:
            return False, "The %s file does not exists" % name


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

            elif message_type == "check":
                for recipient in message_recipients:
                    due_date, name, amount, phone = recipient['Due'], recipient['Name'],\
                        recipient['Amount'], recipient['Phone']
                    values = dict()
                    values['NAME'] = name
                    values['DUE'] = due_date
                    values['AMOUNT'] = amount
                    t = string.Template(message_)
                    if not isinstance(due_date, datetime):
                        continue
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
            message_type_ = config[key]
            if not message_type_['status']:
                self.reporter((key, "%s has been disabled"))
                continue
            with closing(open(self.message_file, "rb")) as fl:
                messages = Pickle.load(fl)
            try:
                message = messages[key]
            except KeyError:
                self.reporter((False, "Controller cannot find %s messages" % key))
                continue
            try:
                details = config[key]
            except KeyError:
                self.reporter((False, "Configurations for %s is missing" % key))
                continue
            get_recipients = self.read_file(key)
            if get_recipients[0]:
                recipients = get_recipients[1]
                if isinstance(message_creator(key, details, recipients, message), list):
                    complete_list = message_creator(key, details, recipients, message)
                else:
                    self.reporter(("Error", "%s has an error cant, get its messages"))
                    continue
                for every_msg in complete_list:
                    inst = PhoneNumber(every_msg[0][1])
                    phn = inst.list_of_numbers()
                    if phn:
                        self.db.add_messages([every_msg[0][0], phn[0], "server", every_msg[1], self.now])
                        self.db.add_outbox([every_msg[0][0], phn[0], "waiting",every_msg[1], self.now])
            else:
                print "Cant get recipients for %s" % key


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
        self.important_files()

    def important_files(self):
        self.nothing = ""
        if os.path.exists("bin/details.txt"):
            return
        with closing(open("bin/details.txt", "w")) as fl:
            fl.write(time.ctime()[-13:])
        return True


class Controller(object, Initializer):
    def __init__(self):
        self.now = datetime.datetime.today()
        self.latter = datetime.timedelta(hours=24) + self.now
        self.db = DatabaseManager()
        self.db.connect(dialect="mysql", user="root", passwd="creawib", database="bima")
        serverManager.runKlass(("admin", "passwd"))
        self.waiting_messages = list()
        Initializer.__init__(self)

    def clock_manager(self):
        """
                Manages the application clock
        """
        seconds = 0
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
            self.messenger()

    def messenger(self):
        if self.time_checker():
            self.db.add_server_log((self.now, 0))
            message_controller = MessageController(self.db)
            message_controller.central_command()
            self.message_collector()
        self.message_sender()
        with closing(open("bin/details.txt", "w")) as fl:
            fl.write(time.ctime())
        return True

    def hustler(self):
        td = Thread(target=self.clock_manager)
        td.start()

    def message_collector(self):
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
        with closing(open("bin/details.txt", "rb")) as fl:
            start_date = fl.readline()
            if start_date[:10] == time.ctime()[:10]:
                print False, start_date[:10], time.ctime()[:10]
                return False
            else:
                print True, start_date[:10], time.ctime()[:10]
                return True

    def message_sender(self):
        print "%d messages waiting to be sent" % len(self.waiting_messages)
        sent_list = []
        for message in self.waiting_messages:
            sender = Messenger([message])
            sender.check_config("smsleopard")
            sent_msg = sender.send_sms()[0]
            sent_list.extend(sent_msg)
        for sent in sent_list:
            self.db.update_outbox(sent)


"""time.sleep(360)"""
cont = Controller()
cont.hustler()

