import json
import requests
import tempfile
import os
import boto3

def lambda_handler(event, context):

    url = "http://44.217.192.92:8080/dadosExternos/envioDadosExternos"   

    try:

        resultado = requests.get(url)

        print(resultado)

        # Verifica se a requisição foi bem-sucedida
        resultado.raise_for_status()

        # Decodifica o JSON
        dados = resultado.json()


        # Extrai a lista de Problemas
        problemas = dados

        # Gero o arquivo json
        nome_arquivo = os.path.join(tempfile.gettempdir(), 'problemas.json')

        with open(nome_arquivo, mode='wt') as f:

            json.dump(problemas, f)

            

        # Upload para o s3
        s3 = boto3.client('s3')

        s3 = boto3.client(
        's3',
        aws_access_key_id='ASIATGYMGOFGNAC6SHOT',
        aws_secret_access_key='JXYga54RRvJB0KhAYIRl9p96GQevoVuem5F6PS9',
        aws_session_token='IQoJb3JpZ2luX2VjEP3//////////wEaCXVzLXdlc3QtMiJHMEUCICy0ZZv9nklxcmO106BvcpDlpaNEzdn93v1fIq/XKnBdAiEAgEjYBeceIbJhtAXoFM620BLElsq+sd9gRY4YMxoKEboqwAIIxv//////////ARABGgwyMjA2Nzk1MzI4NzYiDFy98d90THVqqhkJmiqUAt/+HHt2t5PTPuGxXDQXWVZoCKzT5QQpRlkHY1dWCQQKAWRfHIKYlQ0SB6I47Uf9Ab1PphIhF8xSWt/JUQYZwEDs9esF81wqKtGOS8N2mrrtAWX7goRUWsE/O7ywwAi1lwpr1MstexPkMdBsTlDLtvYtle8zSh62nXAfm3Fx3RJyG0zFff63LPoloEKOUdQX3xJVmHhmWtasOqwnqUdDjgr0zon36nOzBzWsq5wmlfn/gfsNMuuSHNzddffSTw5hoKQI5XQzFCj30x35lxNWO5RFJWvw3OAI2xV+PRpaWa2qzDJdQod1AOnO4dhViCjPWVAGuohERd44gz8orSxbqzKaPlE+D1+C1qVJ8v1euyNgb/geqDDH1O3BBjqdAVP/d78LxkAmV8D7hiJp42fELKGLux4XYIWdEo9ifMvotPb1vxe/EvB6FeguW0fH/iunMu5bvpx5NQX/uU77wUZE180w/k5GZ7ImhzOyHAqcgGZlESYB+UZmN9usIj+Z/RWaoUUK6xN+rOrTEEbmfIiIyx7TwP4T6Ai8h0nM+jJAD86joDdGgQftDn7Re8Jm7IVR3hqXgj4ny2fzeyg=',
        region_name='us-east-1'
        )
        

        s3.upload_file(

            Filename=nome_arquivo,
            Bucket='infrawatch-bronze',
            Key='problemas.json'

        )

        return problemas

    

    except requests.exceptions.RequestException as e:

        print(f"Erro na requisição: {e}")

        return None



    except json.JSONDecodeError as e:

        print(f"Erro ao decodificar JSON: {e}")

        print(f"Resposta completa da API: {resultado.text}")

        return None

if __name__ == "__main__":
    lambda_handler({}, None)