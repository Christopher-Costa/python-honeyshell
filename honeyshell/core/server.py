#! /usr/bin/python3

import pickle
import sys
import _thread as thread
from core.socket import HoneyshellSocket
from core.session import HoneyshellSession

class HoneyshellServer:

    def __init__(self):
        self.filesystem = pickle.load(open('fs/filesystem.p', 'rb'))
        self.socket = HoneyshellSocket(port=2200)
        self.last_login_time = 0
        self.last_login_addr = ''
        self.last_failed_time = 0
        self.last_failed_addr = ''
        self.num_failed = 0

    def start(self):
        print ("Honeyshell started...")
        while True:
            try:
                connection, address = self.socket.socket.accept()
                print ("Honeyshell connection from {0}".format(address))
                ssh_connection = HoneyshellSession(connection, address, self)
                thread.start_new_thread(ssh_connection.open, ())

            except KeyboardInterrupt:
                print("Honeyshell terminated by user...")
                break
