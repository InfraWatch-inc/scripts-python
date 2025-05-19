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

def extrair_marca(nome_gpu):
    nome_gpu = nome_gpu.strip()
    if nome_gpu.lower().startswith("nvidia"):
        return "NVIDIA", nome_gpu.replace("NVIDIA", "").strip()
    elif nome_gpu.lower().startswith("amd"):
        return "AMD", nome_gpu.replace("AMD", "").strip()
    elif nome_gpu.lower().startswith("intel"):
        return "Intel", nome_gpu.replace("Intel", "").strip()
    else:
        return "Desconhecida", nome_gpu

def captura_de_componentes() -> None:
    '''
        Iniciando a captura dos componentes presentes no servidor e posteriomente cadastrando os mesmos no banco.

    '''
    print("Estou mostrando numero do servidor que sera cadastrado os componentes", globais['ID_SERVDIDOR'])
    
   
    infoCPU = cpuinfo.get_cpu_info()

    print (infoCPU['brand_raw']) # Captura do Modelo da cpu
    print (infoCPU['vendor_id_raw']) # Captura o Vendedor/Marca da cpu
    
    teste = ['NVIDIA RTX A6000',
    'NVIDIA GeForce RTX 3090',
    'NVIDIA GeForce RTX 2080 Ti', 
    'a']

    infoGPU = GPUtil.getGPUs()
    
    for i, nome in enumerate(teste, start=1):
        marca, modelo = extrair_marca(nome)
        print(f"{i}: Marca: {marca} | Modelo: {modelo}")
        componentes['fkServidor']    



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