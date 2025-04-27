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

# TODO adicionar pastas de ano e mes após Java (Lambda) conseguir identificar esse caminho

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
        database=os.getenv('DB'),
        port=os.getenv('DB_PORT')
    )
    return conexao

def enviar_arquivo(nome, mes, ano) -> None:
    '''
        Envia o arquivo JSON para o bucket S3.

        params:
            - nome (str): nome do arquivo a ser enviado.
            - mes (int): mês do arquivo a ser enviado.
            - ano (int): ano do arquivo a ser enviado.
        return:
            - None
    '''
    diretorio = nome.split('/')[2]
    s3.upload_file(
        Filename=nome,
        Bucket=os.getenv('BUCKET_NAME'),
        Key=nome.split('/')[2]
    )

def coletar_registros(horario_coleta) -> list:
    '''
        Coleta os registros do banco de dados a partir do horário da última coleta.

        params:
            - horario_coleta (datetime): horário da última coleta.
        return:
            - list: lista de tuplas com os dados coletados do banco de dados.
    '''
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
    '''
        Organiza os dados coletados do banco de dados em um dicionário estruturado.
        
        params:
            - resultado (list): lista de tuplas com os dados coletados do banco de dados.
        return:
            - list: lista de dicionários com os dados organizados.
    '''
    capturas_consolidadas = {}

    for linha in resultado:
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
    '''
    Inicia o processo de ETL, coletando dados do banco de dados e enviando para o S3.
    O processo é executado diariamente, coletando dados a cada 24 horas.

    params:
        - None
    return:
        - None
    '''
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
        enviar_arquivo(nome_arquivo, mes, ano, file)

        print("\n⏳ \033[1;34m Capturando informações de hardware e processos... \033[0m\n"
          "🛑 Pressione \033[1;31m CTRL + C \033[0m para encerrar a captura.")
        
        try:
            time.sleep(86400)
            os.system('cls' if os.name == 'nt' else 'clear')
        except:
            exit("Encerrando Captura...")

def init() -> None:
    '''
        Inicia o script com uma interface para interação com o usuário.

        params:
            - None
        return:
            - None
    '''
    print("SCRIPT DE ETL DOS DADOS DE CAPTURA:")
    print("✏️  Digite a opção desejada para continuar:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("1  Iniciar ETL")
    print("2  Sair")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    while True:
        opt = input("Digite uma opção: ")

        if opt == "1":
            try:
                main()
            except Exception as error:
                if error.args[0] == 1452:
                    print("\033[1;31m Encerrando captura: \033[0m Este servidor não está cadastrado em nosso sistema.")
                else:
                    print(error)
            break
            
        elif opt == "2":
            exit(f"Até a próxima!")
        else:
            print("Opção inválida!")

if __name__ == "__main__":
    init()