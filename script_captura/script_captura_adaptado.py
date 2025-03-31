import os
import time
import psutil
import GPUtil
import platform
import subprocess
import mysql.connector
from unidecode import unidecode 
from datetime import datetime, timedelta, timezone

conexao = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Ranier2006!",
    database="infrawatch"
)
cursor = conexao.cursor()

windows_sh = ["powershell", "-Command", "Get-WmiObject Win32_BaseBoard ", "| Select-Object -ExpandProperty SerialNumber"]
linux_sh = "sudo dmidecode -s system-uuid"
monitoramento = []

def inicializador():
    try:
        so =  platform.system()
    except Exception as e:
        print(e)

    try:
        sh = windows_sh if so == "Windows" else linux_sh
        global mother_board_uuid
        mother_board_uuid = subprocess.check_output(sh, shell=True).decode().strip()
    except subprocess.SubprocessError as e:
        print(e)

# Pegando o Informações de coleta
 
    if mother_board_uuid != None:
        cursor.execute("""SELECT Componente.componente, Componente.numeracao, ConfiguracaoMonitoramento.descricao,ConfiguracaoMonitoramento.funcaoPython,ConfiguracaoMonitoramento.idConfiguracaoMonitoramento, Servidor.idServidor FROM Servidor JOIN Componente 
              ON Servidor.idServidor = Componente.fkServidor JOIN ConfiguracaoMonitoramento ON
              ConfiguracaoMonitoramento.fkComponente = Componente.idComponente 
              WHERE Servidor.uuidPlacaMae = %s""", (mother_board_uuid,))   

        resultado = cursor.fetchall()

        if len(resultado) == 0:
            print("🛑 O servidor não tem configuração de monitoramento cadastrado no Banco de Dados...")
            exit("")

        global id_servidor
        id_servidor = resultado[0][5]

        for linha in resultado:
            numeracao = linha[1]
            itens_descricao = unidecode(linha[2])
            itens_descricao = itens_descricao.lower().split(' ')
            descricao = ''

            for item in itens_descricao:
                descricao += f'{item}'
                if item != itens_descricao[-1]:
                    descricao += '_'
                    
            coluna = f'{linha[0].lower()}{numeracao}_{descricao}'
            funcao = linha[3]
            fkConfig = linha[4]

            monitoramento.append({
                'coluna': coluna,
                'funcao': funcao,
                'numeracao': numeracao,
                'fkConfiguracaoMonitoramento':fkConfig
            })
        init()
    else:
        print("🛑 O servidor não está registrado no Banco de Dados...")
        exit("")

def coletar_dados():
    try:
        dados = []
        for item in monitoramento:
            funcao = item['funcao']
            numeracao = item['numeracao']
            dados.append(eval(funcao))

    except Exception as e:
        print(e)

    return dados

def captura():
    while True:
        print("\n⏳ \033[1;34m Capturando informações de hardware... \033[0m\n"
          "🛑 Pressione \033[1;31m CTRL + C \033[0m para encerrar a captura.")
        
        dados_servidor = coletar_dados()

        fuso_brasil = timezone(timedelta(hours=-3))
        data_hora_brasil = datetime.now(fuso_brasil).strftime('%Y-%m-%d %H:%M:%S')

        colunas = ''
        dados_inserir = ''

        i = 0
        for item in monitoramento:
            colunas += f'{item['coluna']}'
            dados_inserir += f'{dados_servidor[i]}'

            query_relacional = f'INSERT INTO Captura (dadoCaptura, dataHora, fkConfiguracaoMonitoramento) VALUES ({dados_servidor[i]}, "{data_hora_brasil}", {item['fkConfiguracaoMonitoramento']});'

            cursor.execute(query_relacional)
            conexao.commit()

            # TODO adicionar insert na tabela alerta caso necessário 
            # TODO e usar campo isAlerta da tabela captura_servidor_n

            colunas += ','
            dados_inserir += ','
            
            i+=1
        
        query_dataframe = f"INSERT INTO captura_servidor_{id_servidor} ({colunas} dtHora) VALUES ({dados_inserir} '{data_hora_brasil}');"
  
        cursor.execute(query_dataframe)
        conexao.commit()

        

        try:
            time.sleep(600)
            os.system('cls' if os.name == 'nt' else 'clear')
        except:
            exit("")

def init():
    print("Iniciando verificação de Hardware... \n")

    # Menu de pções para o usuário:
    print("🔧 Menu de Ações:")
    print("✏️  Digite a opção desejada para continuar:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("1  Iniciar monitoramento")
    print("2  Sair")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    while True:
        opt = input("Digite uma opção: ")

        if opt == "1":
            try:
                captura()
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
    inicializador()
