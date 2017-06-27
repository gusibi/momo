#! -*- coding: utf-8 -*-

from momo.models import Model


class WXKeyWord(Model):

    '''
    _id: '关键字ID',
    word: '关键字',
    data: {
        'workflow': '工作流',
        'step': '工作流第几步',
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
        self.kw = kw.encode('utf-8')
        self.kw = kw

    def _get_data(self):
        kw = WXKeyWord.get(word=self.kw)
        if not kw:
            return None
        return kw.get('data', {})

    def get_response(self):
        data = self._get_data()
        if not data:
            return
        return data['value']
