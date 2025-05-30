import json
import requests
import tempfile
import os
import boto3

def lambda_handler(event, context):

    url = "http://localhost:8080/src/routes/dadosExternos.js"   

    try:

        resultado = requests.get(url)

        # Verifica se a requisição foi bem-sucedida
        resultado.raise_for_status()

        # Decodifica o JSON
        dados = resultado.json()

        # Extrai a lista de Problemas
        problemas = dados['value']

        # Gero o arquivo json
        nome_arquivo = os.path.join(tempfile.gettempdir(), 'dados.json')

        with open(nome_arquivo, mode='wt') as f:

            json.dump(problemas, f)

            

        # Upload para o s3
        s3 = boto3.client('s3')

        s3.upload_file(

            Filename=nome_arquivo,
            Bucket='infrawatch-bronze',
            Key='problemas/dados.json'

        )

        return problemas

    

    except requests.exceptions.RequestException as e:

        print(f"Erro na requisição: {e}")

        return None

    

    except json.JSONDecodeError as e:

        print(f"Erro ao decodificar JSON: {e}")

        print(f"Resposta completa da API: {resultado.text}")

        return None

