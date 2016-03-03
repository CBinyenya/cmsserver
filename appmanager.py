__author__ = 'Monte'
import os
import wx
import time
import urllib2
import platform
import logging
import socket

REMOTE_SERVER = "www.google.com"
LOCK = False

class Printer(object):

    def __init__(self, msg):
        self.msg = msg


    def get_input(self):
        dlg = wx.TextEntryDialog(self, self.msg, "Database Connection", 'Server')
        if dlg.ShowModal() == wx.ID_OK:
            dlg.Destroy()
            entrty = dlg.GetValue()
        else:
            entrty = None

        return entrty

def log():
    if platform.platform().startswith('Windows'):
        logging_file = os.path.join(os.getenv('HOMEDRIVE'), os.getenv('HOMEPATH'), 'server2.ini')

    else:
        logging_file = os.path.join(os.getenv('HOME'), 'server2.ini')
        os.chdir('/home/server2/server1.3')
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s: %(levelname)s: %(message)s', filename=logging_file,
                            filemode='w',)
    return logging
log = log()

def check_network_connection():
    lock = True

    def urllib2_check():
        global LOCK
        try:
            urllib2.urlopen("http://google.com", timeout=20)
            LOCK = False
            lock = True
        except urllib2.URLError:
            if not LOCK:
                log.warning("No internet connection!")
                LOCK = True

    while True:
        try:
            socket.gethostbyname(REMOTE_SERVER)
            if lock:
                log.info("Internet access")
                lock = False
            time.sleep(30)
        except socket.error:
            urllib2_check()


