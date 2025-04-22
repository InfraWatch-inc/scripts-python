import json
import requests
import tempfile
import os
import boto3
import time
from datetime import datetime, timedelta, timezone
import mysql.connector
from mysql.connector.pooling import PooledMySQLConnection
from dotenv import load_dotenv

# rodar script
# entrar loop
# time.sleep de 24 horas
# a cada 24 horas vai selecionar os dados do banco
    # vai organizar para ficar json colunar por captura
    # guardar a data Hora mais recente para ignorar as informações antigas
# vai enviar para o b

load_dotenv()
fuso_brasil = timezone(timedelta(hours=-3))
ultima_coleta = None
s3 = boto3.client('s3')

def conectar_bd() -> PooledMySQLConnection: # TODO definir o retorno 
    '''
        Inicia ou atualiza a conexão com o banco e o cursor.

        params:
            - None
        return:
            - None
    '''
    conexao = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB')
    )
    return conexao

def enviar_arquivo(nome) -> None:
    s3.upload_file(
        Filename=nome,
        Bucket=os.getenv('BUCKET_NAME'),
        Key=f'coletas/{nome}.json'
    )

def coletar_registros(horario_coleta) -> list:
    # TODO esquematizar a condicao se o horario coleta vier none ou não
    condicao = ''
    if not horario_coleta:
        condicao = 'aaa' # TODO
    conexao = conectar_bd()
    cursor = conexao.cursor()
    cursor.execute("""SELECT * FROM viewGetServidor %s""", condicao) # TODO realizar o select
    resultado = cursor.fetchall()
    conexao.close()
    ultima_coleta = datetime.now(fuso_brasil).strftime('%d/%m/%Y-%H:%M')
    return resultado

def organizar_resultado(resultado) -> list: # TODO
    informacoes_coletas = []
    for linha in resultado:
        numeracao = linha[1]
        itens_descricao = linha[2]
        itens_descricao = itens_descricao.lower().split(' ')
        descricao = ''

        for item in itens_descricao:
            descricao += f'{item}'
            if item != itens_descricao[-1]:
                descricao += '_'
                
        coluna = f'{linha[0].lower()}{numeracao}_{descricao}'
        funcao = linha[3]
        fkConfig = linha[4]
        limite_atencao = linha[6]
        limite_critico = linha[7]

        informacoes_coletas.append({
            'componente': linha[0],
            'coluna': coluna,
            'funcao': funcao,
            'numeracao': numeracao,
            'fkConfiguracaoMonitoramento':fkConfig,
            'limiteAtencao': limite_atencao,
            'limiteCritico': limite_critico
        })

    return informacoes_coletas

def main() -> None:
    while True:
        resultado = coletar_registros(ultima_coleta)
        
        dicionario_registros = organizar_resultado(resultado)        

        nome_arquivo = os.path.join(tempfile.gettempdir(), f'coleta-{ultima_coleta}.json')

        with open(nome_arquivo, mode='wt') as file:
            json.dump(dicionario_registros, file)

        enviar_arquivo(nome_arquivo)

        # excluir json 

        time.sleep(86400) # 24 horas

if __name__ == "__main__":
    main()