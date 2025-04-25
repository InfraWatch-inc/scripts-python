import os
import time
import psutil
import GPUtil
import pynvml
from dotenv import load_dotenv
import platform
import subprocess
import mysql.connector
from datetime import datetime, timedelta, timezone

load_dotenv()
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
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB'),
        port=os.getenv('DB_PORT')
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

def coletar_dados_processos() -> dict:
    '''
        Coleta dos processos do servidor monitorado, sendo eles ranqueados em uso da gpu, cpu e ram e retorna esta informação em forma de dict.

        params:
            - None
        return:
            - dict: onjeto com os dados dos top 5 processos em execução no servidor
    '''
    processos_agregados = {}

    # gpus que estão sendo monitoradas
    gpus_monitoradas = list(filter(lambda item: item['componente'] == 'GPU', monitoramento))
    if gpus_monitoradas:
        for gpu in gpus_monitoradas: # para cada gpu
            indice_gpu = int(gpu['numeracao']) - 1 # coletar index da gpu

            try: 
                handle = pynvml.nvmlDeviceGetHandleByIndex(indice_gpu) # seleciona gpu que vou ver os processos 
                processos_gpu = pynvml.nvmlDeviceGetComputeRunningProcesses(handle) # coleta os processos da gpu

                for processo in processos_gpu:
                    try:
                        proc = psutil.Process(processo.pid) # identifica o processo 
                        nome = proc.name()

                        if nome not in processos_agregados: # se o processo não estiver na lista, adiciona zerado
                            processos_agregados[nome] = {"uso_cpu": 0.0, "uso_ram": 0.0, "uso_gpu": 0.0}

                        # soma os dados do processo
                        gpu_mem = processo.usedGpuMemory or 0
                        processos_agregados[nome]["uso_gpu"] += round(gpu_mem / 1024**2,2)  # MB
                        processos_agregados[nome]["uso_cpu"] += round(proc.cpu_percent(interval=0.1),2)
                        processos_agregados[nome]["uso_ram"] += round(proc.memory_percent(),2)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except pynvml.NVMLError:
                continue

    # Coleta processos que não dependem de GPU necessariamente
    for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
        try:
            nome = proc.info['name']

            if nome not in processos_agregados: # mesma logica de verificar se o processo existe 
                processos_agregados[nome] = {"uso_cpu": 0.0, "uso_ram": 0.0, "uso_gpu": 0.0}

            # adiciona os valores dos processos
            processos_agregados[nome]["uso_cpu"] += round(proc.info['cpu_percent'],2)
            processos_agregados[nome]["uso_ram"] += round(proc.info['memory_percent'],2)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Converte para lista de obj
    processos_lista = [{
        "nome": nome,
        "uso_gpu": dados["uso_gpu"],
        "uso_cpu": dados["uso_cpu"],
        "uso_ram": dados["uso_ram"]
    } for nome, dados in processos_agregados.items()]

    # ordena os processos com hirarquia de uso gpu, cpu e ram
    processos_ordenados = sorted(
        processos_lista,
        key=lambda p: (p['uso_gpu'], p['uso_cpu'], p['uso_ram']),
        reverse=True
    )
    # retorna os top5
    return processos_ordenados[:5]

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
            cadastrar_bd(f'INSERT INTO Processo (nomeProcesso, usoCpu, usoGpu, usoRam, dataHora, fkServidor) VALUES (%s,%s,%s,%s,%s,%s);', (processo['nome'], processo['uso_cpu'], processo['uso_gpu'], processo['uso_ram'], data_hora_brasil, globais['ID_SERVDIDOR']))

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
