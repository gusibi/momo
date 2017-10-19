#! -*- coding: utf-8 -*-
import copy

from six import with_metaclass
from pymongo import MongoClient
from pymongo import ReturnDocument
from momo.settings import Config

pyclient = MongoClient(Config.MONGO_MASTER_URL)


class ModelMetaclass(type):
    """
    Metaclass of the Model.
    """
    __collection__ = None

    def __init__(cls, name, bases, attrs):
        super(ModelMetaclass, cls).__init__(name, bases, attrs)
        cls.db = pyclient['momo_bill']
        if cls.__collection__:
            cls.collection = cls.db[cls.__collection__]


class Model(with_metaclass(ModelMetaclass, object)):

    '''
    Model
    '''

    __collection__ = 'model_base'

    @classmethod
    def get(cls, _id=None, **kwargs):
        if _id:
            doc = cls.collection.find_one({'_id': _id})
        else:
            doc = cls.collection.find_one(kwargs)
        return doc

    @classmethod
    def find(cls, filter=None, projection=None, skip=0, limit=20, **kwargs):
        docs = cls.collection.find(filter=filter,
                                   projection=projection,
                                   skip=skip, limit=limit,
                                   **kwargs)
        return docs

    @classmethod
    def insert(cls, **kwargs):
        doc = cls.collection.insert_one(kwargs)
        return doc

    @classmethod
    def update_or_insert(cls, fields=None, **kwargs):
        '''
        :param fields: list filter fields 
        :param kwargs: update fields
        :return: 
        '''
        if fields:
            filters = {field: kwargs[field] for field in fields if kwargs.get(field)}
            doc = cls.collection.find_one_and_update(
                filters, kwargs, return_document=ReturnDocument.AFTER, upsert=True)
        else:
            doc = cls.collection.insert_one(kwargs)
        return doc


    @classmethod
    def bulk_inserts(cls, *params):
        '''
        :param params: document list
        :return: 
        '''
        results = cls.collection.insert_many(params)
        return results

    @classmethod
    def update_one(cls, filter, **kwargs):
        result = cls.collection.update_one(filter, **kwargs)
        return result

    @classmethod
    def update_many(cls, filter, **kwargs):
        results = cls.collection.update_many(filter, **kwargs)
        return results

    @classmethod
    def delete_one(cls, **filter):
        cls.collection.delete_one(filter)

    @classmethod
    def delete_many(cls, **filter):
        cls.collection.delete_many(filter)
