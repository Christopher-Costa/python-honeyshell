#! /usr/bin/python3

import getopt

class Exit:

    def __init__(self, args, shell):
        self.args = args
        self.shell = shell
        self.parse_args()

        self.execute()

    def parse_args(self):
        optlist, args = getopt.getopt(self.args, '', [])

        if args:
            self.status = args[0]
        else:
            self.status = 0

    def execute(self):
        self.shell.channel.send("logout\n")
        self.shell.clear_line()
        self.shell.channel.close()
        self.shell.session_open = False
