import os
import time
import psutil
import GPUtil
import pynvml
import requests
import platform
import subprocess
import json
import cpuinfo
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

TEMPO_RESETA_ALERTA = 3600 # o tempo está em segundos

monitoramento = []

dadosComponentes = []

controle_alertas = {}

fkEmpresa = None
fkEndereco = None

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
        Fazer o login, validar se o servidor está cadastrado no banco baseado no uuid e se ele tem dados sobre os componentes a serem monitorados.

        params:
            - None
        return:
            - None
    ''' 

    global fkEmpresa, fkEndereco

    # Login do usuário
    print("\n" + "🔑" * 20 + " LOGIN " + "🔑" * 20)
    print("Por favor, insira suas credenciais para continuar:\n")
    emailLogin = input("📧 Digite seu e-mail: ")
    senhaLogin = input("🔒 Digite sua senha: ")
    print("-" * 45 + "\n")

    url = f"{os.getenv('WEB_URL')}/colaboradores/autenticar/{emailLogin}/{senhaLogin}"
    
    resultado = requests.post(url)


    if resultado.status_code != 200:
            print("🛑 O usuário ou senha incorretos... \n")
    
    
    else:
        print("\nLogin feito com sucesso! \n")
        # print("resultado do login quando da certo", resultado.json())

        fkEmpresa = resultado.json()['fkEmpresa']
        
        urlEnd = f"{os.getenv('WEB_URL')}/empresas/buscar/{fkEmpresa}"
        resultadoEnd = requests.get(urlEnd)
        # print("OLHA AQUI KAIO", resultadoEnd.json())
        if resultadoEnd.status_code != 200:
            print("🛑 O endereco baseado no idEmpresa não foi pego... \n")
            # print(resultadoEnd.json())
        else:
            fkEndereco = resultadoEnd.json()[0]['fkEndereco']
        
        # print("fkEmpresa ver se funcionou", fkEmpresa)
        # print("enderoco ver se funcionou", fkEndereco)

        print("Iniciando verificação de Hardware... \n")
        coletar_uuid()
    
        if globais['UUID'] != None:
            res = requests.get(f"{os.getenv('WEB_URL')}/monitoramento/{globais['UUID']}")

            resultado = res.json()

            if res.status_code != 200:
                print("🛑 O servidor não está registrado no Banco de Dados... \n")

                print("✏️  Deseja cadastrar seu servidor? \n")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print("1  Sim!")
                print("2  Não!")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                resposta = input("Digite uma opção:")

                if resposta == '1':
                    cadastrar_servidor()
                else:
                    exit(f"Até a próxima!")

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

def extrair_marca_gpu(nome_gpu):
    nome_gpu = nome_gpu.strip().lower()
    if "nvidia" in nome_gpu:
        return "NVIDIA", nome_gpu.replace("NVIDIA", "").strip()
    elif "amd" in nome_gpu:
        return "AMD", nome_gpu.replace("AMD", "").strip()
    elif "intel" in nome_gpu:
        return "Intel", nome_gpu.replace("Intel", "").strip()
    else:
        return "Desconhecida", nome_gpu

def extrair_marca_cpu(nome_cpu):
    nome_cpu = nome_cpu.strip().lower()  
    if "amd" in nome_cpu:
        return "AMD"
    elif "intel" in nome_cpu:
        return "Intel"
    else:
        return "Desconhecida"

def capturar_modelo_disco() -> None:
    try:
        COMANDO_WINDOWS = ["powershell", "-Command", "Get-WmiObject Win32_DiskDrive | Select-Object -ExpandProperty Model"]

        resultado = subprocess.check_output(COMANDO_WINDOWS, shell=True).decode().strip()

        return resultado
    
    except subprocess.SubprocessError as e:
        print(e)

def cadastrar_servidor() -> None:

    print("\n" + "═" * 40)
    print(" 📝  CADASTRO DE NOVO SERVIDOR ")
    print("═" * 40 + "\n")

    tagName = input("🏷️  Tag do servidor: ")
    
    uuidPlacaMae = coletar_uuid()
    idInstancia = None
    
    status = input("⚙️  Status do servidor (ativo ou inativo): ").strip().lower()

    if status not in ['ativo', 'inativo']:
        print("⚠️  Status inválido. Digite 'ativo' ou 'inativo'.")
        exit()
    
    dtCadastro = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    so = input("💻  Sistema operacional (Ex: Windows ou Linux):")
  
    
    url = f"{os.getenv('WEB_URL')}/servidores/cadastrarDoPython"

    jsonServidor = {
        "tagName": tagName,
        "tipo": 'fisico',
        "uuid": uuidPlacaMae,
        "idInstancia": idInstancia,
        "status": status,
        "dtCadastro": dtCadastro,
        "so": so,
        "fkEmpresa": fkEmpresa,
        "fkEndereco": fkEndereco
    }
    
    print("\n📤  Enviando dados para cadastro")

    res = requests.post(url, data=json.dumps(jsonServidor), headers={'Content-Type': 'application/json'})

    print("-" * 40)
    if res.status_code == 200:
       print("✅  Servidor cadastrado com sucesso!")
    else:
        print("❌  Falha ao cadastrar o servidor.")

def cadastrar_componente() -> None:
    '''
        Iniciando a captura dos componentes presentes no servidor e posteriomente cadastrando os mesmos no banco.

    '''
    # print("Estou mostrando numero do servidor que sera cadastrado os componentes", globais['ID_SERVDIDOR'])
    
    componentes = []

# ===================================== CPU =====================================
    infoCPU = cpuinfo.get_cpu_info()
    modeloCPU = infoCPU['brand_raw']

    # Pego apenas a cpu principal do servidor, não encontrei maneira no python de capturar marcas de CPUs diferentes caso houver    
    marcaCPU = extrair_marca_cpu(modeloCPU)

    print(f"1: Marca: {marcaCPU} | Modelo: {modeloCPU}")

    componentes.append({
                "componente": "CPU", 
                "marca": marcaCPU,
                "numeracao": 1,
                "modelo":modeloCPU}) 
        
    # print(componentes)

# ===================================== GPU =====================================
    infoGPU = GPUtil.getGPUs()
  
    for i, gpu in enumerate(infoGPU, start=1):
        marcaGPU, modeloGPU = extrair_marca_gpu(gpu.name)

        # print(f"{i}: Marca: {marcaGPU} | Modelo: {modeloGPU}")

        componentes.append({
                    "componente": "GPU", 
                    "marca": marcaGPU,
                    "numeracao": i,
                    "modelo":modeloGPU}) 
        
# ===================================== RAM =====================================
    print("Captura dos componentes como CPU e GPU feitas!")
    print("==========================================================================\n")
    print("✏️   Vamos cadastrar a marca e modelo de sua RAM!:\n")

    optMarcaRAM = input("Digite aqui a marca de sua RAM:")
    marcaRAM = optMarcaRAM

    optModeloRAM = input("Digite aqui o modelo de sua RAM:")
    modeloRAM = optModeloRAM
    
    componentes.append({
                    "componente": "RAM", 
                    "marca": marcaRAM,
                    "numeracao": 1,
                    "modelo":modeloRAM})
    
# ===================================== DISCO =====================================

    print("\n==========================================================================\n")
    print("🖴  Capturando modelo de disco automaticamente...\n")
    modelo_disco = capturar_modelo_disco()
    if modelo_disco: 
        print("✏️  Agora iremos cadastrar a marca de seu Disco principal!:\n")

        optMarcaDISCO = input("Digite aqui a marca de seu Disco:")
        marcaDISCO = optMarcaDISCO

        componentes.append({
                        "componente": "DISCO", 
                        "marca": marcaDISCO,
                        "numeracao": 1,
                        "modelo":modelo_disco})

    # Print final

    dadosComponentes.append({
        "fkServidor": globais['ID_SERVDIDOR'],
        "componentes": componentes
    })

    # print("Componentes FINAL", dados)

    post_dadosComponente(dadosComponentes)
    return dadosComponentes
    
def post_dadosComponente(dadosComponentes) -> None:
    '''

    '''    
    res = requests.post(f"{os.getenv('WEB_URL')}/componente/cadastrar/dados/{globais['ID_SERVDIDOR']}", data=json.dumps(dadosComponentes), headers={'Content-Type': 'application/json'})

    if res.status_code == 200:
        print("Componentes cadastrados com sucesso!")
    else:
        print("Não cadastrou os dados")

    # print("dados capturados: ", dados)

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

def post_configuracoes_monitoramento(configuracoes) -> None:
    '''
    Inserindo configurações de monitoramento no banco de dados.
    '''
    url = f"{os.getenv('WEB_URL')}/componente/cadastrar/configuracaoMonitoramento"
    res = requests.post(url, data=json.dumps(configuracoes), headers={'Content-Type': 'application/json'})

    try:
        res = requests.post(url, data=json.dumps(configuracoes), headers={'Content-Type': 'application/json'})

        if res.status_code >= 200 and res.status_code < 300: # Verifica se o status é 2xx (sucesso)
            print("✅ Cadastrei a configuração do monitoramento com sucesso!")
        else:
            print("❌ Não cadastrou a configuração do monitoramento.")
            print(f"Status Code: {res.status_code}") # Imprime o status code
            print(f"Response Text: {res.text}")     # Imprime o texto da resposta da API
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão ao enviar configurações de monitoramento: {e}")

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



def configurar_monitoramento() -> None:
    """
    Permite ao usuário escolher as configurações de monitoramento para cada componente,
    incluindo a definição dos limites de atenção e crítico.
    """
    configuracoes = []

    url = f"{os.getenv('WEB_URL')}/servidores/buscar/servidorPython/{globais['ID_SERVDIDOR']}"

    resultado = requests.get(url)

    if resultado.status_code != 200:
        print("Ta errado kaio", resultado)
    else:
        print(resultado.json())

        componentes = resultado.json()

        for componente_info in componentes:
            componente_tipo = componente_info.get('componente')
            componente_id = componente_info.get('idComponente')

            print(f"\n--- Configuração para {componente_tipo} (ID: {componente_id}) ---")

            if componente_tipo == 'CPU':

                # Configuração para CPU

                print("\n--- Configuração para CPU ---")
                print("1: Uso da CPU (%)")
                print("2: Frequência da CPU (MHz)")
                opcao_cpu = input("Digite o número da opção desejada para CPU: ")

                if opcao_cpu == '1':
                    print("\nConfigurando: Uso da CPU (%)")
                    try:
                        limite_atencao = float(input("Digite o limite de atenção (ex: 80.0): "))
                        limite_critico = float(input("Digite o limite crítico (ex: 95.0): "))
                        configuracoes.append({ 
                                'unidadeMedida': '%',
                                'descricao': 'Uso da CPU',
                                'fkComponente': componente_id,
                                'limiteAtencao': limite_atencao,
                                'limiteCritico': limite_critico,
                                'funcaoPython': 'psutil.cpu_percent()'
                            })
                        print("Configuração de uso da CPU adicionada.")
                    except ValueError:
                        print("Entrada inválida para os limites. Por favor, digite um número.")
                elif opcao_cpu == '2':
                    print("\nConfigurando: Frequência da CPU (MHz)")
                    try:
                        limite_atencao = float(input("Digite o limite de atenção (ex: 2000.0): "))
                        limite_critico = float(input("Digite o limite crítico (ex: 4000.0): "))
                        configuracoes.append({ 
                                'unidadeMedida': 'MHz',
                                'descricao': 'Frequência da CPU',
                                'fkComponente': componente_id,
                                'limiteAtencao': limite_atencao,
                                'limiteCritico': limite_critico,
                                'funcaoPython': 'psutil.cpu_freq().current'
                            })
                        print("Configuração de frequência da CPU adicionada.")
                    except ValueError:
                        print("Entrada inválida para os limites. Por favor, digite um número.")
                else:
                    print("Opção inválida para CPU.")

            elif componente_tipo == 'RAM':

                # Configuração para RAM

                print("\n--- Configuração para RAM ---")
                print("1: Uso da Memória RAM (%)")
                print("2: Uso da Memória RAM (Byte)")
                opcao_ram = input("Digite o número da opção desejada para RAM: ")

                if opcao_ram == '1':
                    print("\nConfigurando: Uso da Memória RAM (%)")
                    try:
                        limite_atencao = float(input("Digite o limite de atenção (ex: 75.0): "))
                        limite_critico = float(input("Digite o limite crítico (ex: 90.0): "))
                        configuracoes.append({ 
                                'unidadeMedida': '%',
                                'descricao': 'Uso da Memória RAM',
                                'fkComponente': componente_id,
                                'limiteAtencao': limite_atencao,
                                'limiteCritico': limite_critico,
                                'funcaoPython': 'psutil.virtual_memory().percent'
                            })
                        print("Configuração de uso da RAM (porcentagem) adicionada.")
                    except ValueError:
                        print("Entrada inválida para os limites. Por favor, digite um número.")
                elif opcao_ram == '2':
                    print("\nConfigurando: Uso da Memória RAM (Byte)")
                    try:
                        limite_atencao = float(input("Digite o limite de atenção (ex: 8000000000): "))
                        limite_critico = float(input("Digite o limite crítico (ex: 16000000000): "))
                        configuracoes.append({ 
                                'unidadeMedida': 'Byte',
                                'descricao': 'Uso da Memória RAM',
                                'fkComponente': componente_id,
                                'limiteAtencao': limite_atencao,
                                'limiteCritico': limite_critico,
                                'funcaoPython': 'psutil.virtual_memory().used'
                            })
                        print("Configuração de uso da RAM (bytes) adicionada.")
                    except ValueError:
                        print("Entrada inválida para os limites. Por favor, digite um número.")
                else:
                 print("Opção inválida para RAM.")

            elif componente_tipo == 'DISCO':
                # Configuração para disco
                print("\n--- Configuração para disco ---")
                print("1: Uso do disco (%)")
                opcao_disco = input("Digite o número da opção desejada para disco: ")

                if opcao_disco == '1':
                    print("\nConfigurando: Uso do disco (%)")
                    try:
                        limite_atencao = float(input("Digite o limite de atenção (ex: 85.0): "))
                        limite_critico = float(input("Digite o limite crítico (ex: 95.0): "))
                        configuracoes.append({ 
                                'unidadeMedida': '%',
                                'descricao': 'Uso do Disco',
                                'fkComponente': componente_id,
                                'limiteAtencao': limite_atencao,
                                'limiteCritico': limite_critico,
                                'funcaoPython': 'psutil.disk_usage("/").percent' 
                            })
                        print("Configuração de uso do disco adicionada.")
                    except ValueError:
                        print("Entrada inválida para os limites. Por favor, digite um número.")
                else:
                    print("Opção inválida para disco.")

            elif componente_tipo == 'GPU':
                # Configuração para GPU
                print("\n--- Configuração para GPU ---")
                print("1: Uso da GPU (%)")
                print("2: Temperatura da GPU (°C)")
                opcao_gpu = input("Digite o número da opção desejada para GPU: ")

                if opcao_gpu == '1':
                    print("\nConfigurando: Uso da GPU (%)")
                    try:
                        limite_atencao = float(input("Digite o limite de atenção (ex: 70.0): "))
                        limite_critico = float(input("Digite o limite crítico (ex: 90.0): "))
                        configuracoes.append({ 
                                'unidadeMedida': '%',
                                'descricao': 'Uso da GPU ',
                                'fkComponente': componente_id,
                                'limiteAtencao': limite_atencao,
                                'limiteCritico': limite_critico,
                                'funcaoPython': 'round(GPUtil.getGPUs()[numeracao - 1].load * 100, 2)'
                            })
                        print("Configuração de uso da GPU adicionada.")
                    except ValueError:
                        print("Entrada inválida para os limites. Por favor, digite um número.")
                elif opcao_gpu == '2':
                    print("\nConfigurando: Temperatura da GPU (°C)")
                    try:
                        limite_atencao = float(input("Digite o limite de atenção (ex: 60.0): "))
                        limite_critico = float(input("Digite o limite crítico (ex: 90.0): "))
                        configuracoes.append({ 
                                'unidadeMedida': 'ºC',
                                'descricao': 'Temperatura da GPU',
                                'fkComponente': componente_id,
                                'limiteAtencao': limite_atencao,
                                'limiteCritico': limite_critico,
                                'funcaoPython': 'GPUtil.getGPUs()[componente_numeracao - 1].temperature'
                            })
                        print("Configuração de temperatura da GPU adicionada.")
                    except ValueError:
                        print("Entrada inválida para os limites. Por favor, digite um número.")
                else:
                    print("Opção inválida para GPU.")

        print("\n--- Configurações de monitoramento escolhidas ---")

        # for config in configuracoes:
        print(configuracoes)


        post_configuracoes_monitoramento(configuracoes)    

def init() -> None:
    '''
        Iniciar a aplicação visual para mostrar opções do usuário (monitoramento ou sair), assim começando o processo de captura ou finalizando a aplicação.

        params:
            - None
        return:
            - None
    '''
    
    # Menu de pções para o usuário:
    print("\n" + "╔" + "═" * 38 + "╗")
    print("║ 🛠️  MENU DE AÇÕES DO MONITORAMENTO 🛠️  ║")
    print("╚" + "═" * 38 + "╝")
    print("  ✏️  Digite a opção desejada para continuar:\n")
    print("  ┌" + "─" * 46 + "┐")
    print("  │ 1️⃣  Cadastrar servidor, componentes e config. │")
    print("  │ 2️⃣  Iniciar monitoramento                     │")
    print("  └" + "─" * 46 + "┘\n")

    while True:
        opt = input("👉  Digite sua opção: ")

        if opt == "2":
            try:
                captura()                  
            except Exception as error:
                if error.args[0] == 1452:
                    print("\033[1;31m Encerrando captura: \033[0m Este servidor não está cadastrado em nosso sistema.")
                else:
                    print(error)
            # break
            
        elif opt == "1":
            # cadastrar_servidor()
            # cadastrar_componente()
            configurar_monitoramento()
        else:
            print("⚠️ Opção inválida. Por favor, digite 1 ou 2.")

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