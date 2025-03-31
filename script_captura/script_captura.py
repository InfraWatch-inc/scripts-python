import HardwareData
import time
from dbConnection import cursor as mysql, connection

def init():
    print("Iniciando verificação de Hardware... \n")

    system_info = HardwareData.SystemData()
    cpu_info = HardwareData.CPUData()
    ram_info = HardwareData.RAMData()
    gpu_info = HardwareData.GPUData()

    if not system_info.motherboardUuid:
        print("🛑 Verificação de hardware falhou... Não foi possível identificar a placa mãe")
        return

    print(f"⚙️ Sistema operacional: {system_info}")
    print(f"🔑 UUID da placa mãe: {system_info.motherboardUuid}")
    print(f"🧠 Núcleos do processador: {cpu_info.cores}")
    print(f"⚙️ Threads do processador: {cpu_info.threads}")
    print(f"💾 Memória instalada: {ram_info.total}Gb")
    print(f"🔄 Memória Swap: {ram_info.totalSwap}Gb")

    for gpu in gpu_info.gpus:
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
                monitoring(system_info, cpu_info, ram_info, gpu_info)

            except Exception as error:
                if error.args[0] == 1452:
                    print("\033[1;31mEncerrando captura:\033[0m Este servidor não está cadastrado em nosso sistema.")
                else:
                    print(error)
            break
            
        elif opt == "2":
            exit(f"Até a próxima!")
        else:
            print("Opção inválida!")

def monitoring(
        system_info: HardwareData.SystemData,
        cpu_info: HardwareData.CPUData,
        ram_info: HardwareData.RAMData,
        gpu_info: HardwareData.GPUData):
    print("\n⏳ \033[1;34mCapturando informações de hardware... \033[0m\n"
          "🛑 Pressione \033[1;31mCTRL + C\033[0m para encerrar a captura.")

    def insert_server_log():
        mysql.execute("INSERT INTO RegistroServidor (usoCPU, usoRAM, clock, fkServidor) VALUES (%s, %s, %s, %s)", (
            cpu_info.use, ram_info.used, cpu_info.freq, system_info.motherboardUuid
        ))
        connection.commit()

    def insert_gpu_log():
        for gpu in gpu_info.gpus:
            if gpu.load != gpu.load:
                return
            
            mysql.execute("INSERT INTO RegistroGPU (usoGPU, usoVRAM, temperatura, fkGPU) VALUES (%s, %s, %s, %s)", (
                round(gpu.load * 100, 2), gpu.memoryUsed, gpu.temperature, gpu.uuid
            ))

        connection.commit()


    while True:
        cpu_info.update()
        ram_info.update()
        gpu_info.update()

        insert_server_log()
        insert_gpu_log()


        try:
            time.sleep(2)
        except:
            print("")
            exit()

if __name__ == "__main__":
    init()
