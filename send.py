import os
import pika
import json
import uuid
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_container_sas, ContainerSasPermissions

# Main
def main():
    # JOB ID for tracking
    jobID = str(uuid.uuid4())
    print('job-id: ' + jobID, flush=True)

    # Generate SAS token for container
    sas_url = generateSaSUri(jobID)

    # RabbitMQ connection
    password= os.getenv("password")
    hostname= 'localhost' #os.getenv("hostname")

    credentials= pika.PlainCredentials('user', password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue='sample', durable=True)

    # Set number of messages to send
    for num in range(10):
        task = {
            'job-id': jobID,
            'task-id': num,
            'sas-url': sas_url,
            'wait-seconds': 30
        }
        channel.basic_publish(exchange='', 
                            routing_key='sample',
                            properties=pika.BasicProperties(delivery_mode = pika.spec.PERSISTENT_DELIVERY_MODE),
                            body=json.dumps(task))

    connection.close()


# Generate SAS token for container
def generateSaSUri(jobID):
    try:
        connection_string = os.getenv("STORAGE_CONNECTION")
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.create_container(jobID)

        sas_token = generate_container_sas(
            container_client.account_name,
            container_client.container_name,
            account_key=container_client.credential.account_key,
            permission=ContainerSasPermissions(write=True),
            expiry=datetime.utcnow() + timedelta(hours=2),
            start=datetime.utcnow() - timedelta(minutes=1)
        )

        sas_url=f"{container_client.url}/?{sas_token}"
        #print("SAS URL: " + sas_url, flush=True)
        return sas_url
    
    except Exception as ex:
        print("Exception:")
        print(ex)
        return None

# call main function
if __name__ == "__main__":
    main()