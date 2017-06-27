#! -*- coding: utf-8 -*-

from pymongo import MongoClient
from momo.settings import Config

pyclient = MongoClient(Config.MONGO_MASTER_URL)


class Model:

    '''
    Model
    '''

    __collection__ = None

    @classmethod
    def _get_db(cls):
        return pyclient['momo_bill']

    @classmethod
    def _get_collection(cls):
        if cls.__collection__:
            db = cls._get_db()
            return db[cls.__collection__]
        raise

    @classmethod
    def get(cls, _id=None, **kwargs):
        collection = cls._get_collection()
        if _id:
            doc = collection.find_one({'_id': _id})
        else:
            doc = collection.find_one(kwargs)
        return doc

    @classmethod
    def query(cls, **kwargs):
        collection = cls._get_collection()
        if not kwargs:
            docs = collection.find()
        else:
            docs = collection.find(kwargs)
        return docs

    @classmethod
    def create(cls, **kwargs):
        collection = cls._get_collection()
        doc = collection.insert_one(kwargs)
        return doc

    @classmethod
    def bulk_inserts(self, *params):
        pass

    def update(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass
