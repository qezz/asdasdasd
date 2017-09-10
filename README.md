# PyStorage

## Requirements ##

### 1. Python 3.6
### 2. mongod version 3.2 and higher

``` bash
brew install mongod
brew install mongodb
```

### 3. pymongo & gridfs

``` bash
pip3 install pymongo
pip3 install gridfs
```


### 4. Enable auth users in mongo

See documentation: https://docs.mongodb.com/manual/tutorial/enable-authentication/#overview

> Note: You must use `mongo --auth` to prevent unexpected things

## Usage

Usage is pretty simple see docs for api, and test for small examples

Basic usage is

``` python
config = from_json_file("test/config_example.json")
server = Server(self.config)
user = server.sign_up_new_user(self.username, self.password)

# do things with `user`
```


## License

There is no license, see [explanation](https://choosealicense.com/no-license/) for details.

In a short hand, you can't use this code without my direct permission.

## Author

Sergey Mishin, sergei.a.mishin@gmail.com
