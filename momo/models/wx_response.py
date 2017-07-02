#! -*- coding: utf-8 -*-
from datetime import datetime

from momo.models import Model
from momo.models.bill import Bill, Tag
from momo.models.account import Account, AccountWorkflow as AW


class WXKeyWord(Model):

    '''
    _id: '关键字ID',
    word: '关键字',
    data: {
        'workflow': '工作流',
        'action': '工作流动作',
        'value': '返回值',
        'type': '返回值类型 url|pic|text',
    },
    'created_time': '创建时间',
    '''

    __collection__ = 'wx_keyword'

    def update(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass


class KWResponse:

    def __init__(self, uid, kw):
        self.uid = uid
        self.kw = kw

    def _get_data(self):
        value = BillWorkFlow(self.uid, self.kw).get_result()
        if not value:
            return None
        print(value)
        return value

    def get_response(self):
        value = self._get_data()
        if not value:
            return
        return value


class BillWorkFlow(object):

    actions = {
            'active': {
                'new_uid': {
                    'value': '欢迎使用魔魔记账，你是第一次使用，请设置用户名！',
                    'next': 'input_username',
                },
                'old_uid': {
                    'value': '输入金额',
                    'next': 'input_amount',
                }
            },
            'input_username': {
                'value': '注册成功，忘记用户名可以输入"用户名"查询\n请输入金额',
                'next': 'input_amount',
            },
            'input_amount':{
                'value': '请选择分类: \n',
                'next': 'input_tag',
            },
            'input_tag': {
                'value': '记账完成，可以再次输入"记账"记录下一笔',
            }
        }
    name = 'keep_accounts'

    def __init__(self, uid, kw):
        self.uid = uid
        self.kw = kw

    def _get_all_tags(self):
        tags = Tag.find(limit=100)
        tags_name = [t['name'] for t in tags]
        names = '\n'.join(tags_name)
        return names

    def process_active(self):
        account = Account.get(_id=self.uid)
        action = self.actions['active']
        if not account:
            account = Account.create(_id=self.uid)
            status = 'new_uid'
        else:
            status = 'old_uid'
        return {'next': action[status]['next']}, action[status]['value']

    def process_input_username(self):
        username = self.kw
        account = Account.get(username=username)
        if account:
            return {'next': 'input_username'}, '用户名已被使用，请重新输入'
        Account.update_or_insert(fields=['_id'],
                                 _id=self.uid,
                                 username=username,
                                 created_time=datetime.utcnow())
        action = self.actions['input_username']
        return {'next': action['next']}, action['value']

    def process_input_amount(self):
        action = self.actions['input_amount']
        try:
            amount = float(self.kw)
        except ValueError:
            return {'next': 'input_amount'}, '输入的金额不正确，请重新输入'
        data = {
            'uid': self.uid,
            'money': self.kw
        }
        msg = '%s%s' % (action['value'], self._get_all_tags())
        return {'next': action['next'], 'data': data}, msg

    def process_input_tag(self):
        action = self.actions['input_tag']
        aw = AW.get(_id=self.uid)
        if not aw:
            return {}, None
        data = aw['data']
        tag = Tag.get(name=self.kw)
        if not tag:
            names = self._get_all_tags()
            msg = '暂不允许此分类，分类列表如下: \n%s\n请重新输入' % names
            return {'data': data, 'next': 'input_tag'}, msg
        data['tag'] = self.kw
        return {'data': data, 'next': 'done'}, action['value']

    def process_workflow(self, action):
        function_name = 'process_{action}'.format(action=action)
        function = getattr(self, function_name)
        params, value = function()
        params['_id'] = self.uid
        next = params.get('next')
        if next == 'done':
            data = params['data']
            data['created_time'] = datetime.utcnow()
            Bill.create(**data)
            AW.delete(_id=self.uid)
        else:
            AW.update_or_insert(fields=['_id'], **params)
        return value

    def get_result(self):
        kw = WXKeyWord.get(word=self.kw)
        aw = AW.get(_id=self.uid)
        if kw:
            data = kw['data']
            workflow_key = data.get('workflow')
            if not workflow_key or workflow_key != self.name:
                return data
            action = data.get('action', 'active')
            value = self.process_workflow(action)
            return value
        elif aw:
            value = self.process_workflow(aw['next'])
            return value
        else:
            return
