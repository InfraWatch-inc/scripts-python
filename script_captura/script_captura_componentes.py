import os
import time
import psutil
import GPUtil
import pynvml
import wmi
import requests
import platform
import subprocess
import cpuinfo
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

globais = {
    'COMANDOS_WINDOWS': ["powershell", "-Command", "Get-WmiObject Win32_BaseBoard ", "| Select-Object -ExpandProperty SerialNumber"],
    'COMANDOS_LINUX': "sudo dmidecode -s system-uuid",
    'UUID': None, 
    'ID_SERVDIDOR': None,
    'IS_GPU': False
}

componentes = []

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
    print("Estou mostrando numero do servidor que sera cadastrado os componentes", globais['ID_SERVDIDOR'])
    
   # ===================================== CPU =====================================
    infoCPU = cpuinfo.get_cpu_info()
    infoCPUespecifico = infoCPU['brand_raw'].split()[0] # Captura do Modelo da cpu
    modeloCPU = infoCPU['brand_raw']

    # Pego apenas a cpu principal do servidor, não encontrei maneira no python de capturar marcas de CPUs diferentes caso houver    
    marcaCPU = extrair_marca_cpu(infoCPUespecifico)

    print(f"1: Marca: {marcaCPU} | Modelo: {modeloCPU}")

    componentes.append({"fkServidor": globais['ID_SERVDIDOR'],
                "componentes":[{"componente": "CPU", 
                "marca": marcaCPU,
                "numeracao": 1,
                "modelo":modeloCPU}]}) 
        
    print(componentes)

    # ===================================== GPU =====================================
    infoGPU = GPUtil.getGPUs()
  
    for i, gpu in enumerate(infoGPU, start=1):
        marcaGPU, modeloGPU = extrair_marca_gpu(gpu.name)

        print(f"{i}: Marca: {marcaGPU} | Modelo: {modeloGPU}")

        componentes.append({"fkServidor": globais['ID_SERVDIDOR'],
                    "componentes":[{"componente": "GPU", 
                    "marca": marcaGPU,
                    "numeracao": i,
                    "modelo":modeloGPU}]}) 
    print("Componentes FINAL",componentes)

    # ===================================== RAM =====================================

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
        res = requests.get(f"{os.getenv('WEB_URL')}/monitoramento/{globais['UUID']}")

        resultado = res.json()

        if res.status_code != 200:
            print("🛑 O servidor não está registrado no Banco de Dados...")
            exit("")

        globais['ID_SERVDIDOR'] = resultado[0]['idServidor']
        print(globais)
        print(globais['ID_SERVDIDOR'])
        captura_de_componentes()
        return globais['ID_SERVDIDOR']
    else:
        print("🛑 O servidor não está registrado no Banco de Dados...")
        exit("")


if __name__ == "__main__":
    inicializador()