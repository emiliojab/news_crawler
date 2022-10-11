""" This modules connects to MongoDB.
"""
from . import config
from pymongo import MongoClient
from abc import abstractmethod
import urllib


class Connect(object):

    def __init__(self):
        pass

    @abstractmethod
    def connect_to_DB(self):
        """ If in the future another Database is to be used,
            it must have this function for connection.
        """
        pass


class MongoDB(Connect):

    def __init__(self) -> None:
        super().__init__()
        # get the credentials from config.py
        self._conf = config.MongoDBConfig()
        (self.mongoDB_username, self.mongoDB_pwd,
         self.mongoDB_port, self.mongoDB_host) = self._conf.get_credentials()

        # here quote_plus is used because the password or username might have
        # characters in them, which will return an error while connecting to
        # MongoDB with URI
        self.mongoDB_pwd = urllib.parse.quote_plus(self.mongoDB_pwd)
        self.mongoDB_username = urllib.parse.quote_plus(self.mongoDB_username)

    def connect_to_DB(self, **kwargs) -> MongoClient:
        # from .env file, the host/ip address is predefined, here we can
        # overwrite the ip address while calling this function if MongoDB's
        # ip address has changes without the need to change it from the .env
        if kwargs:
            for key, value in kwargs.items():
                self.mongoDB_host = value
        mongo_uri = f'mongodb://{self.mongoDB_username}:{self.mongoDB_pwd }@' \
                    + f'{self.mongoDB_host}:{self.mongoDB_port}/' \
                    + f'compose?authSource=admin&ssl=true'
        return MongoClient(mongo_uri)
