import unittest
import pystorage

from pystorage import StorageClient, Server
from pystorage.errors import AuthError

from test.utils import from_json_file

class TestStorageClientConstruct(unittest.TestCase):
    """Test basic actions with StorageClient"""

    username = "test_user"
    password = "test_password"

    def setUp(self):
        self.config = from_json_file("test/config_example.json")
        self.server = Server(self.config)
        self.server.sign_up_new_user(self.username, self.password)

    def tearDown(self):
        self.server.drop_user(self.username)

    @classmethod
    def tearDownClass(cls):
        server = Server(from_json_file("test/config_example.json"))
        if server._user_exists(cls.username):
            server.drop_user(cls.username)


    def test_connect_with_config(self):
        # StorageClient(username, password)
        client = StorageClient(self.username, self.password, Server(self.config))

    def test_connect_wo_config(self):
        # StorageClient(username, password)
        self.assertRaises(Exception, StorageClient.__init__,
                          self.username, self.password)


class TestNewClient(unittest.TestCase):

    username = "test_user"
    password = "test_password"

    def setUp(self):
        self.config = from_json_file("test/config_example.json")
        self.server = Server(self.config)

    @classmethod
    def tearDownClass(cls):
        server = Server(from_json_file("test/config_example.json"))
        if server._user_exists(cls.username):
            server.drop_user(cls.username)

    def test_create_new_client(self):
        server = Server(self.config)
        # storage_client = StorageClient(self.username, self.password, server = server)
        new_user = server.sign_up_new_user(self.username, self.password)
        self.assertTrue(server._user_exists(self.username))

        server.drop_user(new_user.user.username)
        self.assertFalse(server._user_exists(self.username))

class TestDropUser(unittest.TestCase):
    """Drop (remove) user by server"""

    username = "test_user"
    password = "test_password"

    def setUp(self):
        self.server = Server(from_json_file("test/config_example.json"))
        self.new_user = self.server.sign_up_new_user(self.username, self.password)

    def test_drop_user(self):
        self.server.drop_user(self.username)
        self.assertFalse(self.server._user_exists(self.username))



class TestOperationsOnEmpty(unittest.TestCase):
    """Test for operations on (almost) empty storage"""

    username = "test_user"
    password = "test_password"

    some_text = b"Hello World"

    def setUp(self):
        config = from_json_file("test/config_example.json")
        self.server = Server(config)
        self.client = self.server.sign_up_new_user(self.username, self.password)

    def tearDown(self):
        self.client.remove_dir("/", recursively=True)
        self.server.drop_user(self.username)

    @classmethod
    def tearDownClass(cls):
        server = Server(from_json_file("test/config_example.json"))
        if server._user_exists(cls.username):
            server.drop_user(cls.username)


    def test_upload_file(self):
        tmp_filepath = "/tmp/py_test_file"
        with open(tmp_filepath, "wb") as f:
            f.write(self.some_text)

        self.client.upload(tmp_filepath, "my_new_file.txt")

        self.assertNotEqual(None, self.client.find_file("/my_new_file.txt"))

    def test_create_dirs(self):
        self.client.make_dirs("path/to/nested/dir")
        self.assertNotEqual(None, self.client.find_dir("/path/to/nested/dir/"))


class TestOperationsOverFiles(unittest.TestCase):
    """Test operations with some files stored in storage"""

    username = "test_user"
    password = "test_password"

    some_text = b"Hello World"

    def setUp(self):
        config = from_json_file("test/config_example.json")
        self.server = Server(config)
        self.client = self.server.sign_up_new_user(self.username, self.password)

        self.client.make_dirs("path/to/nested/dir")

        tmp_filepath = "/tmp/py_test_file"
        with open(tmp_filepath, "wb") as f:
            f.write(self.some_text)

        self.files = ["/path/to/nested/dir/file1",
                      "/path/to/nested/dir/file2",
                      "/path/to/nested/dir/file3"]

        for filepath in self.files:
            self.client.upload(tmp_filepath, filepath)

    def tearDown(self):
        self.client.remove_dir("/", recursively=True)
        self.server.drop_user(self.username)

    @classmethod
    def tearDownClass(cls):
        server = Server(from_json_file("test/config_example.json"))
        if server._user_exists(cls.username):
            server.drop_user(cls.username)

    def test_list_single_dir(self):
        self.assertEqual(["/path/to/nested/dir/"],
                         self.client.list_files("/path/to/nested/"))

    def test_list_multiple_files(self):
        self.assertEqual(self.files,
                         self.client.list_files("/path/to/nested/dir"))

    def test_remove_dir_recursively(self):
        self.client.remove_dir("path/to/nested/dir", recursively=True)

        self.assertEqual(None, self.client.find_dir("/path/to/nested/dir/"))
        self.assertNotEqual(None, self.client.find_dir("/path/to/nested/"))

        self.assertEqual([], self.client.list_files("/path/to/nested/"))

    def test_remove_dir(self):
        self.assertRaises(Exception, self.client.remove_dir, "path/to/nested/dir",
                          recursively = False)

    def test_move_dir(self):
        self.client.move_dir("/path/to/nested/", "another_dir")
        self.assertEqual(["/another_dir/dir/file1",
                          "/another_dir/dir/file2",
                          "/another_dir/dir/file3"],
                         self.client.list_files("/another_dir/dir"))

    def test_download_file(self):
        saved = self.client.download_to_file("path/to/nested/dir/file1", "/tmp/test_file_local.txt")

        with open(saved, "rb") as f:
            res = f.read()

        self.assertEqual(res, self.some_text)

class TestSwitchUser(unittest.TestCase):
    """Dedicated testcase for switching user"""

    username = "test_user"
    password = "test_password"


    username_b = "another_user"
    password_b = "another_password"

    some_text = b"Hello World"

    def setUp(self):
        config = from_json_file("test/config_example.json")
        self.server = Server(config)
        self.client = self.server.sign_up_new_user(self.username, self.password)
        self.server.sign_up_new_user(self.username_b, self.password_b)

    def tearDown(self):
        self.server.drop_user(self.username)
        self.server.drop_user(self.username_b)


    @classmethod
    def tearDownClass(cls):
        server = Server(from_json_file("test/config_example.json"))
        if server._user_exists(cls.username):
            server.drop_user(cls.username)

        if server._user_exists(cls.username_b):
            server.drop_user(cls.username_b)



    def test_switch_user(self):

        self.assertEqual(self.username, self.client.user.username)
        self.assertEqual(self.password, self.client.user.password)

        self.client.switch_user(self.username_b, self.password_b)

        self.assertEqual(self.username_b, self.client.user.username)
        self.assertEqual(self.password_b, self.client.user.password)

    def test_switch_user_error(self):
        self.assertRaises(AuthError, self.client.switch_user,
                          "random", "pass")

if __name__ == "__main__":
    unittest.main()
