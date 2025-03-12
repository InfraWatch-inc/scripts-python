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

    database_server_verify(system_info, cpu_info, gpu_info, id_empresa)
    time.sleep(2)


def database_server_verify(
        system_info: HardwareData.SystemData,
        cpu_info: HardwareData.CPUData,
        gpu_info: HardwareData.GPUData,
        idEmpresa: int
):
    mysql.execute("SELECT * FROM Servidor WHERE uuidPlacaMae = %s", (system_info.motherboardUuid,))
    verify_motherboard_uuid = mysql.fetchone()

    if not verify_motherboard_uuid:
        while True:
            print("\033[1;31m⚠️  Esse servidor não está cadastrado!\033[0m\n")
            print("\033[1;34m➤ Deseja cadastrá-lo?\033[0m")
            print("\033[1;32m[1] Sim\033[0m")
            print("\033[1;31m[2] Não\033[0m")
            print("\n\033[1;33m🔸 Caso escolha 'Não', o programa será encerrado.\033[0m")
            opt = input("Digite sua escolha: ")

            if opt != "1" and opt != "2":
                print("\033[1;31m⚠️  A opção precisa ser um número entre 1 e 2...\033[0m")
            elif opt == "2":
                exit()
            else:
                break


        tag_name = input("\033[1;36m🔖 Digite um alias para o seu servidor (Tag Name): \033[0m")
        tipo_servidor = ""

        while True:
            print("\033[1;34m🖥️  Qual é o tipo de servidor?\033[0m\n")
            print("\033[1;36m☁️  [1] Nuvem\033[0m")
            print("\033[1;33m🏢 [2] Físico (On-Premise)\033[0m")
            opt = input("Digite sua escolha: ")

            if opt == "1":
                tipo_servidor = "nuvem"
                break
            elif opt == "2":
                tipo_servidor = "fisico"
                break
            else:
                print("Opção inválida")

        print(
            "\033[1;34mℹ️  O servidor será cadastrado e identificado no sistema com a Tag Name inserida anteriormente.\033[0m\n"
            "\033[1;36m💡 Para uma identificação mais precisa, caso o servidor seja em nuvem,\n"
            "   o ID da instância poderá ser adicionado em nosso sistema web.\033[0m")

        mysql.execute("INSERT INTO Servidor (tagName, tipo, uuidPlacaMae, SO, fkEmpresa) VALUE (%s, %s, %s, %s, %s)",
                      (tag_name, tipo_servidor, system_info.motherboardUuid, system_info.SO, idEmpresa))
        connection.commit()
        servidor_id = mysql.lastrowid

        mysql.execute("INSERT INTO Componente (fkServidor, nome, tipoComponente) VALUES "
                      "(%s, %s, %s),"
                      "(%s, %s, %s);",
                      (servidor_id, cpu_info.cpu_model, "CPU",
                       servidor_id, "Memoria", "RAM"))


        for gpu in gpu_info.gpus:
            mysql.execute("INSERT INTO Componente (fkServidor, nome, descricao, tipoComponente) VALUES (%s, %s, %s, %s);",
                          (servidor_id, gpu.name, gpu.uuid, "GPU"))

        connection.commit()


        print("\033[1;32m✅ Hardware escaneado e salvo no banco de dados com sucesso.\033[0m")
        return

    print("\033[1;33m⚠️ O servidor já está cadastrado...\033[0m")


init()
