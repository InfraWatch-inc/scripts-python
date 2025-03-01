import GPUtil
import psutil
from mysql.connector import connection
import time
import subprocess
import platform

mydb = connection.MySQLConnection(
    host="localhost",
    user="infrawatch-insert",
    password="Urubu100",
    database="monitor"
)

if mydb.is_connected() == True:
    print('Conectado ao Banco de Dados')

cursor = mydb.cursor();

def get_mother_board_id():
    try:
        so = platform.system()

        windows_sh = ["powershell", "-Command", "Get-WmiObject Win32_BaseBoard "
                                                "| Select-Object -ExpandProperty SerialNumber"]

        linux_sh = "sudo dmidecode -s system-uuid"

        sh = windows_sh if so == "Windows" else linux_sh

        return subprocess.check_output(sh, shell=True).decode().strip()

    except subprocess.SubprocessError as e:
       exit("Erro ao capturar id da placa mãe... Entre em contato como suporte da InfraWatch")

fkServer = get_mother_board_id()
print(fkServer)

getGpus = GPUtil.getGPUs()


contador = 0

while True:
    cpu = psutil.cpu_percent(interval=1)
    clock = psutil.cpu_freq().current
    memoriaUsado = int(psutil.virtual_memory().used / (1024 ** 2)) # Convertendo Bytes para MegaBytes
    discoUsado = int(psutil.disk_usage('C:\\').used/ (1024 ** 2)) # Convertendo Bytes para MegaBytes

    sql = "INSERT INTO ServerLog (cpuLoad, ramUsed, discoUsed, clock, fkServer) VALUES (%s, %s, %s,%s,%s)"
    valores = (cpu, memoriaUsado, discoUsado, clock, fkServer)


    if len(getGpus) > 0:
        gpu = GPUtil.getGPUs()[0]
        gpuUuid = gpu.uuid
        gpuMemoryUsed = gpu.memoryUsed
        gpuLoad = gpu.load * 100 # Converte o load para porcentagem (inteiro de 0 até 100)
        gpuTemperature = gpu.temperature

        sql_gpu = "INSERT INTO GPULog (gpuLoad, usedMemory, temperature, fkGPU) VALUES (%s,%s,%s,%s)"
        valores_gpu = (gpuLoad, gpuMemoryUsed, gpuTemperature, gpuUuid)

        cursor.execute(sql_gpu, valores_gpu)

    cursor.execute(sql, valores)

    mydb.commit()

    contador += 1

    print(f"{contador} - Registros armazenados no banco de dados com sucesso...")
    time.sleep(2) 
    