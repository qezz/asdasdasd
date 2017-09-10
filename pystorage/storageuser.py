"""Public API for storage"""

from pystorage.userinfo import UserInfo
from pystorage.utils import *
from pystorage.errors import NoFile, AuthError

import pymongo
import gridfs

import os

class StorageClient():
    """This class represents a client api to mongo-based storage.

    Allows to:

    * login with username and password
    * switch user with another username and password
    * upload file to storage
    * download file from storage
    * update (overwrite) files
    * delete files
    * list files in particular directory
    * make directories
    * remove directories
    * rename (move) directories
    """

    def _login(self, username, password):
        self.user = UserInfo(username, password)
        self.auth_str = connection_string(self.user, self.server.config)
        self.client = pymongo.MongoClient(self.auth_str,
                                          serverSelectionTimeoutMS=1)

        try:
            self.client.server_info()
        except pymongo.errors.OperationFailure:
            raise AuthError("Wrong username or password.")

        self.db_name = self.user.username + self.server.config["users"]["db_suffix"]

        self.client_gridfs = gridfs.GridFS(self.client[self.server.config["storage_db"]],
                                           collection=self.db_name)
        self.client_gfsbucket = gridfs.GridFSBucket(self.client[self.server.config["storage_db"]],
                                                    bucket_name=self.db_name)

    def __init__(self, username, password, server=None):
        """Creates a new instance of StorageClient.

        Note: `server` is required, for now.

        """

        if server == None:
            raise Exception("Server is not provided")

        self.server = server
        self._login(username, password)


    def switch_user(self, username, password):
        """Switches user to another

        Previous user become logged out

        """

        self.client.close()
        self._login(username, password)

    def upload(self, source, target_filepath, replace=True):
        """Uploads a file from `source` path to `target` inside storage

        If `replace` is false, then `AlreadyExists` exception is
        raised

        """

        target_filepath = normalize_filepath(target_filepath)

        if self.find_file(target_filepath) != None:
            if replace:
                self.remove(target_filepath)
            else:
                raise AlreadyExists("File already exists")

        self.make_dirs(os.path.dirname(target_filepath))

        with open(source, "rb") as source_file:
            file_id = self.client_gfsbucket.upload_from_stream(target_filepath,
                                                               source_file)


    def download_to_file(self, filename, target_path = None):
        """Downloads file from internal storage path (`filename`)
        to local `target_path`.

        Returns a path of downloaded file.

        If `target_path` is not specified, then saves it to
        `localpath` (see configuration for details)

        Raises `NoFile` if there is no file by `filename` path

        """

        f_id = self.find_file(filename)
        if f_id == None:
            raise NoFile("File", str(filename), "not found.")

        if target_path == None:
            target_path = filename

        if os.path.dirname(target_path) != "":
            os.makedirs(os.path.dirname(target_path), exist_ok = True)

        with open(target_path, "wb") as target_file:
            try:
                self.client_gfsbucket.download_to_stream(f_id, target_file)
                return target_path
            except gridfs.errors.NoFile:
                raise NoFile("Error: File", str(filename), "condn't been downloaded.")

    def find_file(self, filepath):
        """Finds file and returns it's `ObjectID`.

        Otherwise, returns `None`.

        """

        if filepath[0] != "/":
            filepath = "/" + filepath
        for item in self.client_gfsbucket.find( {"filename": filepath } ).sort("uploadDate", -1).limit(1):
            return item._id

    def find_dir(self, dirpath):
        """Finds a directory and returns it's `ObjectID`.

        Otherwise, returns `None`.

        """

        _dir = self.find_file(dirpath)

        if _dir != None and self.client_gridfs.get(_dir).metadata == {"is_dir" : True}:
            return _dir
        else:
            return None

    def find_several(self, filepath):
        """Returns an iterator over files have been found."""

        return self.client_gfsbucket.find( {"filename": filepath } )

    def rename(self, filepath, new_filepath):
        """Rename file at `filepath` to `new_filepath`

        If no file was found, raises `NoFile` exception

        """

        f_id = self.find_file(filepath)

        if f_id == None:
            raise NoFile("Error: File", str(filepath), "not found.")

        self.client_gfsbucket.rename(f_id, new_filepath)


    def make_dir(self, dirpath):
        """Create a pseudo directory. Use `make_dirs` to create nested
        directories.

        Raises `AlreadyExists` when directory already presented in storage

        """

        dirpath = normalize_dirpath(dirpath)

        ffile = self.find_file(dirpath)
        if ffile != None:
            meta = self.client_gridfs.get(ffile).metadata # or self.find_file(dirpath + "/"):
            if meta == {"is_dir" : False}:
                raise AlreadyExists("File already exists")
            elif meta == {"is_dir" : True}:
                return ffile

        self.client_gridfs.put(b"", filename = dirpath, metadata = { "is_dir": True })

    def make_dirs(self, dirpath):
        """Similar to make_dir, additionally creates intermediate directories
        as required.

        """

        if dirpath[0] != "/":
            dirpath = "/" + dirpath
        dir_split = dirpath.split("/")

        for level in range(2, 1 + len(dir_split)):
            tmp_dir = "/".join(dir_split[0:level])

            self.make_dir(tmp_dir)


    def remove_dir(self, dirpath, recursively=False):
        """Removes a directory.

        Removes all contents of directory if `recursively=True`
        specified. Otherwise, raises an exception.

        """

        dirpath = normalize_dirpath(dirpath)

        files_to_delete = list(self.find_several({'$regex': "^" + dirpath}))

        if not recursively and len(files_to_delete) > 1:
            raise Exception("Directory is not empty")

        [self.client_gfsbucket.delete(f._id) for f in files_to_delete]

        return files_to_delete

    def move_dir(self, dirpath, target_dirpath):
        """Renames a directory"""

        dirpath = normalize_dirpath(dirpath)
        target_dirpath = normalize_dirpath(target_dirpath)
        files = self.find_several({'$regex': "^" + dirpath})
        for f in files:
            old_filename = self.client_gridfs.get(f._id).filename
            new_filename = old_filename.replace(dirpath, target_dirpath, 1)
            self.client_gfsbucket.rename(f._id, new_filename)

    def list_files(self, dirpath):
        """List all files in provided path"""

        dirpath = normalize_dirpath(dirpath)
        return [file.filename for file in self.find_several({'$regex': "^" + dirpath + "(\w|\d)+/?$"})]

    # TODO: add optional parameter `do_actually_delete', defaults to `True'.
    # If False, then just mark file as deleted
    def remove(self, filepath):
        """Removes a file.

        Raises a `NoFile` exception when attempted to remove a
        non-existing file

        """

        f_id = self.find_file(filepath)

        if f_id == None:
            raise NoFile("Error: File", str(filename), "not found.")

        self.client_gfsbucket.delete(f_id)
