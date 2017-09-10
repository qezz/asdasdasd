"""Server-side operations"""

from pystorage.storageuser import StorageClient
from pystorage.userinfo import UserInfo
from pystorage.utils import connection_string

from pystorage.errors import *

import pymongo

from urllib.parse import quote_plus


class Server():
    """Represents a "server", allows to perform some basic server
    operations

    """

    def __init__(self, config=None):
        """`config` is required"""
        if config == None:
            raise Exception("Must provide server config")

        try:
            self.host = config["host"]
            self.storage_db = config["storage_db"]
            self.config = config
        except:
            raise ConfigError("Corrupted configuration provided.")

        self.admin = pymongo.MongoClient("mongodb://%s:%s@%s/%s" % (quote_plus("admin"), quote_plus("admin"), "127.0.0.1", "admin"))

    def _privilege_for_db(username, config, db_suffix):
        return {
            "resource" : {
                "db" : config["storage_db"],
                "collection" : (
                    username + config["users"]["db_suffix"] + db_suffix) },
            "actions" : config["users"]["allowed_actions"] }

    def create_role(self, username):
        """Creates a role for provided username.

        See configuration for details

        """

        self.admin[self.config["storage_db"]].command(
            "createRole",
            username + self.config["users"]["role_suffix"],
            privileges = [
                Server._privilege_for_db(username, self.config, db_suffix)
                for db_suffix in [".files", ".chunks"]],
            roles = [])


    def create_user(self, username, password):
        """Creates a user for provided username.

        See configuration for details

        """

        try:
            self.create_role(username)
        except pymongo.errors.DuplicateKeyError:
            raise AlreadyExists
        except:
            raise InvalidResponse("Can't create new role (user).")

        res = self.admin[self.storage_db].add_user(
            username,
            password = password,
            roles = [{
                "role": username + self.config["users"]["role_suffix"],
                "db": self.storage_db }])
        return res

    def sign_up_new_user(self, username, password):
        """Creates a new user for provided username and password.

        Returns new instance if StorageClient
        """

        self.create_user(username, password)
        return StorageClient(username, password, self)

    def drop_user(self, username):
        """Removes user and its role"""

        self.admin[self.storage_db].command("dropUser", username)
        self.admin[self.storage_db].command("dropRole", username
                                            + self.config["users"]["role_suffix"])

    def _user_exists(self, username): # FIXME: Complexity is O(n)
        users = self.admin[self.storage_db].command("usersInfo")['users']
        for user in users:
            if user.get("user") == username:
                return True

        return False
