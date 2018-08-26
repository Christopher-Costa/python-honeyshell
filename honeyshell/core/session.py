#! /usr/bin/python3

import paramiko
import socket
from honeyshell.core.process import HoneyshellProcess
from honeyshell.shell import HoneyshellShell

class HoneyshellSession:

    def __init__(self, connection, address, server):
        self.connection = connection
        self.address = address
        self.server = server

    def open(self):
        self.process = HoneyshellProcess()

        ssh_session = paramiko.Transport(self.connection)
        ssh_session.set_gss_host(socket.getfqdn(''))
        ssh_session.load_server_moduli()
        ssh_session.add_server_key(paramiko.RSAKey(filename='keys/user_rsa_key'))
        ssh_session.start_server(server=self.process)

        channel = ssh_session.accept(20)
        self.process.event.wait(10)

        HoneyshellShell(ssh_session, channel, self.server, self.process)
