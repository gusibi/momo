import sys
from time import sleep

from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer

import requests

API_URL = "http://www.tuling123.com/openapi/api"
API_KEY0 = ""  # 机器人1 的key
API_KEY1 = ""  # 机器人2 的key

momo = ChatBot(
    'Momo',
    storage_adapter='chatterbot.storage.MongoDatabaseAdapter',
    logic_adapters=[
            "chatterbot.logic.BestMatch",
            "chatterbot.logic.MathematicalEvaluation",
            "chatterbot.logic.TimeLogicAdapter",
        ],
    input_adapter='chatterbot.input.VariableInputTypeAdapter',
    output_adapter='chatterbot.output.OutputAdapter',
    database='chatterbot',
    read_only=True
)


def ask(question, key, name):
    params = {
        "key": key,
        "userid": name,
        "info": question,
    }
    res = requests.post(API_URL, json=params)
    result = res.json()
    answer = result.get('text')
    return answer


def A(bsay):
    print('B:', bsay)
    answer = ask(bsay, API_KEY0, 'momo123')
    print('A:', answer)
    return answer


def B(asay):
    print('A:', asay)
    answer = ask(asay, API_KEY1, 'momo456')
    print('B', answer)
    return answer


def tariner(asay):
    momo.set_trainer(ListTrainer)
    while True:
        conv = []
        conv.append(asay)
        bsay = B(asay)
        conv.append(bsay)
        momo.train(conv)
        print(conv)
        conv = []
        conv.append(bsay)
        asay = A(bsay)
        conv.append(asay)
        momo.train(conv)
        print(conv)
        sleep(5)  # 控制频率


def main(asay):
    tariner(asay)


if __name__ == '__main__':
    main(*sys.argv[1:])
