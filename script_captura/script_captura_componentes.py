import os
import GPUtil
import requests
import platform
import subprocess
import cpuinfo
import json
from dotenv import load_dotenv

load_dotenv()

globais = {
    'COMANDOS_WINDOWS': ["powershell", "-Command", "Get-WmiObject Win32_BaseBoard ", "| Select-Object -ExpandProperty SerialNumber"],
    'COMANDOS_LINUX': "sudo dmidecode -s system-uuid",
    'UUID': None, 
    'ID_SERVDIDOR': None,
    'IS_GPU': False
}

dados = []
def capturar_modelo_disco() -> None:
    try:
        COMANDO_WINDOWS = ["powershell", "-Command", "Get-WmiObject Win32_DiskDrive | Select-Object -ExpandProperty Model"]

        resultado = subprocess.check_output(COMANDO_WINDOWS, shell=True).decode().strip()

        return resultado
    
    except subprocess.SubprocessError as e:
        print(e)

def post_dados(dados) -> None:
    '''

    '''    
    res = requests.post(f"{os.getenv('WEB_URL')}/componente/cadastrar/dados/{globais['ID_SERVDIDOR']}", data=json.dumps(dados), headers={'Content-Type': 'application/json'})

    if res.status_code == 200:
        print("Componentes cadastrados com sucesso!")
    else:
        print("Não cadastrou os dados")

    # print("dados capturados: ", dados)

def extrair_marca_gpu(nome_gpu):
    nome_gpu = nome_gpu.strip()
    if nome_gpu.lower().startswith("nvidia"):
        return "NVIDIA", nome_gpu.replace("NVIDIA", "").strip()
    elif nome_gpu.lower().startswith("amd"):
        return "AMD", nome_gpu.replace("AMD", "").strip()
    elif nome_gpu.lower().startswith("intel"):
        return "Intel", nome_gpu.replace("Intel", "").strip()
    else:
        return "Desconhecida", nome_gpu

def extrair_marca_cpu(nome_cpu):
    nome_cpu = nome_cpu.strip()
    if nome_cpu.lower().startswith("amd"):
        return "AMD"
    elif nome_cpu.lower().startswith("intel"):
        return "Intel"
    else:
        return "Desconhecida"

def captura_de_componentes() -> None:
    '''
        Iniciando a captura dos componentes presentes no servidor e posteriomente cadastrando os mesmos no banco.

    '''
    # print("Estou mostrando numero do servidor que sera cadastrado os componentes", globais['ID_SERVDIDOR'])
    
    componentes = []

# ===================================== CPU =====================================
    infoCPU = cpuinfo.get_cpu_info()
    infoCPUespecifico = infoCPU['brand_raw'].split()[0] # Captura do Modelo da cpu
    modeloCPU = infoCPU['brand_raw']

    # Pego apenas a cpu principal do servidor, não encontrei maneira no python de capturar marcas de CPUs diferentes caso houver    
    marcaCPU = extrair_marca_cpu(infoCPUespecifico)

    # print(f"1: Marca: {marcaCPU} | Modelo: {modeloCPU}")

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

    dados.append({
        "fkServidor": globais['ID_SERVDIDOR'],
        "componentes": componentes
    })

    # print("Componentes FINAL", dados)

    post_dados(dados)
    return dados

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
        res = requests.get(f"{os.getenv('WEB_URL')}/monitoramento/componente/{globais['UUID']}")

        resultado = res.json()
        
        if res.status_code != 200:
            print("🛑 O servidor não está registrado no Banco de Dados... Entre em contato com o suporte!")
            
            exit("")
        
        elif resultado == []:
            print("🛑 O servidor não está registrado no Banco de Dados... Entre em contato com o suporte!")
            exit("")
            # print("1 - Sim")
            # print("2 - Não")

            # optCadastroServ = input("Digite uma opção: ")

            # if optCadastroServ == '1':
            #     print("Realize seu login para cadastrar seu servidor!")
            #     optEmail = input("✏️  Digite seu e-mail: ")
            #     optSenha = input("✏️  Digite sua senha: ")
                
            #     dadosAutenticar = {
            #         "email": optEmail,
            #         "senha": optSenha
            #     }
                
            #     resServ = requests.post(f"{os.getenv('WEB_URL')}/colaboradores/autenticar", data=json.dumps(dadosAutenticar), headers={'Content-Type': 'application/json'})
            #     resultadoServidor = resServ.json()
            #     print("Captura de servidores:", resultadoServidor)

            #     if resServ.status_code == 200:
            #         resultadoServidor = resServ.json()
            #         print("✅ Login bem-sucedido!")
            #         print("Resposta:", resultadoServidor)
            #     else:
            #         print("🛑 Falha ao autenticar. Verifique seu e-mail e senha.")
            #         print("Status:", resServ.status_code)
            #         print("Resposta:", resServ.text)
            #       uuid = coletar_uuid()
            #       res = requests.post(f"{os.getenv('WEB_URL')}/componente/cadastrar/servidor/{uuid}", data=json.dumps(uuid), headers={'Content-Type': 'application/json'})

            # elif optCadastroServ == '2':
            #     print("Servidor não cadastrado!")
            #     return

            # else:
            #     print("Opção inválida!")
            #     inicializador()
            

        globais['ID_SERVDIDOR'] = resultado[0]['idServidor']
        # print(globais)
        # print(globais['ID_SERVDIDOR'])
        captura_de_componentes()
        return globais['ID_SERVDIDOR']
    else:
        print("🛑 O servidor não está registrado no Banco de Dados...")
        exit("")


if __name__ == "__main__":
    inicializador()