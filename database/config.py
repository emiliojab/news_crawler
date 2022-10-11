""" This module gets the MongoDB credentials from the .env file.
"""
from abc import abstractmethod
from typing import Tuple
from dotenv import load_dotenv
import os


class Config(object):

    def __init__(self):
        # Load the variables from .env file
        load_dotenv()

    @abstractmethod
    def get_credentials(self):
        """ If in the future another Database is to be used,
            it must have this function to return credentials.
        """
        pass


class MongoDBConfig(Config):

    def __init__(self) -> None:
        super().__init__()
        self.__mongoDB_username = os.getenv("MONGODB_USER")
        self.__mongoDB_pwd = os.getenv("MONGODB_PASSWORD")
        self.__mongoDB_port = os.getenv("MONGODB_PORT")
        self.__mongoDB_host = os.getenv("MONGODB_HOST")

    def get_credentials(self) -> Tuple:
        """ This function returns the credentials to be used in connection.py
        """
        return (self.__mongoDB_username, self.__mongoDB_pwd,
                self.__mongoDB_port, self.__mongoDB_host)
