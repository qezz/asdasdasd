"""Simple wrapper for user info"""

class UserInfo():

    def __init__(self, username, password):
        self.username = username
        self.password = password # TODO: add salt and hashing

    @property
    def username(self):
        "Getter for username"
        return self.__username

    @username.setter
    def username(self, username):
        "Setter for username"
        self.__username = username

    @property
    def password(self):
        "Getter for password"
        return self.__password

    @password.setter
    def password(self, password):
        "Setter for password"
        self.__password = password
