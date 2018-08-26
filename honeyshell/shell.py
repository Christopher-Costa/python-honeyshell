#! /usr/bin/python3

import paramiko
from paramiko.py3compat import b, u, decodebytes
import sys
from honeyshell.commands.ls import Ls

class HoneyshellShell:

    def __init__(self, connection, channel, server, process):
        self.who = 'root'
        self.cwd = '/root'
        self.home = '/root'
        self.connection = connection
        self.channel = channel
        self.process = process
        self.filesystem = server.filesystem
        self.history = []
        self.open = True
        self.dir_color = '\x1b[38;5;27m'
        self.default_color = '\x1b[0m'

        while True:
            command = ''
            specials = ''
            position = 0
            hposition = -1

            if not self.open:
                break

            self.prompt()
            while True:

                char = self.channel.recv(1)

                ###
                # Backspace
                ###
                if ord(char) == 127:
                    if position > 0:
                        c = command
                        command = c[:position - 1] + c[position:]
                        position -= 1

                ###
                # Delete
                ###
                elif ord(char) == 126:
                    if position < len(command):
                        c = command
                        command = c[:position] + c[position+1:]
                        specials += self.cursor_right()
                        #position += 1

                ###
                # Return
                ###
                elif ord(char) == 13:
                    self.update_history(command)
                    self.channel.send('\r\n')
                    self.run_command(command)

                    position = 0
                    hposition = 0
                    command = ''
                    specials = ''

                ###
                # Escape
                ###
                elif ord(char) == 27:
                    char2 = self.channel.recv(1)

                    ###
                    # [
                    ###
                    if ord(char2) == 91:
                        char3 = self.channel.recv(1)

                        ###
                        # Up Arrow
                        ###
                        if ord(char3) == 65:
                            if len(self.history) + hposition > 0:
                                hposition -= 1
                                command = self.history[hposition]
                                position = len(command)

                        ###
                        # Down Arrow
                        ###
                        elif ord(char3) == 66:
                            if hposition < -1:
                                hposition += 1
                                command = self.history[hposition]
                                position = len(command)

                        ###
                        # Right Arrow
                        ###
                        elif ord(char3) == 67:
                            if position < len(command):
                                specials += self.cursor_right()
                                position += 1
  
                        ###
                        # Left Arrow
                        ###
                        elif ord(char3) == 68:
                            if position > 0:
                                specials += self.cursor_left()
                                position -= 1

                else:
                    command += char.decode()
                    position += 1

                if not self.open:
                    break

                self.channel.send('\r\x1b[K')
                self.prompt()
                self.channel.send(command)
                self.channel.send(specials)

    def cursor_right(self):
        return '\x1b[C'

    def cursor_left(self):
        return '\x1b[D'

    def update_history(self, command):
        if not command:
            return
        if not self.history:
            self.history += [command]
        if command == self.history[-1]:
            return
        self.history += [command]

    def prompt(self):
        self.channel.send('[' + self.who + '@' + self.lhost() + ' ' + self.prompt_path() + ']' + self.prompt_symbol() + ' ')

    def lhost(self):
        l = self.connection.sock.getsockname()[0]
        if l == '127.0.0.1':
            return 'localhost'
        else:
            return l

    def prompt_path(self):
        if self.cwd == self.home:
            return '~'
        else:
            return self.cwd

    def prompt_symbol(self):
        if self.who == 'root':
            return '#'
        else:
            return '$'

    def run_command(self, command):
        if not command:
            return
        parts = command.split()
        if parts[0] == 'exit':
            self.channel.close()
            self.open = False
        else:
            if parts[0] == 'ls':
                Ls(parts[1:], self)
            else:
                self.channel.send('-bash: ' + parts[0] + ': command not found\n')

    def colorize(self, file):
        if file['isdir']:
            return '\x1b[38;5;27m' + file['name'] + '\x1b[0m'
        if file['islnk']:
            return '\x1b[38;5;51m' + file['name'] + '\x1b[0m'
        if file['isfifo']:
            return '\x1b[40;38;5;111m' + file['name'] + '\x1b[0m'
        if file['issock']:
            return '\x1b[38;5;13m' + file['name'] + '\x1b[0m'
        if file['isblk']:
            return '\x1b[48;5;232;38;5;11m' + file['name'] + '\x1b[0m'
        if file['ischr']:
            return '\x1b[48;5;232;38;5;3m' + file['name'] + '\x1b[0m'
        if int(file['mode'], 8) & 2048:
            return '\x1b[48;5;196;38;5;15m' + file['name'] + '\x1b[0m'
        if int(file['mode'], 8) & 1024:
            return '\x1b[48;5;11;38;5;16m' + file['name'] + '\x1b[0m'
        if int(file['mode'], 8) & 512 and int(file['mode'], 8) & 2:
            return '\x1b[48;5;10;38;5;16m' + file['name'] + '\x1b[0m'
        if int(file['mode'], 8) & 2:
            return '\x1b[48;5;10;38;5;21m' + file['name'] + '\x1b[0m'
        if int(file['mode'], 8) & 512:
            return '\x1b[48;5;21;38;5;15m' + file['name'] + '\x1b[0m'
        if int(file['mode'], 8) & 1 or int(file['mode'], 8) & 8 or int(file['mode'], 8) & 64:
            return '\x1b[38;5;34m' + file['name'] + '\x1b[0m'
        if file['name'].endswith('\\.tar') or file['name'].endswith('\\.tgz') or file['name'].endswith('\\.arc') or file['name'].endswith('\\.arj') or file['name'].endswith('\\.taz') or file['name'].endswith('\\.lha') or file['name'].endswith('\\.lz4') or file['name'].endswith('\\.lzh') or file['name'].endswith('\\.lzma') or file['name'].endswith('\\.tlz') or file['name'].endswith('\\.txz') or file['name'].endswith('\\.tzo') or file['name'].endswith('\\.t7z') or file['name'].endswith('\\.zip') or file['name'].endswith('\\.z') or file['name'].endswith('\\.Z') or file['name'].endswith('\\.dz') or file['name'].endswith('\\.gz') or file['name'].endswith('\\.lrz') or file['name'].endswith('\\.lz') or file['name'].endswith('\\.lzo') or file['name'].endswith('\\.xz') or file['name'].endswith('\\.bz2') or file['name'].endswith('\\.bz') or file['name'].endswith('\\.tbz') or file['name'].endswith('\\.tbz2') or file['name'].endswith('\\.tz') or file['name'].endswith('\\.deb') or file['name'].endswith('\\.rpm') or file['name'].endswith('\\.jar') or file['name'].endswith('\\.war') or file['name'].endswith('\\.ear') or file['name'].endswith('\\.sar') or file['name'].endswith('\\.rar') or file['name'].endswith('\\.alz') or file['name'].endswith('\\.ace') or file['name'].endswith('\\.zoo') or file['name'].endswith('\\.cpio') or file['name'].endswith('\\.7z') or file['name'].endswith('\\.rz') or file['name'].endswith('\\.cab'):
            return '\x1b[38;5;9m' + file['name'] + '\x1b[0m'
        if file['name'].endswith('\\.jpg') or file['name'].endswith('\\.jpeg') or file['name'].endswith('\\.gif') or file['name'].endswith('\\.bmp') or file['name'].endswith('\\.pbm') or file['name'].endswith('\\.pgm') or file['name'].endswith('\\.ppm') or file['name'].endswith('\\.tga') or file['name'].endswith('\\.xbm') or file['name'].endswith('\\.xpm') or file['name'].endswith('\\.tif') or file['name'].endswith('\\.tiff') or file['name'].endswith('\\.png') or file['name'].endswith('\\.svg') or file['name'].endswith('\\.svgz') or file['name'].endswith('\\.mng') or file['name'].endswith('\\.pcx') or file['name'].endswith('\\.mov') or file['name'].endswith('\\.mpg') or file['name'].endswith('\\.mpeg') or file['name'].endswith('\\.m2v') or file['name'].endswith('\\.mkv') or file['name'].endswith('\\.webm') or file['name'].endswith('\\.ogm') or file['name'].endswith('\\.mp4') or file['name'].endswith('\\.m4v') or file['name'].endswith('\\.mp4v') or file['name'].endswith('\\.vob') or file['name'].endswith('\\.qt') or file['name'].endswith('\\.nuv') or file['name'].endswith('\\.wmv') or file['name'].endswith('\\.asf') or file['name'].endswith('\\.rm') or file['name'].endswith('\\.rmvb') or file['name'].endswith('\\.flc') or file['name'].endswith('\\.avi') or file['name'].endswith('\\.fli') or file['name'].endswith('\\.flv') or file['name'].endswith('\\.gl') or file['name'].endswith('\\.dl') or file['name'].endswith('\\.xcf') or file['name'].endswith('\\.xwd') or file['name'].endswith('\\.yuv') or file['name'].endswith('\\.cgm') or file['name'].endswith('\\.emf') or file['name'].endswith('\\.axv') or file['name'].endswith('\\.anx') or file['name'].endswith('\\.ogv') or file['name'].endswith('\\.ogx'):
            return '\x1b[38;5;13m' + file['name'] + '\x1b[0m'
        if file['name'].endswith('\\.aac') or file['name'].endswith('\\.au') or file['name'].endswith('\\.flac') or file['name'].endswith('\\.mid') or file['name'].endswith('\\.midi') or file['name'].endswith('\\.mka') or file['name'].endswith('\\.mp3') or file['name'].endswith('\\.mpc') or file['name'].endswith('\\.ogg') or file['name'].endswith('\\.ra') or file['name'].endswith('\\.wav') or file['name'].endswith('\\.axa') or file['name'].endswith('\\.oga') or file['name'].endswith('\\.spx') or file['name'].endswith('\\.xspf'):
            return '\x1b[38;5;45m' + file['name'] + '\x1b[0m'
        return file['name']
