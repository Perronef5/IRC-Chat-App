import Util

class User:
    def __init__(self, client_socket, fullname='',username='', nickname=Util.generate_random_nickname(), password='', usertype='user'):
        self._client_socket = client_socket
        self._fullname = fullname
        self._username = username
        self._nickname = nickname
        self._password = password
        self._usertype = usertype
        self._status = "Online"
        self.awaymessage = ""
        self.channels = {}   # Channels that user has connected to from latest to most recent.

    @property
    def socket(self):
        return self._client_socket

    @property
    def fullname(self):
        return self._fullname

    @property
    def username(self):
        return self._username

    @property
    def nickname(self):
        return self._nickname

    @property
    def usertype(self):
        return self._usertype

    @property
    def password(self):
        return self._password

    @property
    def status(self):
        return self._status

    @fullname.setter
    def fullname(self, new_fullname):
        self._fullname = new_fullname

    @username.setter
    def username(self, new_username):
        self._username = new_username

    @nickname.setter
    def nickname(self, new_nickname):
        self._nickname = new_nickname

    @usertype.setter
    def usertype(self, new_usertype):
        self._usertype = new_usertype

    @password.setter
    def password(self, new_password):
        self._password = new_password

    @status.setter
    def status(self, new_status):
        self._status = new_status
