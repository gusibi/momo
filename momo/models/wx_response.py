#! -*- coding: utf-8 -*-
from datetime import datetime

from momo.models import Model
from momo.models.bill import Bill, Tag
from momo.models.account import Account, AccountWorkflow as AW, UserWorkFlow


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

    def __init__(self, uid, word):
        self.uid = uid
        self.word = word  # key word

    def _get_data(self):
        kw = WXKeyWord.get(word=self.word)
        aw = AW.get(uid=self.uid) or {}
        if not (kw or aw):
            return
        workflow_key = kw.get('data', {}).get('workflow') if kw else None
        if workflow_key == BillWorkFlow.name or aw.get('workflow') == BillWorkFlow.name:
            value = BillWorkFlow(self.uid, self.word, wxkw=kw, aw=aw).get_result()
        elif workflow_key == UserWorkFlow.name or aw.get('workflow') == UserWorkFlow.name:
            value = UserWorkFlow(self.uid, self.word, wxkw=kw, aw=aw).get_result()
        else:
            return
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
                'value': '请选择分类: \n%s\n重新输入金额请输入"修改"',
                'next': 'input_tag',
            },
            'input_tag': {
                'value': '记账完成，可以再次输入"记账"记录下一笔',
            },
            'again': {
                'value': '请重新输入金额',
                'next': 'input_amount',
            },
            'cancel': {
                'value': '已取消记账, 可以重新输入"记账"开始记账。',
                'next': 'clear',
            }
        }
    name = 'keep_accounts'

    def __init__(self, uid, word, wxkw=None, aw=None):
        self.uid = uid
        self.word = word
        self.wxkw = wxkw  # weixin key word instance
        self.aw = aw

    def _get_all_tags(self):
        tags = Tag.find(limit=100)
        tags_name = [t['name'] for t in tags]
        names = '\n'.join(tags_name)
        return names

    def process_active(self):
        account = Account.get(_id=self.uid)
        action = self.actions['active']
        if not account:
            account = Account.insert(_id=self.uid)
            status = 'new_uid'
        else:
            status = 'old_uid'
        return {'next': action[status]['next']}, action[status]['value']

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
        return {'next': action['next']}, action['value']

    def process_input_amount(self):
        action = self.actions['input_amount']
        try:
            amount = float(self.word)
        except (ValueError, TypeError):
            return {'next': 'input_amount'}, '输入的金额不正确，请重新输入'
        data = {
            'uid': self.uid,
            'money': amount
        }
        msg = action['value'] % self._get_all_tags()
        return {'next': action['next'], 'data': data}, msg

    def process_again(self):
        action = self.actions['again']
        aw = AW.get(uid=self.uid)
        if not aw:
            return {}, None
        data = {
            'uid': self.uid,
        }
        return {'next': action['next']}, action['value']

    def process_cancel(self):
        action = self.actions['cancel']
        aw = AW.get(uid=self.uid)
        if not aw:
            return {}, None
        return {'next': action['next']}, action['value']

    def process_input_tag(self):
        action = self.actions['input_tag']
        aw = AW.get(uid=self.uid)
        if not aw:
            return {}, None
        data = aw['data']
        tag = Tag.get(name=self.word)
        if not tag:
            names = self._get_all_tags()
            msg = '暂不允许此分类，分类列表如下: \n%s\n请重新输入' % names
            return {'data': data, 'next': 'input_tag'}, msg
        data['tag'] = self.word
        return {'data': data, 'next': 'done'}, action['value']

    def process_workflow(self, action):
        function_name = 'process_{action}'.format(action=action)
        function = getattr(self, function_name)
        params, value = function()
        params['uid'] = self.uid
        next = params.get('next')
        if next == 'done':
            data = params['data']
            data['created_time'] = datetime.utcnow()
            Bill.insert(**data)
            AW.delete(uid=self.uid)
        elif next == 'clear':
            AW.delete(uid=self.uid)
        else:
            print(params)
            if self.uid:
                params['workflow'] = self.name
                AW.update_or_insert(fields=['uid'], **params)
        return value

    def get_result(self):
        print(self.wxkw)
        if self.wxkw:
            action = self.wxkw['data'].get('action', 'active')
            print('action', action)
            value = self.process_workflow(action)
            return value
        elif self.aw:
            value = self.process_workflow(self.aw['next'])
            return value
        else:
            return
