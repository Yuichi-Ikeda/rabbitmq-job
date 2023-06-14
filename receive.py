import os
import pika
import json
import time
from azure.storage.blob import ContainerClient

password= os.getenv("password")
hostname= os.getenv("hostname")

credentials= pika.PlainCredentials('user', password)
connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, credentials=credentials))
channel = connection.channel()

channel.queue_declare(queue='sample', durable=True)
channel.basic_qos(prefetch_count=1)

def callback(ch, method, properties, body):
    task = json.loads(body)
    print('TASK_START: {}, task-id: {}'.format(task['job-id'], task['task-id']), flush=True)
    
    # Wait for seconds for task simulation
    time.sleep(task['wait-seconds'])

    try:
        container = ContainerClient.from_container_url(task['sas-url'])
        container.upload_blob(name='task-{:06}'.format(task['task-id']), data='Task Starting.', overwrite=True)
    except Exception as ex:
        print("Exception: " + ex)

    # Manual ack
    ch.basic_ack(delivery_tag = method.delivery_tag)
    
    print('TASK_END: {}, task-id: {}'.format(task['job-id'], task['task-id']), flush=True)


channel.basic_consume(queue='sample', auto_ack=False, on_message_callback=callback)

print('Start MQ Consuming', flush=True)
channel.start_consuming()