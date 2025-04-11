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

globais = {
    'COMANDOS_WINDOWS': ["powershell", "-Command", "Get-WmiObject Win32_BaseBoard ", "| Select-Object -ExpandProperty SerialNumber"],
    'COMANDOS_LINUX': "sudo dmidecode -s system-uuid",
    'conexao': None, 
    'cursor': None, 
    'UUID': None, 
    'ID_SERVDIDOR': None
}

INTERVALO_CAPTURA = 60


monitoramento = []

def conectar_bd() -> None:
    '''
        Inicia ou atualiza a conexão com o banco e o cursor.

        params:
            - None
        return:
            - None
    '''
    globais['conexao'] = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Ranier2006!",
        database="infrawatch"
    )

    globais['cursor'] = globais['conexao'].cursor()

def atualizar_itens_monitorar(query) -> None:
    '''
        Recebe o resultado da query de select para verificar os itens a ser monitorados de acordo com o que está cadastrado no banco.

        params:
            - query (list): resultado da query do select.
        return:
            - None
    '''
    for linha in query:
            numeracao = linha[1]
            funcao = linha[3]
            fkConfig = linha[4]
            limite_atencao = linha[6]
            limite_critico = linha[7]

            monitoramento.append({
                'componente': linha[0],
                'funcao': funcao,
                'numeracao': numeracao,
                'fkConfiguracaoMonitoramento':fkConfig,
                'limiteAtencao': limite_atencao,
                'limiteCritico': limite_critico
            })

def coletar_uuid() -> None:
    '''
        Coleta uuid do servidor e guarda na variável global.

        params:
            - None
        return:
            - None
    '''
    try:
        so =  platform.system()
    except Exception as e:
        print(e)

    try:
        sh = globais['COMANDOS_WINDOWS'] if so == "Windows" else globais['COMANDOS_LINUX']
        globais['UUID'] = subprocess.check_output(sh, shell=True).decode().strip()
    except subprocess.SubprocessError as e:
        print(e)


def inicializador() -> None:
    '''
        Validar se o servidor está cadastrado no banco baseado no uuid e se ele tem dados sobre os compnentes a serem monitorados.

        params:
            - None
        return:
            - None
    '''
    print("Iniciando verificação de Hardware... \n")
    coletar_uuid()
 
    if globais['UUID'] != None:
        globais['cursor'].execute("""SELECT * FROM viewGetServidor WHERE uuidPlacaMae = %s""", (globais['UUID'],))   

        resultado = globais['cursor'].fetchall()

        if len(resultado) == 0:
            print("🛑 O servidor não tem configuração de monitoramento cadastrado no Banco de Dados...")
            exit("")

        globais['ID_SERVDIDOR'] = resultado[0][5]

        atualizar_itens_monitorar(resultado)
        init()
    else:
        print("🛑 O servidor não está registrado no Banco de Dados...")
        exit("")

def coletar_dados() -> list:
    '''
        Coletar os dados dos hardwares informados na variável monitoramento, retornando uma lista com os dados coletados. OBS.: Usamod eval para traduzir string em codigo python.

        params:
            - None
        return:
            - list: lista com os dados coletados dos hardwares informados no monitoramento (dados vindos do banco)
    '''

    pynvml.nvmlInit()
    try:
        dados = []
        for item in monitoramento:
            funcao = item['funcao']
            numeracao = item['numeracao']
            try:
                dado = eval(funcao)
                if dado is None:
                    dado = -1 # erro na captura do dado
            except Exception as e:
                dado = -2 # Erro na execução da função

            dados.append(dado)

    except Exception as e:
        print(e)

    return dados

def enviar_notificacao(nivel_alerta, id_alerta) -> None:
    '''
        Abrir chamado no Jira da empresa e complementar com mensagem no Slack, informando o chamado e detalhes do alerta.

        params:
            - nivel_alerta (int): qual o nivel do alerta (1 - atenção, 2 - crítico)
            - id_alerta (int): id do alerta gravado no banco de dados
        return:
            - None
    '''
    # todo - implementar lógica de envio da notificacao 
    print("Abrir chamado e enviando mensagem no Slack...")
    pass

def coletar_dados_processos() -> list:
    '''
        Coleta dos processos das GPU's monitradas, sendo eles o uso da gpu, cpu e ram e retorna esta informação em forma de array/list.

        params:
            - None
        return:
            - list: lista com os dados dos top 5 processos em execução na GPU
    '''

    processos_total = {}
    gpus_monitoradas = list(filter(lambda item: item['componente'] == 'GPU', monitoramento))

    for gpu in gpus_monitoradas:
        indice_gpu = int(gpu['numeracao']) - 1

        handle = pynvml.nvmlDeviceGetHandleByIndex(indice_gpu)
        processos_gpu = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)

        for processo_gpu in processos_gpu:
            pid = processo_gpu.pid

            try:
                used_memory = processo_gpu.usedGpuMemory
                if used_memory is None:
                    print(f"[!] PID {processo_gpu.pid} tem usedGpuMemory = None")
                    uso_gpu_em_mb = 0.0
                else:
                    uso_gpu_em_mb = used_memory / 1024 ** 2
            except AttributeError as e:
                print(f"[!] Erro ao acessar usedGpuMemory no PID {processo_gpu.pid}: {e}")
                uso_gpu_em_mb = 0.0


            try:
                proc = psutil.Process(pid)
                nome = proc.name()
                uso_cpu = proc.cpu_percent(interval=None)
                uso_ram = proc.memory_info().rss / 1024 ** 2

                if nome not in processos_total:
                    processos_total[nome] = [0.0, 0.0, 0.0]

                processos_total[nome][0] += uso_cpu
                processos_total[nome][1] += uso_gpu_em_mb
                processos_total[nome][2] += uso_ram

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            
    processos_agrupados = [
        (nome, round(uso[0], 2), round(uso[1], 2), round(uso[2], 2))
        for nome, uso in processos_total.items()
    ]
    processos_agrupados.sort(key=lambda x: x[2], reverse=True)

    return processos_agrupados[:5]

def cadastrar_bd(query, params) -> int:
    '''
        Inserir dados no banco de dados e retornar o id do item cadastrado.

        params:
            - query (str): texto com formatação para fazer a query no banco
            - params (tuple): dados para complementarem a query
        return:
            - int: id do item inserido no banco de dados
    '''
    if not globais['conexao'].is_connected():
        globais['conexao'].reconnect()
        conectar_bd()

    try:
        globais['cursor'].execute(query, params)
        globais['conexao'].commit()
    except mysql.connector.Error as error:
        print(f"Erro ao executar a consulta: {error}")
    except Exception as error:  
        print(f"Erro inesperado: {error}")

    return globais['cursor'].lastrowid
    
def captura() -> None:
    '''
        Iniciar o processo de captura em um Loop while infinito, coletando os dados de hardware e processos a cada 10 minutos (INTERVALO_CAPTURA).

        params:
            - None
        return:
            - None
    '''

    while True:
        print("\n⏳ \033[1;34m Capturando informações de hardware e processos... \033[0m\n"
          "🛑 Pressione \033[1;31m CTRL + C \033[0m para encerrar a captura.")
        
        dados_servidor = coletar_dados()
        dados_processos = coletar_dados_processos()

        fuso_brasil = timezone(timedelta(hours=-3))
        data_hora_brasil = datetime.now(fuso_brasil).strftime('%Y-%m-%d %H:%M:%S')

        for config, valor in zip(monitoramento, dados_servidor):
            cadastrar_bd(f'INSERT INTO Captura (dadoCaptura, dataHora, fkConfiguracaoMonitoramento) VALUES (%s, %s, %s);', (valor, data_hora_brasil, config['fkConfiguracaoMonitoramento']))
            is_alerta = False
            nivel_alerta = 1

            if valor >= config['limiteCritico']:
                print("\n🚨 \033[1;34m Alerta crítico gerado... \033[0m\n")
                nivel_alerta = 2
                is_alerta = True
            elif valor >= config['limiteAtencao']:
                print("\n⚠️ \033[1;34m Alerta atenção gerado... \033[0m\n")
                is_alerta = True

            if is_alerta:
                id_alerta = cadastrar_bd(f'INSERT INTO Alerta (dataHora, fkConfiguracaoMonitoramento, nivel, valor) VALUES (%s, %s, %s, %s);', (data_hora_brasil, config['fkConfiguracaoMonitoramento'], 1, valor))
                enviar_notificacao(nivel_alerta, id_alerta)

        for processo in dados_processos:
            cadastrar_bd(f'INSERT INTO Processo (nomeProcesso, usoCpu, usoGpu, usoRam, dataHora, fkServidor) VALUES (%s,%s,%s,%s,%s,%s);', (processo[0], processo[1], processo[2], processo[3], data_hora_brasil, globais['ID_SERVDIDOR']))

        try:
            time.sleep(INTERVALO_CAPTURA)
            os.system('cls' if os.name == 'nt' else 'clear')
        except:
            exit("Encerrando Captura...")

def init() -> None:
    '''
        Iniciar a aplicação visual para mostrar opções do usuário (monitoramento ou sair), assim começando o processo de captura ou finalizando a aplicação.

        params:
            - None
        return:
            - None
    '''
    
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
    conectar_bd()
    inicializador()
