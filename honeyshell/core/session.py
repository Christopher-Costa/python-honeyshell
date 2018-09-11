#! /usr/bin/python3

import paramiko
import socket
from core.process import HoneyshellProcess
from core.shell import HoneyshellShell

class HoneyshellSession:

    def __init__(self, connection, address, server):
        self.connection = connection
        self.address = address
        self.server = server

    def open(self):
        self.process = HoneyshellProcess(self)
        ssh_session = paramiko.Transport(self.connection)
        ssh_session.set_gss_host(socket.getfqdn())
        ssh_session.load_server_moduli()
        ssh_session.add_server_key(paramiko.RSAKey(filename='keys/id_rsa'))
        ssh_session.start_server(server=self.process)

        print ("Honeyshell session established...")
        channel = ssh_session.accept(20)
        self.process.event.wait(10)

        HoneyshellShell(ssh_session, channel, self, self.server, self.process)
        print ("Honeyshell session disconnected...")
