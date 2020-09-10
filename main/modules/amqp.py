import asyncio
import json
import os

import aioamqp

RABBITMQ_HOST = '0.0.0.0'
RABBITMQ_LOGIN = 'rabbitmq'
RABBITMQ_PASSWORD = 'rabbitmq'

if 'DEBUG' in os.environ:
    RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST')
    RABBITMQ_LOGIN = os.environ.get('RABBITMQ_DEFAULT_USER')
    RABBITMQ_PASSWORD = os.environ.get('RABBITMQ_DEFAULT_PASS')



async def send(body, queue):
    transport, protocol = await aioamqp.connect(host=RABBITMQ_HOST,
                                                port=5672,
                                                login=RABBITMQ_LOGIN,
                                                password=RABBITMQ_PASSWORD)
    channel = await protocol.channel()

    if 'DEBUG' in os.environ:
        await channel.queue_declare(queue, durable=True)
    else:
        await channel.queue_declare(queue)
    await channel.basic_publish(json.dumps(body), '', queue)
    await protocol.close()
    transport.close()


loop = asyncio.get_event_loop()
