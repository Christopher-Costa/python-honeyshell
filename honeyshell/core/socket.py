#! /usr/bin/python3

import socket

class HoneyshellSocket:

    def __init__(self, port=2200):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
        self.socket.listen(5)
