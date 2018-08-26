#! /usr/bin/python3

import pickle
import _thread as thread
from honeyshell.core.socket import HoneyshellSocket
from honeyshell.core.session import HoneyshellSession

class HoneyshellServer:

    def __init__(self):
        self.filesystem = pickle.load(open('fs/filesystem.p', 'rb'))
        self.socket = HoneyshellSocket(port=2200)

    def start(self):
        while True:
            connection, address = self.socket.socket.accept()
            ssh_connection = HoneyshellSession(connection, address, self)
            thread.start_new_thread(ssh_connection.open, ())
