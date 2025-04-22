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

load_dotenv()
fuso_brasil = timezone(timedelta(hours=-3))
s3 = boto3.client('s3')

def conectar_bd() -> PooledMySQLConnection:
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

def enviar_arquivo(nome, mes, ano) -> None:
    s3.upload_file(
        Filename=nome,
        Bucket=os.getenv('BUCKET_NAME'),
        Key=f'coletas/{ano}/{mes}/{nome}.json'
    )

def coletar_registros(horario_coleta) -> list:
    conexao = conectar_bd()
    cursor = conexao.cursor()

    if not horario_coleta:
        cursor.execute("SELECT * FROM viewAnalise;")
    else:
        cursor.execute(f"SELECT * FROM viewAnalise WHERE dataHora > %s;", (horario_coleta))

    resultado = cursor.fetchall()
    conexao.close()
    ultima_coleta = datetime.now(fuso_brasil)
    return resultado, ultima_coleta

def organizar_resultado(resultado) -> list:
    capturas_consolidadas = {}

    for linha in resultado:
        print(linha)
        servidor = linha[0]
        dataHora = linha[13].strftime('%Y-%m-%d %H:%M:%S')
        componente = linha[5].lower()
        numeracao = linha[6]
        descricao_original = linha[8]
        valor_monitorado = linha[9]
        gerou_alerta = linha[12] == 'Sim'

        itens_descricao = descricao_original.lower().split(' ')
        descricao = '_'.join(itens_descricao)
        coluna = f'{componente}{numeracao}_{descricao}'

        chave = (servidor, dataHora)

        if chave not in capturas_consolidadas:
            capturas_consolidadas[chave] = {
                "servidor": servidor,
                "dtHora": dataHora,
                "isAlerta": False
            }

        capturas_consolidadas[chave][coluna] = valor_monitorado

        if gerou_alerta:
            capturas_consolidadas[chave]["isAlerta"] = True

    return list(capturas_consolidadas.values())

def main() -> None:
    global ultima_coleta
    ultima_coleta = None
    while True:
        resultado, ultima_coleta = coletar_registros(ultima_coleta)
        
        dicionario_registros = organizar_resultado(resultado)   
        dt_arquivo = ultima_coleta.strftime('%d-%H:%M')

        nome_arquivo = os.path.join(tempfile.gettempdir(), f'coleta-{dt_arquivo}.json')
        
        with open(nome_arquivo, mode='wt') as file:
            json.dump(dicionario_registros, file)

        mes = ultima_coleta.month
        ano = ultima_coleta.year
        #enviar_arquivo(nome_arquivo, mes, ano)

        time.sleep(86400) # 24 horas

if __name__ == "__main__":
    main()