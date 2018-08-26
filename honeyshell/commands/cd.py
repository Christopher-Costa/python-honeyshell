#! /usr/bin/python3

import getopt

class Cd:

    def __init__(self, args, shell):
        self.args = args
        self.shell = shell
        self.parse_args()

        self.execute()

    def parse_args(self):
        optlist, args = getopt.getopt(self.args, 'LP', [])

        if args:
            self.target = args[0].rstrip('/')
        else:
            self.target = self.shell.home

    def execute(self):
        fs = self.shell.filesystem

        if self.target.startswith('/'):
            directory_path = self.target            
        elif self.target == '..':
            directory_path = '/'.join(self.shell.cwd.split('/')[:-1]) or '/'
        elif self.target == '~' or not self.target:
            directory_path = self.shell.home
        else:
            directory_path = self.shell.cwd + '/' + self.target
                                
        if directory_path in fs:
            if fs[directory_path]['isdir']:
                self.shell.cwd = directory_path
            else:
                self.shell.channel.send("-bash: cd: " + self.target + ": Not a directory\n")
        else:
            self.shell.channel.send("-bash: cd: " + self.target + ": No such file or directory\n")
