import threading
import paramiko
import time
import textwrap

class HoneyshellProcess:

    def __init__(self, session):
        self.session = session
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if username == 'root' and password == 'root':
            return paramiko.AUTH_SUCCESSFUL

        self.session.server.num_failed += 1
        self.session.server.last_failed_time = time.time()
        self.session.server.last_failed_addr = self.session.address[0]
        time.sleep(2)
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        return paramiko.AUTH_FAILED

    def check_channel_env_request(self, channel, name, value):
        return False

    def check_auth_none(self, username):
        return paramiko.AUTH_FAILED

    def check_auth_gssapi_with_mic(self):
        return paramiko.AUTH_FAILED

    def check_auth_gssapi_keyex(self):
        return paramiko.AUTH_FAILED

    def enable_auth_gssapi(self):
        return True

    def get_banner(self):
        banner = textwrap.dedent("""\
            Welcome to this wonderful SSH server.

            Have a good time!
            """)
        language = 'en-US'
        return (banner, language)

    def get_allowed_auths(self, username):
        return 'password'

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        self.width = width
        self.height = height
        return True

    def check_channel_window_change_request(self, channel, width, height, pixelwidth, pixelheight):
        self.width = width
        self.height = height
        return True
