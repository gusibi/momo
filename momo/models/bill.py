#! -*- coding: utf-8 -*-
from datetime import datetime

from momo.models import Model


class Bill(Model):

    '''
    记账
    :param _id: 账单ID
    :param uid: 用户ID
    :param money: 金额 精确到分
    :param tag: 标签
    :param remark: 备注
    :param created_time: 创建时间
    '''

    __collection__ = 'bill'
    __default_fields__ = {
        'created_time': datetime.utcnow()
    }

    def update(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass



class Tag(Model):

    '''
    :param _id: id
    :param name: 标签名
    :param icon: 图标
    :param created_time: 创建时间
    '''

    __collection__ = 'tag'

    __default_fields__ = {
        'created_time': datetime.utcnow()
    }

