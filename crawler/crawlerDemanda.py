import json
import requests
import tempfile
import os
import boto3

def lambda_handler(event, context):

    url = "http://44.194.222.41:8080/dadosExternosDemanda/envioDadosExternosDemanda"   

    try:

        resultado = requests.get(url)

        print(resultado)

        # Verifica se a requisição foi bem-sucedida
        resultado.raise_for_status()

        # Decodifica o JSON
        dados = resultado.json()


        # Extrai a lista de Problemas
        demanda = dados

        # Gero o arquivo json
        nome_arquivo = os.path.join(tempfile.gettempdir(), 'demanda.json')

        with open(nome_arquivo, mode='wt') as f:

            json.dump(demanda, f)

            

        # Upload para o s3
        s3 = boto3.client('s3')

        s3 = boto3.client(
        's3',
        aws_access_key_id='',
        aws_secret_access_key='',
        aws_session_token='',
        region_name='us-east-1'
        )
        

        s3.upload_file(

            Filename=nome_arquivo,
            Bucket='infrawatch-bronze',
            Key='demanda.json'

        )

        return demanda

    

    except requests.exceptions.RequestException as e:

        print(f"Erro na requisição: {e}")

        return None



    except json.JSONDecodeError as e:

        print(f"Erro ao decodificar JSON: {e}")

        print(f"Resposta completa da API: {resultado.text}")

        return None

if __name__ == "__main__":
    lambda_handler({}, None)