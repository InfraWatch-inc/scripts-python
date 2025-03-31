import os
import time
import psutil
import GPUtil
import platform
import subprocess
import mysql.connector

conexao = mysql.connector.connect(
    host="",
    user="insert-user",
    password="Urubu100#",
    database="infrawatch"
)
cursor = conexao.cursor()

mother_board_uuid = None

windows_sh = ["powershell", "-Command", "Get-WmiObject Win32_BaseBoard ", "| Select-Object -ExpandProperty SerialNumber"]
linux_sh = "sudo dmidecode -s system-uuid"

monitoramento = []
def inicializador():
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

# Pegando o Informações de coleta
 
if mother_board_uuid != None:

    curso.execute("""SELECT servidor.idservidor, componente.componente, componente.numeracao, componente.fkServidor, 
              configuracaoMonitoramento.fkComponete, configuracaoMonitoramento.funcaoPython, configuracaoMonitoramento.descricao FROM servidor JOIN componente 
              ON servidor.idservidor = componente.fkServidor JOIN configuracaoMonitoramento ON
              configuracaoMonitoramento.fkComponete = componente.idComponente 
              WHERE servidor.idservidor = %s""", (mother_board_uuid,))   

    resultado = cursor.fetchall()
    coluna = resultado[(1)]
    numeracao = resultado[(2)]
    funcao = resultado[(5)]
else:
    print("🛑 O servidor não está registrado no banco de...")
    exit("")

monitoramento.append({
            'coluna': coluna,
            'funcao': funcao,
            'numeracao': numeracao
        })

def coletar_dados():
    
    try:
        #newlist = [x for x in fruits if "a" in x]
        #dados = [monitoramento[i].coluna, eval("monitoramento[i].funcao") for i in monitoramento]
        dados = []
        for item in monitoramento:
            coluna = item['coluna']
            funcao = item['funcao']
            numeracao = item['numeracao']
            dados.append({
                'coluna': coluna,
                'funcao': eval(funcao),  
                'numeracao': numeracao
            })

    except Exception as e:
        print(e)

    try:
        gpu_info = GPUtil.getGPUs()
    except Exception as e:
        print(e)

    return dados

def monitoramento():
    while True:
        print("\n⏳ \033[1;34m Capturando informações de hardware... \033[0m\n"
          "🛑 Pressione \033[1;31m CTRL + C \033[0m para encerrar a captura.")
        
        dados_servidor = coletar_dados()

        cursor.execute("INSERT INTO RegistroServidor (usoCPU, usoRAM, clock, fkServidor) VALUES (%s, %s, %s, %s)", (
            dados_servidor.cpu_info.use, dados_servidor.ram_info.used, dados_servidor.cpu_info.freq, dados_servidor.system_info.motherboardUuid
        ))
        conexao.commit()

    
        for gpu in dados_servidor.gpu_info.gpus:
            if gpu.load != gpu.load:
                return

            cursor.execute("INSERT INTO RegistroGPU (usoGPU, usoVRAM, temperatura, fkGPU) VALUES (%s, %s, %s, %s)", (
                round(gpu.load * 100, 2), gpu.memoryUsed, gpu.temperature, gpu.uuid
            ))
        conexao.commit()

        try:
            time.sleep(5)
            os.system('cls' if os.name == 'nt' else 'clear')
        except:
            exit("")

def init():
    print("Iniciando verificação de Hardware... \n")

    dados_servidor = coletar_dados()

    if not mother_board_uuid:
        print("🛑 Verificação de hardware falhou... Não foi possível identificar a placa mãe")
        return
    
    sys = dados_servidor.system_info
    cpu = dados_servidor.cpu_info
    ram = dados_servidor.ram_info
    gpus = dados_servidor.gpu_info

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
                monitoramento()
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
