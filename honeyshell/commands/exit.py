#! /usr/bin/python3

import getopt

class Exit:

    def __init__(self, args, shell):
        self.args = args
        self.shell = shell
        self.parse_args()

        self.execute()

    def parse_args(self):
        optlist, args = getopt.getopt(self.args, 'LP', [])

        if args:
            self.status = args[0]
        else:
            self.status = 0

    def execute(self):
        self.shell.channel.close()
        self.shell.session_open = False
