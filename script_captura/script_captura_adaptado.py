import os
import time
import psutil
import GPUtil
import pynvml
import platform
import subprocess
import mysql.connector
from unidecode import unidecode 
from datetime import datetime, timedelta, timezone

pynvml.nvmlInit()

conexao = mysql.connector.connect(
    host="",
    user="user-captura",
    password="Urubu100#",
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
        cursor.execute("""SELECT Componente.componente, Componente.numeracao, ConfiguracaoMonitoramento.descricao ConfiguracaoMonitoramento.funcaoPython,ConfiguracaoMonitoramento.idConfiguracaoMonitoramento, Servidor.idServidor, ConfiguracaoMonitoramento.limiteAtencao, ConfiguracaoMonitoramento.limiteCritico FROM Servidor JOIN Componente 
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
            limite_atencao = linha[6]
            limite_critico = linha[7]

            monitoramento.append({
                'componente': linha[0],
                'coluna': coluna,
                'funcao': funcao,
                'numeracao': numeracao,
                'fkConfiguracaoMonitoramento':fkConfig,
                'limiteAtencao': limite_atencao,
                'limiteCritico': limite_critico
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

def coletar_dados_processos():
    processos_total = []
    gpus_monitoradas = list(filter(lambda item: item['componente'] == 'GPU', monitoramento))

    for gpu in gpus_monitoradas:
        indice_gpu = int(gpu['numeracao']) - 1  # numeracao começa em 1

        handle = pynvml.nvmlDeviceGetHandleByIndex(indice_gpu)
        processos_gpu = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)

        for processo_gpu in processos_gpu:
            pid = processo_gpu.pid
            uso_gpu_em_mb = processo_gpu.usedGpuMemory / 1024 ** 2  # bytes → MB

            proc = psutil.Process(pid)
            nome = proc.name()
            uso_cpu = proc.cpu_percent(interval=None)
            uso_ram = proc.memory_info().rss / 1024 ** 2  # bytes → MB

            processos_total.append(tuple(
                nome,
                round(uso_cpu, 2),
                round(uso_gpu_em_mb, 2),
                round(uso_ram, 2)
            ))

    processos_total.sort(key=lambda x: x[2], reverse=True)
    return processos_total[:5]

def captura():
    while True:
        print("\n⏳ \033[1;34m Capturando informações de hardware e processos... \033[0m\n"
          "🛑 Pressione \033[1;31m CTRL + C \033[0m para encerrar a captura.")
        
        dados_servidor = coletar_dados()
        dados_processos = coletar_dados_processos()

        fuso_brasil = timezone(timedelta(hours=-3))
        data_hora_brasil = datetime.now(fuso_brasil).strftime('%Y-%m-%d %H:%M:%S')

        i = 0
        for item in monitoramento:
            query_relacional_captura = f'INSERT INTO Captura (dadoCaptura, dataHora, fkConfiguracaoMonitoramento) VALUES ({dados_servidor[i]}, "{data_hora_brasil}", {item['fkConfiguracaoMonitoramento']});'

            cursor.execute(query_relacional_captura)
            conexao.commit()

            if dados_servidor[i] >= item['limiteCritico']:
                query_relacional_alerta = f'INSERT INTO Alerta (dataHora, fkConfiguracaoMonitoramento, tipoAlerta) VALUES ({data_hora_brasil}, {item['fkConfiguracaoMonitoramento']}, 2);'

                cursor.execute(query_relacional_alerta)
                conexao.commit()
            elif dados_servidor[i] >= item['limiteAtencao']:
                query_relacional_alerta = f'INSERT INTO Alerta (dataHora, fkConfiguracaoMonitoramento, tipoAlerta) VALUES ({data_hora_brasil}, {item['fkConfiguracaoMonitoramento']}, 1);'

                cursor.execute(query_relacional_alerta)
                conexao.commit()
            
            i+=1

        for processo in dados_processos:
            query_relacional_processo = f'INSERT INTO Processo (nome, usoCpu, usoGpu, usoRam, dataHora, fkServidor) VALUES ({processo[0]}, {processo[1]}, {processo[2]}, {processo[3]}, {data_hora_brasil}, {id_servidor});'

            cursor.execute(query_relacional_processo)
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
