#! /usr/bin/python3

import paramiko
from paramiko.py3compat import b, u, decodebytes
import sys
import time
from commands.ls   import Ls
from commands.cd   import Cd
from commands.exit import Exit

class HoneyshellShell:


    def __init__(self, connection, channel, session, server, process):
        self.who = 'root'
        self.cwd = '/root'
        self.home = '/root'
        self.connection = connection
        self.channel = channel
        self.session = session
        self.process = process
        self.server = server
        self.history = []
        self.session_open = True
        self.last_char_tab = False

        self.command = ''
        self.specials = ''
        self.position = 0
        self.hposition = -1

        while True:
            if not self.session_open: break

            self.failed_login_banner()
            self.last_login_banner()
            self.prompt()

            while True:
                character = self.next_character()
                self.handle_character(character)

                if not self.session_open: break

                self.clear_line()
                self.prompt()
                self.channel.send(self.command)
                self.channel.send(self.specials)

    def last_login_banner(self):

        if self.server.last_login_time:
            self.channel.send('Last login: ')
            self.channel.send( time.strftime('%a %b %d %H:%M:%S %Y', time.localtime(self.server.last_login_time)) )
            self.channel.send(' from ' )
            self.channel.send( self.server.last_login_addr )
            self.channel.send("\r\n")

        self.server.last_login_time = time.time()
        self.server.last_login_addr = self.session.address[0]

    def failed_login_banner(self):
        if self.server.last_failed_time:
            self.channel.send('Last failed login: ')
            self.channel.send( time.strftime('%a %b %d %H:%M:%S %Z %Y', time.localtime(self.server.last_failed_time)) )
            self.channel.send(' from ')
            self.channel.send( self.server.last_failed_addr )
            self.channel.send(' on ssh:notty')
            self.channel.send("\r\n")

            self.channel.send('There ')
            if self.server.num_failed == 1:
                self.channel.send('was ')
            else:
                self.channel.send('were ')
            self.channel.send( str(self.server.num_failed) )
            self.channel.send(' failed login attempts since the last successful login.')
            self.channel.send("\r\n")

            self.server.last_failed_time = 0
            self.server.last_failed_addr = ''
            self.server.num_failed = 0  

    def clear_line(self):
        self.channel.send('\r\x1b[K')

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
            return self.cwd.split('/')[-1] or '/'

    def prompt_symbol(self):
        if self.who == 'root':
            return '#'
        else:
            return '$'

    def run_command(self, command):

        handlers = {
            'exit' : Exit ,
            'ls'   : Ls ,
            'cd'   : Cd 
        }

        if not command:
            return

        parts = command.split()

        if parts[0] in handlers:
            handlers[parts[0]](parts[1:], self)

        else:
            self.channel.send('-bash: ' + parts[0] + ': command not found\n')

        if not command == self.history[-1]:
            self.history.append(command)

    def colorize(self, file, orphan=False, target=False, text=''):
        if file and not text:
            text = file['name']

        if target:
            if not file:
                return '\x1b[05;48;5;232;38;5;15m' + text + '\x1b[0m'

        elif orphan:
            return '\x1b[48;5;232;38;5;9m' + text + '\x1b[0m'

        if not file:
            return text
            
        if file['isdir']:
            return '\x1b[38;5;27m' + text + '\x1b[0m'

        if file['islnk']:
            return '\x1b[38;5;51m' + text + '\x1b[0m'

        if file['isfifo']:
            return '\x1b[40;38;5;111m' + text + '\x1b[0m'

        if file['issock']:
            return '\x1b[38;5;13m' + text + '\x1b[0m'

        if file['isblk']:
            return '\x1b[48;5;232;38;5;11m' + text + '\x1b[0m'

        if file['ischr']:
            return '\x1b[48;5;232;38;5;3m' + text + '\x1b[0m'

        if int(file['mode'], 8) & 2048:
            return '\x1b[48;5;196;38;5;15m' + text + '\x1b[0m'

        if int(file['mode'], 8) & 1024:
            return '\x1b[48;5;11;38;5;16m' + text + '\x1b[0m'

        if int(file['mode'], 8) & 512 and int(file['mode'], 8) & 2:
            return '\x1b[48;5;10;38;5;16m' + text + '\x1b[0m'

        if int(file['mode'], 8) & 2:
            return '\x1b[48;5;10;38;5;21m' + text + '\x1b[0m'

        if int(file['mode'], 8) & 512:
            return '\x1b[48;5;21;38;5;15m' + text + '\x1b[0m'

        if int(file['mode'], 8) & 1 or int(file['mode'], 8) & 8 or int(file['mode'], 8) & 64:
            return '\x1b[38;5;34m' + text + '\x1b[0m'

        if (
            file['name'].endswith('.tar') or
            file['name'].endswith('.tgz') or
            file['name'].endswith('.arc') or
            file['name'].endswith('.arj') or
            file['name'].endswith('.taz') or
            file['name'].endswith('.lha') or
            file['name'].endswith('.lz4') or
            file['name'].endswith('.lzh') or
            file['name'].endswith('.lzma') or
            file['name'].endswith('.tlz') or
            file['name'].endswith('.txz') or
            file['name'].endswith('.tzo') or
            file['name'].endswith('.t7z') or
            file['name'].endswith('.zip') or
            file['name'].endswith('.z') or
            file['name'].endswith('.Z') or
            file['name'].endswith('.dz') or
            file['name'].endswith('.gz') or
            file['name'].endswith('.lrz') or
            file['name'].endswith('.lz') or
            file['name'].endswith('.lzo') or
            file['name'].endswith('.xz') or
            file['name'].endswith('.bz2') or
            file['name'].endswith('.bz') or
            file['name'].endswith('.tbz') or
            file['name'].endswith('.tbz2') or
            file['name'].endswith('.tz') or
            file['name'].endswith('.deb') or
            file['name'].endswith('.rpm') or
            file['name'].endswith('.jar') or
            file['name'].endswith('.war') or
            file['name'].endswith('.ear') or
            file['name'].endswith('.sar') or
            file['name'].endswith('.rar') or
            file['name'].endswith('.alz') or
            file['name'].endswith('.ace') or
            file['name'].endswith('.zoo') or
            file['name'].endswith('.cpio') or
            file['name'].endswith('.7z') or
            file['name'].endswith('.rz') or
            file['name'].endswith('.cab')
        ):
            return '\x1b[38;5;9m' + text + '\x1b[0m'

        if (
            file['name'].endswith('.jpg') or
            file['name'].endswith('.jpeg') or
            file['name'].endswith('.gif') or
            file['name'].endswith('.bmp') or
            file['name'].endswith('.pbm') or
            file['name'].endswith('.pgm') or
            file['name'].endswith('.ppm') or
            file['name'].endswith('.tga') or
            file['name'].endswith('.xbm') or
            file['name'].endswith('.xpm') or
            file['name'].endswith('.tif') or
            file['name'].endswith('.tiff') or
            file['name'].endswith('.png') or
            file['name'].endswith('.svg') or
            file['name'].endswith('.svgz') or
            file['name'].endswith('.mng') or
            file['name'].endswith('.pcx') or
            file['name'].endswith('.mov') or
            file['name'].endswith('.mpg') or
            file['name'].endswith('.mpeg') or
            file['name'].endswith('.m2v') or
            file['name'].endswith('.mkv') or
            file['name'].endswith('.webm') or
            file['name'].endswith('.ogm') or
            file['name'].endswith('.mp4') or
            file['name'].endswith('.m4v') or
            file['name'].endswith('.mp4v') or
            file['name'].endswith('.vob') or
            file['name'].endswith('.qt') or
            file['name'].endswith('.nuv') or
            file['name'].endswith('.wmv') or
            file['name'].endswith('.asf') or
            file['name'].endswith('.rm') or
            file['name'].endswith('.rmvb') or
            file['name'].endswith('.flc') or
            file['name'].endswith('.avi') or
            file['name'].endswith('.fli') or
            file['name'].endswith('.flv') or
            file['name'].endswith('.gl') or
            file['name'].endswith('.dl') or
            file['name'].endswith('.xcf') or
            file['name'].endswith('.xwd') or
            file['name'].endswith('.yuv') or
            file['name'].endswith('.cgm') or
            file['name'].endswith('.emf') or
            file['name'].endswith('.axv') or
            file['name'].endswith('.anx') or
            file['name'].endswith('.ogv') or
            file['name'].endswith('.ogx')
        ):
            return '\x1b[38;5;13m' + text + '\x1b[0m'

        if (
            file['name'].endswith('.aac') or
            file['name'].endswith('.au') or
            file['name'].endswith('.flac') or
            file['name'].endswith('.mid') or
            file['name'].endswith('.midi') or
            file['name'].endswith('.mka') or
            file['name'].endswith('.mp3') or
            file['name'].endswith('.mpc') or
            file['name'].endswith('.ogg') or
            file['name'].endswith('.ra') or
            file['name'].endswith('.wav') or
            file['name'].endswith('.axa') or
            file['name'].endswith('.oga') or
            file['name'].endswith('.spx') or
            file['name'].endswith('.xspf')
        ):
            return '\x1b[38;5;45m' + text + '\x1b[0m'

        return text

    def next_character(self):
        character = self.channel.recv(1)

        if ( hex(character[-1]) == '0x1b' ):
            character += self.channel.recv(1)

            if ( hex(character[-1]) == '0x5b' ):
                character += self.channel.recv(1)

                if ( hex(character[-1]) == '0x33' ):
                    character += self.channel.recv(1)
        return character

    def handle_ctrl_c(self):
        self.channel.send('^C\r\n')

        self.position = 0
        self.hposition = 0
        self.command = ''
        self.specials = ''

    def handle_ctrl_a(self):
        self.specials = self.cursor_left() * len(self.command)
        self.position = 0

    def handle_ctrl_e(self):
        self.specials = ''
        self.position = len(self.command)

    def handle_backspace(self):            
        if self.position > 0:
            command  = self.command
            position = self.position

            self.command = command[:position - 1] + command[position:]
            self.position -= 1

    def handle_return(self):
        self.update_history(self.command)
        self.channel.send('\r\n')
        self.run_command(self.command)

        self.position = 0
        self.hposition = 0
        self.command = ''
        self.specials = ''

    def handle_up_arrow(self):
        if len(self.history) + self.hposition > 0:
            self.hposition -= 1
            self.command = self.history[self.hposition]
            self.position = len(self.command)

    def handle_down_arrow(self):
        if self.hposition < -1:
            self.hposition += 1
            self.command = self.history[self.hposition]
            self.position = len(self.command)

    def handle_right_arrow(self):
        if self.position < len(self.command):
            self.specials += self.cursor_right()
            self.position += 1
  
    def handle_left_arrow(self):
        if self.position > 0:
            self.specials += self.cursor_left()
            self.position -= 1

    def handle_delete(self):
        if self.position < len(self.command):
            command  = self.command
            position = self.position

            self.command = command[:position] + command[position+1:]
            self.specials += self.cursor_right()

    def handle_tab(self):
        fs = self.server.filesystem

        # Need to find the word the cursor is on...
        string_start = self.command.rfind(' ', 0, self.position) + 1
        string = self.command[string_start: self.position]

        # If there are any / that means we're actually looking in a subdirectory
        object_start = string.rfind('/') + 1
        rel_path = string[ :object_start ]
        rel_obj  = string[object_start: ]

        search_path = self.normalize_path(rel_path)

        if string_start == 0:
            # TODO: This means we're looking for a command
            #       somewhere in the PATH
            pass

        else:
            all_files = [ fs[filename] for filename in fs if fs[filename]['root'] == search_path ]
            matching_files = list(filter(lambda file: file['name'].startswith(rel_obj), all_files))

            # If no matches, just move on
            if not matching_files:
                pass

            #If there is exactly one match, just fill it in
            elif len(matching_files) == 1:
                command  = self.command[:string_start + object_start] 
                command += matching_files[0]['name']
                if matching_files[0]['isdir']:
                    command += '/'
                command += self.command[self.position:]

                self.position += len(command) - len(self.command)
                self.command = command    

            # TODO: More than one match. Repeated tab
            elif self.last_char_tab:
                pass

            # More than one match.  First tab.
            else:
                self.last_char_tab = True;
                

    def handle_character(self, character):

        handlers = {
            b'\x7f'    : self.handle_backspace ,
            b'\x01'    : self.handle_ctrl_a ,
            b'\x03'    : self.handle_ctrl_c ,
            b'\x05'    : self.handle_ctrl_e ,
            b'\r'      : self.handle_return ,
            b'\t'      : self.handle_tab,
            b'\x1b[A'  : self.handle_up_arrow ,
            b'\x10'    : self.handle_up_arrow ,
            b'\x1b[B'  : self.handle_down_arrow ,
            b'\x0e'    : self.handle_down_arrow ,
            b'\x1b[C'  : self.handle_right_arrow ,
            b'\x06'    : self.handle_right_arrow ,
            b'\x1b[D'  : self.handle_left_arrow ,
            b'\x02'    : self.handle_left_arrow ,
            b'\x1b[3~' : self.handle_delete
        }

        if character in handlers:
            handlers[character]()

        else:
            command = self.command[:self.position] + character.decode() + self.command[self.position:]
            self.command = command
            self.position += 1

    def normalize_path(self, path):
        fs = self.server.filesystem
                
        if not path.startswith('/') and not path.startswith('~'):
            path = (self.cwd + '/' + path).rstrip('/')

        path_parts = path.split('/')
        new_path_parts = [] 
        for part in path_parts:
            if part == '.':
                pass
            elif part == '..':
                new_path_parts = new_path_parts[:-1]
            elif part == '~':
                cwd_parts = self.cwd.split('/')
                for cwd_part in cwd_parts:
                    if not cwd_part:
                        pass
                    else:
                        new_path_parts.append(cwd_part) 
            elif not part:
                pass
            else:
                new_path_parts.append(part)

        return '/' + '/'.join(new_path_parts)
