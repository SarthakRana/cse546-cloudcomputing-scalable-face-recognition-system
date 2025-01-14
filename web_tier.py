import boto3
import json
import time
import uuid
import botocore
import threading
from flask import Flask, request

app = Flask(__name__)

sqs_client = boto3.client('sqs', region_name='us-east-1')
s3_client = boto3.client('s3')
ec2_resource = boto3.resource('ec2', region_name='us-east-1')
ec2_client = boto3.client('ec2', region_name='us-east-1')

REQ_QUEUE_URL = "request-queue-url_here"
RESP_QUEUE_URL = "response-queue-url-here"
IN_BUCKET_NAME = "input-bucket-name-here"

response_dict = {}
max_instance_count = 20
request_hit = 0
apptier_ids = []
lock = threading.Lock()

usr_data_script = """#!/bin/bash
exec > >(tee /var/log/user-data.log) 2>&1
echo "[$(date)] Starting UserData script"

cd /home/ubuntu
echo "[$(date)] Changed to /home/ubuntu directory"

echo "[$(date)] Starting app_tier.py"
sudo chmod -R u+rwx /home/ubuntu
sudo -u ubuntu /usr/bin/python3 /home/ubuntu/app_tier.py &
echo "[$(date)] Started app_tier.py"

echo "[$(date)] UserData script completed"
"""


def sqs_receive_response():
    try:
        while True:
            msg = sqs_client.receive_message(
                QueueUrl = RESP_QUEUE_URL,
                MaxNumberOfMessages = 10
            )

            for message in msg.get("Messages", {}):
                recieved_msg = json.loads(message["Body"])
                response_dict[recieved_msg["uuid"]]={
                    "json":recieved_msg,
                }
                sqs_client.delete_message(QueueUrl = RESP_QUEUE_URL, ReceiptHandle=message['ReceiptHandle'])
    except botocore.exceptions.ClientError as error:
        print("Error Occurred while receiving response from SQS", error)


def count_running_instances():
    response = ec2_resource.describe_instances(
        Filters=[
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }
        ]
    )
    instances = response['Reservations']
    running_count = sum(len(reservation['Instances']) for reservation in instances)
    return running_count-1


def count_messages_in_queue(queue_url):
    response = sqs_client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=['ApproximateNumberOfMessages']
    )
    return int(response['Attributes']['ApproximateNumberOfMessages'])


def scale_out(instance_counts):

    global usr_data_script

    ami_app_tier = "ami-0367c6e4e0812061e"
    instance_id = ec2_resource.create_instances(
        InstanceType="t2.micro",
        MaxCount=1,
        MinCount=1,
        KeyName = "my_key_pair",
        ImageId=ami_app_tier,
        UserData=usr_data_script,
        TagSpecifications=[
        {"ResourceType": "instance", 
         "Tags": [{"Key": "Name", "Value": "app-tier-instance-" + str(instance_counts)},]}
    ]
    )
    print(f"Created app-tier-instance-{instance_counts}")
    apptier_ids.append(instance_id[0].id)


@app.route("/", methods=["POST"])
def handle_request():

    global request_hit
    global s3_client
    global ec2_resource
    global sqs_client
    global RESP_QUEUE_URL
    global REQ_QUEUE_URL
    global IN_BUCKET_NAME
    global max_instance_count
    global response_dict
    global apptier_ids

    try:
        img_name = request.files["inputFile"].filename
        uuid_img = str(uuid.uuid4())
        image_file = request.files["inputFile"]

        msg_body = {
            "file_name" : img_name,
            "uuid": uuid_img
        }

        s3_client.put_object(Bucket=IN_BUCKET_NAME,Key=img_name,Body=image_file)
        sqs_client.send_message(
            QueueUrl = REQ_QUEUE_URL,
            MessageBody = json.dumps(msg_body),
            MessageGroupId = "testGroup"
        )

        with lock:
            request_hit += 1
            if request_hit <= max_instance_count:
                scale_out(request_hit)

        while True:
            if uuid_img in response_dict:
                prediction = response_dict[uuid_img]
                request_hit -= 1
                if request_hit == 0:
                    for app_tier_id in apptier_ids:
                        ec2_client.terminate_instances(InstanceIds=[app_tier_id])
                        time.sleep(0.5)
                    apptier_ids = []
                return prediction["json"]["prediction"], 200
    
    except Exception as e:
        print(f"Exception: {e}")
        return "", 500


sqs_response_thread = threading.Thread(target=sqs_receive_response)
sqs_response_thread.daemon = True
sqs_response_thread.start()

if __name__ == "__main__":
    sqs_response_thread = threading.Thread(target=sqs_receive_response)
    sqs_response_thread.daemon = True
    sqs_response_thread.start()
    app.run(host="0.0.0.0", port=5000)