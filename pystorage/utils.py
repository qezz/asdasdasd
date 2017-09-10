"""Simple utils for PyStorage"""

from urllib.parse import quote_plus

def connection_string(userinfo, config):
    """Mongo connection string for client"""

    return ("mongodb://%s:%s@%s/%s" % (quote_plus(userinfo.username),
                                       quote_plus(userinfo.password),
                                       config["host"],
                                       config["storage_db"])).format()

def normalize_dirpath(dirpath):
    """Adds '/' at the beginning and at the end of dirpath string if
    needed

    """

    if dirpath[0] != "/":
        dirpath = "/" + dirpath

    if dirpath[-1] != "/":
        dirpath = dirpath + "/"

    return dirpath

def normalize_filepath(filepath):
    """Adds '/' at the beginning of the filepath if needed"""

    if filepath[0] != "/":
        filepath = "/" + filepath

    return filepath
