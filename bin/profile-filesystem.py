#! /usr/bin/python
"""
Python script to stat an entire filesystem and create a pickle 
file with those details.
"""

import sys
import os
import stat
import re
import math
import pickle
import inspect

this_script = os.path.abspath(inspect.getfile(inspect.currentframe()))

root = '/'

filesystem = {}

uids = {
    0   : 'root',
    1   : 'bin',
    2   : 'daemon',
    3   : 'adm',
    4   : 'lp',
    5   : 'sync',
    6   : 'shutdown',
    7   : 'halt',
    8   : 'mail',
    11  : 'operator',
    12  : 'games',
    14  : 'ftp',
    99  : 'nobody',
    192 : 'systemd-network',
    81  : 'dbus',
    999 : 'polkitd',
    74  : 'sshd',
    89  : 'postfix'
}

gids = {
    0   : 'root',
    1   : 'bin',
    2   : 'daemon',
    3   : 'sys',
    4   : 'adm',
    5   : 'tty',
    6   : 'disk',
    7   : 'lp',
    8   : 'mem',
    9   : 'kmem',
    10  : 'wheel',
    11  : 'cdrom',
    12  : 'mail',
    15  : 'man',
    18  : 'dialout',
    19  : 'floppy',
    20  : 'games',
    33  : 'tape',
    39  : 'video',
    50  : 'ftp',
    54  : 'lock',
    63  : 'audio',
    99  : 'nobody',
    100 : 'users',
    22  : 'utmp',
    35  : 'utempter',
    999 : 'input',
    190 : 'systemd-journal',
    192 : 'systemd-network',
    81  : 'dbus',
    998 : 'polkitd',
    997 : 'ssh_keys',
    74  : 'sshd',
    90  : 'postdrop',
    89  : 'postfix'
}

# /proc/41, posix.stat_result(st_mode=16749, st_ino=13277, st_dev=3L, st_nlink=9, st_uid=0, st_gid=0, st_size=0, st_atime=1534698351, st_mtime=1534698351, st_ctime=1534698351)

for path, subdirs, files in os.walk(root, topdown=True):
    for name in ([path] + subdirs + files):
        filename = os.path.join(path, name)

        if filename == this_script:
            pass
        
        try:
            filestats = os.stat(filename)

            filesystem[filename] = {}
            filesystem[filename]['path']  = filename.split('/')
            filesystem[filename]['mode']  = oct(stat.S_IMODE(filestats.st_mode))
            filesystem[filename]['root']  = re.search('(.*)/.*', filename).group(1) or '/'
            filesystem[filename]['name']  = re.search('.*/(.*)', filename).group(1) or '/'
            filesystem[filename]['size']  = filestats.st_size
            filesystem[filename]['nlink'] = filestats.st_nlink
            filesystem[filename]['atime'] = filestats.st_atime
            filesystem[filename]['mtime'] = filestats.st_mtime
            filesystem[filename]['ctime'] = filestats.st_ctime
            filesystem[filename]['uid']   = filestats.st_uid
            filesystem[filename]['user']  = uids[filestats.st_uid]
            filesystem[filename]['gid']   = filestats.st_gid
            filesystem[filename]['group'] = gids[filestats.st_gid]
            filesystem[filename]['blocks'] = int (math.ceil ( float(filestats.st_size) / 512 ))
            filesystem[filename]['isdir'] = stat.S_ISDIR(filestats.st_mode)
            filesystem[filename]['ischr'] = stat.S_ISCHR(filestats.st_mode)
            filesystem[filename]['isblk'] = stat.S_ISBLK(filestats.st_mode)
            filesystem[filename]['isreg'] = stat.S_ISREG(filestats.st_mode)
            filesystem[filename]['isfifo'] = stat.S_ISFIFO(filestats.st_mode)

            if os.path.islink(filename):
                filesystem[filename]['islnk'] = True
                filesystem[filename]['target'] = os.readlink(filename)
            else:
                filesystem[filename]['islnk'] = False
                filesystem[filename]['target'] = ''
                
            filesystem[filename]['issock'] = stat.S_ISSOCK(filestats.st_mode)


        except:
            pass

pickle.dump( filesystem, open( "filesystem.p", 'wb' ))    
