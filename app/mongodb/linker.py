import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

def DBClient():
    base_dir = os.getcwd()
    env_path = os.path.join(base_dir, ".env")
    load_dotenv(dotenv_path=env_path)

    uri = os.getenv("uri")
    client = MongoClient(uri, server_api=ServerApi('1'), maxPoolSize=100)
    return client