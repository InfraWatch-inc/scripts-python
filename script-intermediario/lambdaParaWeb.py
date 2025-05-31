import boto3
import pandas as pd
import requests
import io

NODE_API_URL = ''

s3 = boto3.client('s3')

def lambda_handler(event, context):
    bucket = event['Records'][0]['bucket']['name']
    arquivo = event['Records'][0]['s3']['object']['key']

    obj = s3.get_object(bucket=bucket, key=arquivo)
    cont = obj['body'].read()

    resposta = requests.post(NODE_API_URL, data=cont)

    