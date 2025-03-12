import HardwareData
import time
from dbConnection import cursor as mysql, connection

def company_data():
    print("\n 🔑 Antes de continuar, precisamos validar sua identidade...")

    while True:
        idEmpresa = input("Insira o id da sua empresa, o ID pode ser visualizado no nosso site. Digite aqui: ")

        if not idEmpresa.isdecimal():
            print("O ID é númerico.")

        else:
            return idEmpresa



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


    # Validando identidade do usuário:
    idEmpresa = company_data()

    # Verificando servidor no banco de dados:
    print("\n⏳ Comparando informações com o banco de dados...")


    # Menu de pções para o usuário:
    print("🔧 Menu de Ações:")
    print("✏️  Digite a opção desejada para continuar:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("1  Iniciar monitoramento")
    print("2  Sair")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    while True:
        opt = input("Escolha uma opção: ")

        if not opt.isdecimal():
            print("A opção deve ser um numero")
        elif int(opt) == 1:
            monitoring(system_info, cpu_info, ram_info, gpu_info)
            break
        elif int(opt) == 2:
            exit("Obrigado!")



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



def monitoring(
        system_info: HardwareData.SystemData,
        cpu_info: HardwareData.CPUData,
        ram_info: HardwareData.RAMData,
        gpu_info: HardwareData.GPUData
):
    print("\n⏳ \033[1;34mCapturando informações de hardware... \033[0m\n"
          "🛑 Pressione \033[1;31mESC\033[0m para encerrar a captura.")

    def insert_server_log():
        mysql.execute("INSERT INTO ServerMonitoring (cpuLoad, ramUsed, clock, fkServer) VALUES (%s, %s, %s, %s)", (
            cpu_info.use, ram_info.used, cpu_info.freq, system_info.motherboardUuid
        ))
        connection.commit()

    def insert_gpu_log():
        for gpu in gpu_info.gpus:
            mysql.execute("INSERT INTO GPUMonitoring (GPUload, vramUSed, temperature, fkGPU) VALUES (%s, %s, %s, %s)", (
                round(gpu.load * 100, 2), gpu.memoryUsed, gpu.temperature, gpu.uuid
            ))

        connection.commit()


    while True:
        cpu_info.update()
        ram_info.update()
        gpu_info.update()

        insert_server_log()
        insert_gpu_log()

        time.sleep(2)



init()
