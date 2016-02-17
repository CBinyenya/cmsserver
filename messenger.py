import os
import sys
import urllib
import urllib2
import json
import cPickle as Pickle
from contextlib import closing


class Messenger(object):
    def __init__(self, content, **kwd):
        self.list = content
        self.kwd = kwd

    def check_config(self, protocol):
        """Configures the usernames,key and port numbers"""
        def read():
            try:
                with closing(open("bin/conf", "rb")) as fl:
                    data = Pickle.load(fl)
                return data[protocol]
            except IOError:
                details = {
                    "smsleopard": (u'kbmainspire', u'25d2de9be8879140f495ec80e4d042fa5a53b2f7dd1f3c940ab6c00d26505b0c',
                                   u'K-BIMA')
                }
                with closing(open("bin/conf", "wb")) as fl:
                    Pickle.dump(details, fl)
                return details

        def write(dict1):
            dict2 = read()
            dict2.update(dict1)
            with closing(open("bin/conf", "wb")) as fl:
                Pickle.dump(dict2, fl)
        try:
            if not read():
                raise KeyError
        except KeyError:
            get = raw_input("Do you want to configure %s? ('y' for yes and 'n' for no)" % protocol)
            if get == "y":
                name = raw_input("Enter your username:\t")
                key = raw_input("Enter your key or port number:\t")
                sender_id = raw_input("Enter the Sender ID")
                dictio = {protocol: (name, key, sender_id)}
                write(dictio)

    def send_bulksms(self):
        """Sending a general message to recipients in the list"""        
        inst = PhoneNumber(self.list[0])
        msg = self.list[-1]
        numbers = inst.list_of_numbers()        
        if not numbers:
            print >>sys.stderr, "Invalid number(s)"
            return False
        recipients, message = numbers, msg
        sender = SmsLeopard(recipients, message)
        print "about to send bulk message" 
        response = sender.send_message()
        if not isinstance(response, list):
            return False
        sent, failed = self.send_message(response)
        print>>sys.stdout, "%d sent message(s) & %d failed message(s)" % (len(sent), len(failed))
        return sent, failed
    
    def send_sms(self):
        """Sends personalized messages for a specific individual"""
        numbers = self.list
        sent = list()

        def send():
            for number in numbers:
                inst = PhoneNumber(number[0])
                phn = inst.list_of_numbers()
                if not phn:
                    print >>sys.stderr, "Error Invalid number(s) "
                    return False
                recipients, message = phn, number[1]
                sender = SmsLeopard(recipients, message)
                response = sender.send_message()

                if isinstance(response, list):
                    print "confirmed tuple messages"
                    if response[0][1] == "Success":
                        numbers.remove(number)
                        sent.append(number)
        send()
        return sent, [numbers]
        
    def send_message(self, response):
        sent = []
        failed = []                                    
        for msg in response:
            if msg[1] == "Success":
                sent.append(msg[0])
            else:
                failed.append(msg[0])            
        return sent, failed


class SmsLeopard(object):    
    def __init__(self, recpts, msg):
        self.username, self.apikey, self.sender_id = ('', '', None)
        self.recpts = recpts
        self.msg = msg
        
    def init(self):
        if not self.get_data():
            print >>sys.stderr, "Smsleopard is not configured,username & apikey are missing"
            return False
        self.username, self.apikey, self.sender_id = self.get_data()
        return True
        
    def get_data(self):
        """ Gets the username and apikey from the file config """
        try:
            with closing(open("bin/conf", "rb")) as fl:
                data = Pickle.load(fl)
                return data["smsleopard"]
        except IOError:
            return

    def recipient(self):
        """Generates a string of users from the resipients list"""
        user2 = ""
        for user in self.recpts:
            user2 = user2 + "," + str(user)        
        return user2[1:]
    
    def send_message(self):
        """sends message and returns a tuple of the send status and cost"""
        if not self.init():
            return False
        response = []
        gateway = AfricasTalkingGateway(self.username, self.apikey, self.sender_id)
        to = self.recipient()        
        try:
            recipients = gateway.send_message(to, self.msg)
            for recipient in recipients:
                response.append((recipient['number'], recipient['status'], recipient['cost'], self.msg))
        except AfricasTalkingGatewayException, e:
            print >>sys.stderr, 'Encountered an error while sending: %s' % str(e)
        except urllib2.URLError:
            print >>sys.stderr, "Internet error"
            response = False
        finally:
            return response
        
        
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

        
class AfricasTalkingGatewayException(Exception):
    pass


class AfricasTalkingGateway:    
    def __init__(self, username_, apiKey_, from_=None):
        self.from_ = from_
        self.username = username_
        self.apiKey = apiKey_	
        self.SMSURLString = "https://api.africastalking.com/version1/messaging"
        self.VoiceURLString = "https://voice.africastalking.com/call"
        
    def send_message(self, to_, message_, from_ = None, bulkSMSMode_ = 1, enqueue_ = 0, keyword_ = None, linkId_ = None):
        """
        The optional from_ parameter should be populated with the value of a shortcode or alphanumeric that is
        registered with us
        The optional bulkSMSMode_ parameter will be used by the Mobile Service Provider to determine who gets billed for a
        message sent using a Mobile-Terminated ShortCode. The default value is 1 (which means that
        you, the sender, gets charged). This parameter will be ignored for messages sent using
        alphanumerics or Mobile-Originated shortcodes.
        The optional enqueue_ parameter is useful when sending a lot of messages at once where speed is of the essence
         
         The optional keyword_ is used to specify which subscription product to use to send messages for premium rated short codes
         
         The optional linkId_ parameter is pecified when responding to an on-demand content request on a premium rated short code
         
        """
        if len(to_) == 0 or len(message_) == 0:
                raise AfricasTalkingGatewayException("Please provide both to_ and message_ parameters")

        values = {
            'username': self.username,
            'to': to_,
            'message': message_
        }

        from_ = self.from_
        if from_ is not None:
            values["from"] = self.from_
            values["bulkSMSMode"] = bulkSMSMode_

        if enqueue_ > 0:
            values["enqueue"] = enqueue_

        if keyword_ is not None:
            values["keyword"] = keyword_

        if linkId_ is not None:
            values["linkId"] = linkId_

        headers = {
            'Accept': 'application/json',
            'apikey': self.apiKey
        }

        try:
            data = urllib.urlencode(values)
            request = urllib2.Request(self.SMSURLString, data, headers=headers)
            response = urllib2.urlopen(request)
            the_page = response.read()
        except urllib2.HTTPError as e:
            the_page = e.read()
            decoded = json.loads(the_page)
            raise AfricasTalkingGatewayException(decoded['SMSMessageData']['Message'])
        else:
            decoded = json.loads(the_page)
            recipients = decoded['SMSMessageData']['Recipients']
            return recipients

    def fetchMessages(self, lastReceivedId_):

        url = "%s?username=%s&lastReceivedId=%s" % (self.SMSURLString, self.username, lastReceivedId_)
        headers = {
            'Accept': 'application/json',
            'apikey': self.apiKey
        }

        try:
            request = urllib2.Request(url, headers=headers)
            response = urllib2.urlopen(request)
            the_page = response.read()

        except urllib2.HTTPError as e:

            the_page = e.read()
            decoded = json.loads(the_page)
            raise AfricasTalkingGatewayException(decoded['SMSMessageData']['Message'])

        else:

            decoded = json.loads(the_page)
            messages = decoded['SMSMessageData']['Messages']

            return messages

    def call(self, from_, to_):
        values = {
            'username': self.username,
            'from': from_,
            'to': to_
        }

        headers = {
            'Accept': 'application/json',
            'apikey': self.apiKey
        }

        try:
            data = urllib.urlencode(values)
            request = urllib2.Request(self.VoiceURLString, data, headers=headers)
            response = urllib2.urlopen(request)

        except urllib2.HTTPError as e:

            the_page = e.read()
            decoded = json.loads(the_page)
            raise AfricasTalkingGatewayException(decoded['ErrorMessage'])

