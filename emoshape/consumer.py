import asyncio
import datetime
import json
import os
import time
from threading import Thread

import aioamqp
from emoshape import Emoshape
from symbl import SymblAI
from recognize import recognize
from config.config import *
import redis

from collections import Counter

def get3Emotion(listEmotion):
    maxEmotions = []
    maxEmotionsList = []
    for _ in range(3):
        m = max(listEmotion, key=listEmotion.get)
        emotion = m.replace('channel', '')
        if emotion == 'SAD': # печальный
            maxEmotions.append('&#128532;')
            maxEmotionsList.append(m.replace('channel', ''))
        elif emotion == 'FEAR': # страх
            maxEmotions.append('&#128552;')
            maxEmotionsList.append(m.replace('channel', ''))
        elif emotion == 'DISGUST': # отвращение
            maxEmotions.append('&#128534;')
            maxEmotionsList.append(m.replace('channel', ''))
        elif emotion == 'ANGER': # Гнев
            maxEmotions.append('&#128545;')
            maxEmotionsList.append(m.replace('channel', ''))
        elif emotion == 'DESIRE': # Желать
            maxEmotions.append('&#128523;')
            maxEmotionsList.append(m.replace('channel', ''))
        elif emotion == 'SURPRISE': # Сюрприз
            maxEmotions.append('&#128588;')
            maxEmotionsList.append(m.replace('channel', ''))
        elif emotion == 'INATTENTION': # невнимательный
            maxEmotions.append('&#128528;')
            maxEmotionsList.append(m.replace('channel', ''))
        elif emotion == 'EXCITED': # Возбужденный
            maxEmotions.append('&#128525;')
            maxEmotionsList.append(m.replace('channel', ''))
        elif emotion == 'CONFIDENT': # уверенный
            maxEmotions.append('&#128526;')
            maxEmotionsList.append(m.replace('channel', ''))
        elif emotion == 'HAPPY': # Счастливый
            maxEmotions.append('&#128519;')
            maxEmotionsList.append(m.replace('channel', ''))
        elif emotion == 'TRUST': # Доверительный
            maxEmotions.append('&#128527;')
            maxEmotionsList.append(m.replace('channel', ''))
        listEmotion.pop(m)

    return maxEmotions, maxEmotionsList


def checkEmotion(listEmotion):
    bad = listEmotion['channelFEAR'] + listEmotion['channelSAD'] + listEmotion['channelDISGUST'] + listEmotion['channelANGER']
    netral = listEmotion['channelDESIRE'] + listEmotion['channelSURPRISE'] + listEmotion['channelINATTENTION']
    good = listEmotion['channelEXCITED'] + listEmotion['channelCONFIDENT'] + listEmotion['channelHAPPY'] + listEmotion['channelTRUST']

    em = {
        '-1': bad,
        '0': netral,
        '1': good,
    }

    maxEmotions, maxEmotionsList = get3Emotion(listEmotion)
    return max(em, key=lambda k: em[k]), maxEmotions, maxEmotionsList

def main(body):
    request = json.loads(body)
    if 'DEBUG' in os.environ:
        r = redis.Redis(host='redis')
    else:
        r = redis.Redis()

    em = Emoshape(host=EMOSHAPE_HOST, port=2424, secret=EMOSHAPE_SECRET)

    # В зависимости от того что пришло отдаем в Emoshape
    if 'text' in request:
        text = request['text']
        em.sendMessage(text)
        if text == ' ' or text == '':
            r.set(request['csrftoken'], json.dumps({'errorMessage': 'No text found!'}))
            return
    elif 'file' in request:
        text = recognize(storage_uri=request['file'])
        em.sendMessage(text)
        if text == ' ' or text == '':
            r.set(request['csrftoken'], json.dumps({'errorMessage': 'No text found!'}))
            return
            # em.tone_on('/home/vladislav/Музыка/1.mp3', '/home/vladislav/virtmic')
    else:
        return

    # Получаем выходные данные от Emoshape
    time.sleep(3)
    timeshtamp = datetime.datetime.now()
    emotionIndex, maxEmotions, maxEmotionsList  = checkEmotion(em.getChannels())
    print(f" LOG: {timeshtamp} - [{request['csrftoken']}] [{text}] = " + emotionIndex + ' --- ' + str(maxEmotionsList))
    em.closeConnection()

    # Получаем выходные данные от Symbl AI
    s = SymblAI(message=text)
    res = s.getTopics()
    topics = []
    for item in res['topics']:
        print(item['text'])
        topics.append(item['text'])

    print(f" LOG: {timeshtamp} - [{request['csrftoken']}] [topics] = " + str(topics))

    # Сохраняем выходные данные в redis подписывая токеном пользователя
    r.set(request['csrftoken'], json.dumps({'emotionIndex': int(emotionIndex), 'maxEmotions': ' '.join(maxEmotions), 'maxEmotionsList': ', '.join(maxEmotionsList), 'symblTopics': ', '.join(topics)}))


if __name__ == '__main__':
    class Queue:
        def __init__(self, epuID):
            self.epuID = epuID

        async def callback(self, channel, body, envelope, properties):
            task = Thread(target=main, args=(body,))
            task.start()

            # сделать ожидающую функцию для создание опр. кол-ва воркеров
            # потому что будет определенное кол-во пользователей
            await asyncio.sleep(15)


            # Удаляет сообщение после прочтения
            await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)

        async def worker(self):
            try:
                if 'DEBUG' in os.environ:
                    await asyncio.sleep(25)
                transport, protocol = await aioamqp.connect(host=RABBITMQ_HOST,
                                                            port=5672,
                                                            login=RABBITMQ_LOGIN,
                                                            password=RABBITMQ_PASSWORD)
                channel = await protocol.channel()
            except aioamqp.AmqpClosedConnection:
                print("{ -- Closed connections -- }")
                return


            if 'DEBUG' in os.environ:
                await channel.queue_declare('emoshape', durable=True)
            else:
                await channel.queue_declare('emoshape')

            await channel.basic_qos(prefetch_count=4, prefetch_size=0, connection_global=False)
            await channel.basic_consume(self.callback, queue_name='emoshape')


    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(Queue(0).worker()) #for i in range(2)
    ]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.run_forever()
