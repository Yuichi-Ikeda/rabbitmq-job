import os
import pika
import json
import time
from datetime import datetime
from azure.storage.blob import ContainerClient

password= os.getenv("password")
hostname= os.getenv("hostname")

credentials= pika.PlainCredentials('user', password)
connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, credentials=credentials, heartbeat=0))
channel = connection.channel()

# get queue item
method_frame, header_frame, body = channel.basic_get(queue='sample', auto_ack=False)
delivery_tag = method_frame.delivery_tag

task = json.loads(body)
print('TASK_START: {}, job-id: {}, task-id: {}'.format(str(datetime.now()), task['job-id'], task['task-id']), flush=True)

# Wait for seconds for task simulation
time.sleep(task['wait-seconds'])

# Upload task result to blob storage
try:
    container = ContainerClient.from_container_url(task['sas-url'])
    container.upload_blob(name='task-{:06}'.format(task['task-id']), data='Task Starting.', overwrite=True)
except Exception as ex:
    print("Exception: " + ex)

# Manual ack
channel.basic_ack(delivery_tag=delivery_tag)

print('TASK_END: {}, job-id: {}, task-id: {}'.format(str(datetime.now()), task['job-id'], task['task-id']), flush=True)

if connection is not None:
    connection.close()