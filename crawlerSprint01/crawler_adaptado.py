import os
import time
import psutil
import GPUtil
import platform
import subprocess
import mysql.connector

connection = mysql.connector.connect(
    host="",
    user="insert-user",
    password="Urubu100#",
    database="infrawatch"
)
cursor = connection.cursor()

mother_board_uuid = None

windows_sh = ["powershell", "-Command", "Get-WmiObject Win32_BaseBoard ", "| Select-Object -ExpandProperty SerialNumber"]
linux_sh = "sudo dmidecode -s system-uuid"

def collect_data():
    try:
        system_info = {
            'SO': platform.system(),
            'version': platform.version(),
            'architecture': platform.architecture()[0]
        }
    except Exception as e:
        print(e)

    try:
        sh = windows_sh if system_info.SO == "Windows" else linux_sh
        mother_board_uuid = subprocess.check_output(sh, shell=True).decode().strip()
    except subprocess.SubprocessError as e:
        print(e)

    try:
        cpu_info = {
            'cores': psutil.cpu_count(logical=False),
            'threads': psutil.cpu_count(logical=True),
            'times': psutil.cpu_times(),
            'freq': psutil.cpu_freq().current,
            'use': psutil.cpu_percent()
        }
    except Exception as e:
        print(e)

    try:
        ram_info = {
            'total':(psutil.virtual_memory().total / (1024 ** 3)).__ceil__(),
            'used':(psutil.virtual_memory().used / (1024 ** 3)).__ceil__(),
            'free':(psutil.virtual_memory().free / (1024 ** 3)).__ceil__(),
            'totalSwap':(psutil.swap_memory().total / (1024 ** 3)).__ceil__(),
            'UsedSwap':(psutil.swap_memory().used / (1024 ** 3)).__ceil__(),
            'freeSwap':(psutil.swap_memory().free / (1024 ** 3)).__ceil__()
        }
    except Exception as e:
        print(e)

    try:
        gpu_info = GPUtil.getGPUs()
    except Exception as e:
        print(e)

    return {system_info, ram_info, cpu_info, gpu_info}

def monitoring():
    while True:
        print("\n⏳ \033[1;34m Capturando informações de hardware... \033[0m\n"
          "🛑 Pressione \033[1;31m CTRL + C \033[0m para encerrar a captura.")
        
        server_data = collect_data()

        cursor.execute("INSERT INTO RegistroServidor (usoCPU, usoRAM, clock, fkServidor) VALUES (%s, %s, %s, %s)", (
            server_data.cpu_info.use, server_data.ram_info.used, server_data.cpu_info.freq, server_data.system_info.motherboardUuid
        ))
        connection.commit()

    
        for gpu in server_data.gpu_info.gpus:
            if gpu.load != gpu.load:
                return

            cursor.execute("INSERT INTO RegistroGPU (usoGPU, usoVRAM, temperatura, fkGPU) VALUES (%s, %s, %s, %s)", (
                round(gpu.load * 100, 2), gpu.memoryUsed, gpu.temperature, gpu.uuid
            ))
        connection.commit()

        try:
            time.sleep(5)
            os.system('cls' if os.name == 'nt' else 'clear')
        except:
            exit("")

def init():
    print("Iniciando verificação de Hardware... \n")

    server_data = collect_data()

    if not mother_board_uuid:
        print("🛑 Verificação de hardware falhou... Não foi possível identificar a placa mãe")
        return
    
    sys = server_data.system_info
    cpu = server_data.cpu_info
    ram = server_data.ram_info
    gpus = server_data.gpu_info

    print(f"⚙️ Sistema operacional: {f"{sys.SO} {sys.architecture} {sys.version}"}")
    print(f"🔑 UUID da placa mãe: {mother_board_uuid}")
    print(f"🧠 Núcleos do processador: {cpu.cores}")
    print(f"⚙️ Threads do processador: {cpu.threads}")
    print(f"💾 Memória instalada: {ram.total}Gb")
    print(f"🔄 Memória Swap: {ram.totalSwap}Gb")

    for gpu in gpus.gpus:
        print(f"🖥️ Placa de vídeo: {gpu.name}")

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
                monitoring()
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
