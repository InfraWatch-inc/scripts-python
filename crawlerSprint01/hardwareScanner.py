from crawlerV2 import HardwareData
import time
from crawlerV2.dbConnection import cursor as mysql, connection


def company_data():
    print("\n 🔑 Antes de continuar, precisamos validar sua identidade...")

    while True:
        id_empresa = input("\033[1;34m🏢 Insira o ID da sua empresa.\n"
                           "🔹 O ID pode ser visualizado no nosso site.\n"
                           "✍️  Digite aqui: \033[0m")

        if not id_empresa.isdecimal():
            print("O ID é númerico.")

        else:
            return int(id_empresa)


def init():
    print("Iniciando verificação de Hardware... \n")

    system_info = HardwareData.SystemData()
    cpu_info = HardwareData.CPUData()
    ram_info = HardwareData.RAMData()
    gpu_info = HardwareData.GPUData()

    print(f"⚙️ Sistema operacional: {system_info}")
    print(f"🔑 UUID da placa mãe: {system_info.motherboardUuid}")
    print(f"🧠 Núcleos do processador: {cpu_info.cores}")
    print(f"⚙️ Threads do processador: {cpu_info.threads}")
    print(f"💾 Memória instalada: {ram_info.total}Gb")
    print(f"🔄 Memória Swap: {ram_info.totalSwap}Gb")

    for gpu in gpu_info.gpus:
        print(f"🖥️ Placa de vídeo: {gpu.name}")


    id_empresa = company_data()

    # Verificando servidor no banco de dados:
    print("\n⏳ Comparando informações com o banco de dados...")

    database_server_verify(system_info, cpu_info, ram_info, id_empresa)
    time.sleep(2)
    database_gpu_verify(gpu_info, system_info)
    time.sleep(1)

def database_server_verify(
        system_info: HardwareData.SystemData,
        cpu_info: HardwareData.CPUData,
        ram_info: HardwareData.RAMData,
        company: int
):
    mysql.execute("SELECT * FROM Server WHERE uuidMotherboard = %s", (system_info.motherboardUuid,))
    verify_motherboard_uuid = mysql.fetchone()

    if verify_motherboard_uuid:
        uuid, cores, threads, ram, so, version = verify_motherboard_uuid[:6]

        if cores != cpu_info.cores or threads != cpu_info.threads or ram != ram_info.total or so != system_info.SO\
                or version != system_info.version:

            mysql.execute("UPDATE Server SET cpuCores = %s, cpuThreads = %s, RAM = %s, SO = %s, version = %s",
                          (cpu_info.cores, cpu_info.threads, ram_info.total, system_info.SO, system_info.version))
            connection.commit()

            print("\n🆕 Hardware novo detectado. A base de dados foi atualizada.")

        print("\n✅ Servidor existente no banco de dados e validado com sucesso.")

    else:
        mysql.execute("INSERT INTO Server VALUES (%s, %s, %s, %s, %s, %s, %s)",
                      (system_info.motherboardUuid, cpu_info.cores, cpu_info.threads, ram_info.total, system_info.SO,
                       system_info.version, company))
        connection.commit()

        print("\n✅ Servidor novo registrado com sucesso...")



def database_gpu_verify(
        gpu_info: HardwareData.GPUData,
        system_info: HardwareData.SystemData
):
    # Verificando placas de vídeo
    for gpu in gpu_info.gpus:
        if gpu.load == 'nan' or gpu.temperature == 'nan' or gpu.memoryTotal == 'nan':
            return

        mysql.execute("SELECT * FROM GPU WHERE uuid = %s", (gpu.uuid,))
        result = mysql.fetchone()

        if result:
            if result[3] != system_info.motherboardUuid:
                mysql.execute("UPDATE GPU SET fkServer = %s WHERE uuid = %s", (system_info.motherboardUuid, gpu.uuid))
                print(f"⚠️ Placa de vídeo {gpu.name} transferida de servidor. \n")

            print(f"✅ Placa de video {gpu.name} verificada e operante. \n")

        else:
            mysql.execute("INSERT INTO GPU VALUES (%s, %s, %s, %s)",
                              (gpu.uuid, gpu.name, gpu.memoryTotal, system_info.motherboardUuid))
            print(f"✅ Placa de video {gpu.name} cadastrada com sucesso. \n")

        connection.commit()

init()
