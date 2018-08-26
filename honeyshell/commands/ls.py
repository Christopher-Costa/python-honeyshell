#! /usr/bin/python3

import getopt
import os

class Ls:

    def __init__(self, args, shell):
        self.args = args
        self.shell = shell
        self.show_long = False
        self.show_all = False
        self.show_timesort = False
        self.show_reverse = False
        self.blocksize = 1024

        self.parse_args()

        if self.show_long:
            self.long_list()
        else:
            self.short_list()

    def parse_args(self):
        optlist, args = getopt.getopt(self.args, 'ltra', [])
        for o, a in optlist:
            if o == '-l':
                self.show_long = True
            elif o == '-a':
                self.show_all = True
            elif o == '-t':
                self.show_timesort = True
            elif o == '-r':
                self.show_reverse = True

    def short_list(self):
        files = self.filelist()
        rows = 0

        while True:
            rows += 1
            columns = [sorted(files, key=self.sortname)[x:x + rows] for x in range(0, len(files), rows)]

            max_filenames = []

            for column in columns:
                filenames = [file['name'] for file in column]
                max_filenames.append(max(filenames))

            if len(('  ').join(max_filenames)) <= self.shell.process.width:
                break

            if rows >= len(files):
                break

        for row in range(0, rows):
            line_items = []
            for column in columns:

                try:
                    file = column[row]
                    max_filename = max([file['name'] for file in column], key=len)
                    line_item = self.shell.colorize(file)
                    line_item += ' ' * (len(max_filename) - len(file['name']))
                    line_items.append(line_item)

                except IndexError:
                    pass

            line = ('  ').join(line_items)
            self.shell.channel.send(line + '\r\n')

    def sortname(self, item):
        return item['name'].strip('.')

    def long_list(self):
        files = self.filelist()

        blocks = int(sum([file['blocks'] for file in files]) * 512 / self.blocksize)
        self.shell.channel.send('total ' + str(blocks) + '\r\n')

        links_len = len(str(max([file['nlink'] for file in files])))
        links_format = '%' + str(links_len) + 's '

        user_len = len(max([file['user'] for file in files], key=len))
        user_format = '%' + str(user_len) + 's '

        group_len = len(max([file['group'] for file in files], key=len))
        group_format = '%' + str(group_len) + 's '

        for file in sorted(files, key=self.sortname):
            self.shell.channel.send(self.long_mode(file) + ' ')
            self.shell.channel.send(links_format % str(file['nlink']))
            self.shell.channel.send(user_format % str(file['user']))
            self.shell.channel.send(group_format % str(file['group']))
            self.shell.channel.send(self.shell.colorize(file) + '\r\n')

    def filelist(self):
        fs = self.shell.filesystem
        files = [fs[filename] for filename in fs if fs[filename]['root'] == self.shell.cwd]

        if self.show_all:
            dot = fs[self.shell.cwd]
            dot['name'] = '.'
            dotdot = fs[dot['root']]
            dotdot['name'] = '..'
            files.append(dot)
            files.append(dotdot)

        else:
            files = list(filter(lambda x: x['name'][0] != '.', files))

        return files

    def long_mode(self, file):
        longmode = ''
        mode = file['mode']

        if file['isdir']:
            longmode += 'd'
        elif file['isreg']:
            longmode += '-'
        elif file['isblk']:
            longmode += 'b'
        elif file['islnk']:
            longmode += 'l'
        elif file['ischr']:
            longmode += 'c'
        elif file['issock']:
            longmode += 's'
        elif file['isfifo']:
            longmode += 'p'
        else:
            longmode += '?'

        longmode += 'r' if int(mode, 8) & 256 else '-'
        longmode += 'w' if int(mode, 8) & 128 else '-'
        if int(mode, 8) & 2048:
            if int(mode, 8) & 64:
                longmode += 's'
            else:
                longmode += 'S'
        else:
            if int(mode, 8) & 64:
                longmode += 'x'
            else:
                longmode += '-'

        longmode += 'r' if int(mode, 8) & 32 else '-'
        longmode += 'w' if int(mode, 8) & 16 else '-'
        if int(mode, 8) & 1024:
            if int(mode, 8) & 8:
                longmode += 's'
            else:
                longmode += 'S'
        else:
            if int(mode, 8) & 8:
                longmode += 'x'
            else:
                longmode += '-'

        longmode += 'r' if int(mode, 8) & 4 else '-'
        longmode += 'w' if int(mode, 8) & 2 else '-'
        if int(mode, 8) & 512:
            if int(mode, 8) & 1:
                longmode += 't'
            else:
                longmode += 'T'
        else:
            if int(mode, 8) & 1:
                longmode += 'x'
            else:
                longmode += '-'

        longmode += '.'
        return longmode
