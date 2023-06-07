from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
from os import environ

load_dotenv()


class Database:
    def __init__(self):
        self.client = self.__connect()
        
    def __connect(self):
        try:
            return MongoClient(environ.get('MONGO_URI'))
        except ConnectionFailure:
            raise ConnectionFailure("Could not connect to MongoDB")

    def __enter__(self):
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

