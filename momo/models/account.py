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
    _id: id
    uid: uid
    workflow: workflow name
    next: workflow next
    '''

    __default_fields__ = {
        'created_time': datetime.utcnow()
    }



class UserWorkFlow(object):

    name = 'user_setting'

    actions = {
        'name_query': {
            'new_uid': {
                'value': '竟然没有设置用户名，来设置一下！输入"就不"取消设置！',
                'next': 'input_username',
            },
            'old_uid': {
                'value': '您的用户名为：%s',
                'next': 'done'
            }
        },
        'input_username': {
            'value': '设置成功，您的用户名为：%s，忘记用户名可以输入"用户名"查询',
            'next': 'done'
        },
        'give_up': {
            'value': '好吧你说了算！',
            'next': 'give_up'
        }
    }

    def __init__(self, uid, word, wxkw=None, aw=None):
        self.uid = uid
        self.word = word
        self.wxkw = wxkw  # weixin key word instance
        self.aw = aw

    def process_name_query(self):
        account = Account.get(_id=self.uid) or {}
        username = account.get('username')
        action = self.actions['name_query']
        if not account or not username:
            status = 'new_uid'
            value = action[status]['value']
        else:
            status = 'old_uid'
            value = action[status]['value'] % username
        return {'next': action[status]['next']}, value

    def process_input_username(self):
        username = self.word
        account = Account.get(username=username)
        if account:
            return {'next': 'input_username'}, '用户名已被使用，请重新输入'
        Account.update_or_insert(fields=['_id'],
                                 _id=self.uid,
                                 username=username,
                                 created_time=datetime.utcnow())
        action = self.actions['input_username']
        value = action['value'] % username
        return {'next': action['next']}, value

    def process_give_up(self):
        action = self.actions['give_up']
        aw = AccountWorkflow.get(uid=self.uid)
        if not aw:
            return {}, None
        return {'next': action['next']}, action['value']

    def process_workflow(self, action):
        function_name = 'process_{action}'.format(action=action)
        function = getattr(self, function_name)
        params, value = function()
        params['uid'] = self.uid
        next = params.get('next')
        if next in ['done', 'give_up']:
            AccountWorkflow.delete(uid=self.uid)
        else:
            print(params)
            if self.uid:
                params['workflow'] = self.name
                AccountWorkflow.update_or_insert(fields=['uid'], **params)
        return value

    def get_result(self):
        if self.wxkw:
            action = self.wxkw['data'].get('action', 'name_query')
            value = self.process_workflow(action)
            return value
        elif self.aw:
            value = self.process_workflow(self.aw['next'])
            return value
        else:
            return