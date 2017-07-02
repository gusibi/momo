#! -*- coding: utf-8 -*-
from datetime import datetime

from momo.models import Model


class Account(Model):

    '''
    :param _id: '用户ID',
    :param nickname: '用户昵称',
    :param username: '用户名 用于登录',
    :param avatar: '头像',
    :param password: '密码',
    :param created_time: '创建时间',
    '''
    __collection__ = 'account'
    __default_fields__ = {
        'created_time': datetime.utcnow()
    }


class AccountWorkflow(Model):

    __collection__ = 'account_workflow'

    '''
    _id: uid
    next: workflow next
    '''

    __default_fields__ = {
        'created_time': datetime.utcnow()
    }

