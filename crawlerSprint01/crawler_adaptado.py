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
        so =  platform.system()
    except Exception as e:
        print(e)

    try:
        sh = windows_sh if so == "Windows" else linux_sh
        mother_board_uuid = subprocess.check_output(sh, shell=True).decode().strip()
    except subprocess.SubprocessError as e:
        print(e)

# Pegando o Informações de coleta
 
    if mother_board_uuid != None:

        cursor.execute("""SELECT servidor.idservidor, componente.componente, componente.numeracao, componente.fkServidor, 
              configuracaoMonitoramento.fkComponete, configuracaoMonitoramento.funcaoPython, configuracaoMonitoramento.descricao FROM servidor JOIN componente 
              ON servidor.idservidor = componente.fkServidor JOIN configuracaoMonitoramento ON
              configuracaoMonitoramento.fkComponete = componente.idComponente 
              WHERE servidor.idservidor = %s""", (mother_board_uuid,))   
# fazer for para pegar todos os componentes
        resultado = cursor.fetchall()
        coluna = resultado[(1)]
        numeracao = resultado[(2)]
        funcao = resultado[(5)]
            
        monitoramento.append({
                    'coluna': coluna,
                    'funcao': funcao,
                    'numeracao': numeracao
                })
        init()
    else:
        print("🛑 O servidor não está registrado no banco de dados...")
        exit("")

def coletar_dados():
    
    try:
        #newlist = [x for x in fruits if "a" in x]
        #dados = [monitoramento[i].coluna, eval("monitoramento[i].funcao") for i in monitoramento]
        dados = []
        for item in monitoramento:
            funcao = item['funcao']
            numeracao = item['numeracao']
            dados.append(eval(funcao))

    except Exception as e:
        print(e)

    return dados

def captura():
    while True:
        print("\n⏳ \033[1;34m Capturando informações de hardware... \033[0m\n"
          "🛑 Pressione \033[1;31m CTRL + C \033[0m para encerrar a captura.")
        
        dados_servidor = coletar_dados()

            # Adpatar de acordo com a regra de negocio relacional

        cursor.execute("INSERT INTO RegistroServidor (usoCPU, usoRAM, clock, fkServidor) VALUES (%s, %s, %s, %s)", (
            dados_servidor.cpu_info.use, dados_servidor.ram_info.used, dados_servidor.cpu_info.freq, dados_servidor.system_info.motherboardUuid
        ))
        conexao.commit()
        try:
            time.sleep(600)
            os.system('cls' if os.name == 'nt' else 'clear')
        except:
            exit("")

def init():
    print("Iniciando verificação de Hardware... \n")

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
                captura()
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
    inicializador()
