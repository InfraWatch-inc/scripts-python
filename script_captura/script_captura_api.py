import os
import time
import psutil
import GPUtil
import pynvml
import requests
import platform
import subprocess
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from time import time as tempo_atual

load_dotenv()
globais = {
    'COMANDOS_WINDOWS': ["powershell", "-Command", "Get-WmiObject Win32_BaseBoard ", "| Select-Object -ExpandProperty SerialNumber"],
    'COMANDOS_LINUX': "sudo dmidecode -s system-uuid",
    'UUID': None, 
    'ID_SERVDIDOR': None,
    'IS_GPU': False
}

INTERVALO_CAPTURA = 10

MAX_ALERTAS_POR_COMPONENTES = 5

TEMPO_RESETA_ALERTA = 300 # o tempo está em segundos

monitoramento = []

controle_alertas = {}

def atualizar_itens_monitorar(query) -> None:
    '''
        Recebe o resultado da query de select para verificar os itens a ser monitorados de acordo com o que está cadastrado no banco.

        params:
            - query (list): resultado da query do select.
        return:
            - None
    '''
    for linha in query:
            numeracao = linha['numeracao']
            unidadeMedida = linha['unidadeMedida']
            funcao = linha['funcaoPython']
            fkConfig = linha['idConfiguracaoMonitoramento']
            limite_atencao = linha['limiteAtencao']
            limite_critico = linha['limiteCritico']
        

            monitoramento.append({
                'componente': linha['componente'],
                'funcao': funcao,
                'numeracao': numeracao,
                'metrica': unidadeMedida,
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

    uuid = globais["UUID"]

    return uuid

def is_GPU(json) -> bool:
    for item in json:
        if item['componente'] == "GPU":
            globais['IS_GPU'] = True
            return True
        
    return False

def inicializador() -> None:
    '''
        Validar se o servidor está cadastrado no banco baseado no uuid e se ele tem dados sobre os componentes a serem monitorados.

        params:
            - None
        return:
            - None
    '''
    print("Iniciando verificação de Hardware... \n")
    coletar_uuid()
 
    if globais['UUID'] != None:
        res = requests.get(f"{os.getenv('WEB_URL')}/monitoramento/{globais['UUID']}")

        resultado = res.json()

        if res.status_code != 200:
            print("🛑 O servidor não está registrado no Banco de Dados...")
            exit("")

        if len(resultado) == 0:
            print("🛑 O servidor não tem configuração de monitoramento cadastrado no Banco de Dados...")
            exit("")

        globais['ID_SERVDIDOR'] = resultado[0]['idServidor']

        atualizar_itens_monitorar(resultado)
        
        if is_GPU(resultado):
            try:
                pynvml.nvmlInit()
                print("✅ GPU detectada e pynvml iniciado.")
            except pynvml.NVMLError as e:
                print("❌ Erro ao iniciar pynvml:", e)

    while True:
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

    # pynvml.nvmlInit()
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


def post_dados(dados) -> None:
    '''

    '''    
    res = requests.post(f"{os.getenv('WEB_URL')}/monitoramento/cadastrar/dados/{globais['ID_SERVDIDOR']}", data=json.dumps(dados), headers={'Content-Type': 'application/json'})

    if res.status_code == 200:
        print("ok")
    else:
        print("Não cadastrou os dados")

    print("dados capturados: ", dados)

def post_alerta(nivel_alerta, data_hora_brasil, fkConfiguracaoMonitoramento, valor) -> int:
    '''
    
    '''
    dicionario_alerta = {
        'dadoCaptura': valor,
        'dataHora': data_hora_brasil,
        'fkConfiguracaoMonitoramento': fkConfiguracaoMonitoramento,
        'nivel': nivel_alerta
    }
    
    res = requests.post(f"{os.getenv('WEB_URL')}/monitoramento/cadastrar/alerta", data=json.dumps(dicionario_alerta), headers={'Content-Type': 'application/json'})

    if res.status_code == 200:
        print("ok")
        return res.json()['insertId']
    else:
        print("Não cadastrou o alerta")
        return -1

    

def post_processos(dados_processos, idServidor, data_hora) -> None:
    '''
  
    '''
    dictionario_processos = {
        'idServidor': idServidor,
        'dataHora': data_hora,
        'processos': dados_processos
    }

    print(dictionario_processos)

    res = requests.post(f"{os.getenv('WEB_URL')}/monitoramento/cadastrar/processos", data=json.dumps(dictionario_processos), headers={'Content-Type': 'application/json'})

    if res.status_code == 200:
        print("ok")
    else:
        print("Não cadastrou os processos")

def post_jira(id_alerta, id_servidor, nivel, data_hora, componente, metrica, valor) -> None:
    '''
    '''

    dicionario_chamado = {
        'idAlerta': id_alerta,
        'idServidor': id_servidor,
        'nivel': nivel,
        'dataHora': data_hora,
        'componente': componente,
        'metrica': metrica,
        'valor': valor
    }

    print(dicionario_chamado)

    res = requests.post(f"{os.getenv('WEB_URL')}/monitoramento/cadastrar/chamado", data=json.dumps(dicionario_chamado), headers={'Content-Type': 'application/json'})

    if res.status_code == 200:
        print("ok")
    else: 
        print("Não realizou a abertura de chamado")
    pass

def coletar_dados_processos() -> list:
    '''
        Coleta dos processos do servidor monitorado, sendo eles ranqueados em uso da gpu, cpu e ram e retorna esta informação em forma de list.

        params:
            - None
        return:
            - list: array com os dados dos top 5 processos (dicts) em execução no servidor
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

    # remove processos inúteis, esse processo retorna valores de até 800%, pois é dividido pelos núcleos.
    processos_ordenados = list(filter(lambda p: p['nome'] != "System Idle Process", processos_ordenados)) 

    # retorna os top5
    return processos_ordenados[:5]

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
            # break
            
        elif opt == "2":
            exit(f"Até a próxima!")
        else:
            print("Opção inválida!")

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

        is_alerta = False
        nivel_alerta = 1
        dicionario_capturas = []
        # id_chamado = None

        for config, valor in zip(monitoramento, dados_servidor):
            is_alerta_loop = False
            dicionario_capturas.append({
                'dadoCaptura': valor,
                'componente': config['componente'],
                'metrica': config['metrica'],
                'unidade': config['numeracao']
            })

            if valor >= config['limiteCritico']:
                print("\n🚨 \033[1;34m Alerta crítico gerado... \033[0m\n")
                nivel_alerta = 2
                is_alerta = True
                is_alerta_loop = True
                
            elif valor >= config['limiteAtencao']:
                print("\n⚠️ \033[1;34m Alerta atenção gerado... \033[0m\n")
                is_alerta = True
                is_alerta_loop = True

            if is_alerta_loop:
                componente_key = f"{config['componente']}_{config['numeracao']}"

                now = tempo_atual()
                # Verifica se o componente já tem um alerta registrado
                alerta_info = controle_alertas.get(componente_key, {"contador": 0, "ultimo_alerta": 0})

                #reseta o contador dos alertas que passaram do tempo limite.
                if now - alerta_info["ultimo_alerta"] > TEMPO_RESETA_ALERTA:
                    alerta_info = {"contador": 0, "ultimo_alerta": now}

                if alerta_info["contador"] < MAX_ALERTAS_POR_COMPONENTES: 
                    id_alerta = post_alerta(nivel_alerta, data_hora_brasil, config['fkConfiguracaoMonitoramento'], valor)
                    id_chamado = post_jira(
                        id_alerta=id_alerta,
                        id_servidor=globais['ID_SERVDIDOR'],
                        nivel=nivel_alerta,
                        data_hora=data_hora_brasil,
                        componente=config['componente'],
                        metrica=config['metrica'],
                        valor=valor
                    )

                    alerta_info["contador"]+=1
                    alerta_info["ultimo_alerta"] = now
                
                else:
                    print( print(f"🔕 Alerta para {componente_key} suprimido (limite de {MAX_ALERTAS_POR_COMPONENTES} atingido)."))

                controle_alertas[componente_key] = alerta_info
        
        dados_tempo_real = {
            'idServidor': globais['ID_SERVDIDOR'],
            'dataHora': data_hora_brasil,
            'processos': dados_processos,
            'dadosCaptura': dicionario_capturas,
            'isAlerta': is_alerta,
            # 'modelo': modelo
            'idChamado': locals().get('id_chamado', None) if is_alerta_loop else None
        } 

        post_dados(dados_tempo_real)

        if is_alerta:
            post_processos(dados_processos, globais["ID_SERVDIDOR"], data_hora_brasil)
       
        try:
            time.sleep(INTERVALO_CAPTURA)
            os.system('cls' if os.name == 'nt' else 'clear')
        except KeyboardInterrupt:
            print("\n🛑 \033[1;31m Captura interrompida pelo usuário. \033[0m")
            exit("Encerrando Captura...")
        except Exception as e:
            print(f"Erro ao limpar a tela: {e}")
            exit("Encerrando Captura...")

if __name__ == "__main__":
    inicializador()