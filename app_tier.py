import boto3
import torch
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
from torchvision import datasets
from torch.utils.data import DataLoader
import json
import time


# face match function to recognise faces in image and return the results
mtcnn = MTCNN(image_size=240, margin=0, min_face_size=20) # initializing mtcnn for face detection
resnet = InceptionResnetV1(pretrained='vggface2').eval() # initializing resnet for face img to embeding conversion

def face_match(img_path, data_path): # img_path= location of photo, data_path= location of data.pt
    img = Image.open(img_path)
    face, prob = mtcnn(img, return_prob=True) # returns cropped face and probability
    emb = resnet(face.unsqueeze(0)).detach() # detech is to make required gradient false

    saved_data = torch.load('/home/ubuntu/data.pt') # loading data.pt file
    embedding_list = saved_data[0] # getting embedding data
    name_list = saved_data[1] # getting list of names
    dist_list = [] # list of matched distances, minimum distance is used to identify the person

    for idx, emb_db in enumerate(embedding_list):
        dist = torch.dist(emb, emb_db).item()
        dist_list.append(dist)

    idx_min = dist_list.index(min(dist_list))
    return (name_list[idx_min], min(dist_list))




"""
defining boto3 objects to access aws services SQS, S3, Ec2 instances......
"""
aws_sqs_client = boto3.client('sqs', region_name = 'us-east-1')
url_req_sqs = "request-queue-url_here"
url_resp_sqs = "response-queue-url-here"
aws_s3_client = boto3.client('s3')
s3_input_bucket = "input-bucket-name-here"
s3_output_bucket = "output-bucket-name-here"


while True:

    #  getting responses from the sqs client...  
    response = aws_sqs_client.receive_message(
        # WaitTimeSeconds=20,
        # VisibilityTimeout=20,
        QueueUrl=url_req_sqs,
        MaxNumberOfMessages=10
    )

    if 'Messages' in response:
        for message in response['Messages']:
            msg_body = json.loads(message['Body'])
            img_name = msg_body["file_name"]
            img_uuid = msg_body["uuid"]
            s3_image_retrieved = aws_s3_client.get_object(Bucket=s3_input_bucket, Key=img_name)
            img = s3_image_retrieved["Body"]

            result = face_match(img, 'data.pt')
            print(f"face math result... : {result}")
            
            out_img_name = img_name.split('.')[0]
            out_data = result[0]
            json_data = json.dumps(out_data)
            print(f"json_data : {json_data}")

            # pushing the output to the s3 bucket 
            aws_s3_client.put_object(
                Bucket=s3_output_bucket,
                Key=out_img_name,
                Body=json_data
            )

            # drafiting the resonse with unique id of the image and the prediction result...
            response_body = {
                "prediction":f"{out_img_name}:{result[0]}",
                "uuid": img_uuid
            }

            # sending the response to the response sqs queue 
            aws_sqs_client.send_message(
                QueueUrl = url_resp_sqs,
                MessageBody = json.dumps(response_body),
                MessageGroupId="testGroup"
            )
            aws_sqs_client.delete_message(QueueUrl=url_req_sqs, ReceiptHandle=message['ReceiptHandle'])
        time.sleep(10)
            
    else:
        print("no msg received....")