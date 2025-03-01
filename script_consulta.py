import mysql.connector
import time

mydb = mysql.connector.connect(
    host="10.18.32.14",
    user="infrawatch-select",
    password="Urubu100",  # Não esqueça de preencher com a senha do banco utilizado
    database="monitor"
)

if mydb.is_connected():
    print('Conectado ao Banco de Dados.\n')

cursor = mydb.cursor()

def consultar_server_log(servidor_escolhido):
    print("Escolha o componente que deseja monitorar: \n")
    print("1 - CPU\n")
    print("2 - RAM\n")
    print("3 - DISCO\n")

    opcao = int(input("Digite sua opção: "))

    print("Escolha a métrica que deseja monitorar: \n")
    print("1 - Bytes\n")
    print("2 - Porcentagem\n")

    metrica = int(input("Digite sua opção: "))

    cursor.execute("SELECT * FROM Server WHERE uuidMotherboard = %s;", (servidor_escolhido,))

    id, CPUcores, CPUthreads, RAMTotal, discoTotal, SO, versao = cursor.fetchone()
    print(id, CPUcores, CPUthreads, RAMTotal, discoTotal, SO, versao)

    try:
        cursor.execute("SELECT AVG(cpuLoad), AVG(ramUsed), AVG(discoUsed), AVG(clock) FROM ServerLog WHERE fkServer = %s GROUP BY fkServer;", (servidor_escolhido,))
        resultado = cursor.fetchall()
        print(resultado)
        if resultado:
            print(f"\nLogs do servidor {servidor_escolhido}: \n")
            cpuLoad, ramUsed, discoUsed, clock = resultado[0]

            if opcao == 1:
                # CPU Load
                print(f"\033[1;34mCPU:\033[0m \033[1;33m{cpuLoad:.2f} %\033[0m")
                # Clock Speed
                print(f"\033[1;34mCLOCK:\033[0m \033[1;33m{clock:.2f} MHz\033[0m")

            elif opcao == 2:
                ramFreeBytes = (RAMTotal - ramUsed) 
                ramUsedPercentual = (ramUsed / RAMTotal) * 100
                ramFreePercentual = 100 - ramUsedPercentual

                # RAM Used
                if metrica == 1:
                    # RAM Total, Usada e Livre (em MB)
                    print(f"\033[1;34mRAM Total:\033[0m \033[1;33m{RAMTotal} MB\033[0m")
                    print(f"\033[1;34mRAM Usada:\033[0m \033[1;33m{(ramUsed):.3f} MB\033[0m")
                    print(f"\033[1;34mRAM Livre:\033[0m \033[1;33m{(ramFreeBytes):.3f} MB\033[0m\n")
                    
                elif metrica == 2:
                    # Percentual de RAM Livre e Usada
                    print(f"\033[1;34mPercentual de RAM Livre:\033[0m \033[1;33m{ramFreePercentual:.1f}%\033[0m")
                    print(f"\033[1;34mPercentual de RAM Usada:\033[0m \033[1;33m{ramUsedPercentual:.1f}%\033[0m\n")

            elif opcao == 3:

                discoFreeBytes = (discoTotal - discoUsed) 
                discoUsedPercentual = (discoUsed / discoTotal) * 100
                discoFreePercentual = 100 - discoUsedPercentual
                
                if metrica == 1:

                    # RAM Total, Usada e Livre (em MB)
                    print(f"\033[1;34mArmazenamento Total:\033[0m \033[1;33m{(discoTotal / 1024):.3f} GB\033[0m")
                    print(f"\033[1;34mArmazenamento Usada:\033[0m \033[1;33m{(discoUsed / 1024):.3f} GB\033[0m")
                    print(f"\033[1;34mArmazenamento Livre:\033[0m \033[1;33m{(discoFreeBytes / 1024):.3f} GB\033[0m")
                    
                elif metrica == 2:
                    # Percentual de RAM Livre e Usada
                    print(f"\033[1;34mPercentual de armazenamento Livre:\033[0m \033[1;33m{discoFreePercentual:.1f}%\033[0m")
                    print(f"\033[1;34mPercentual de armazenamento Usada:\033[0m \033[1;33m{discoUsedPercentual:.1f}%\033[0m")
               
        else:
            print(f"Nenhum log encontrado para o servidor {servidor_escolhido}.\n")
    except Exception as e:
        print(f"Erro ao consultar logs do servidor: {e}.\n")

try:
    cursor.execute("SELECT DISTINCT fkServer FROM ServerLog;")
    servidores = cursor.fetchall()

    if not servidores:
        print("Nenhum servidor encontrado na base de dados.")
    else:
        print("Escolha um servidor para consultar os logs: ")
        for i, servidor in enumerate(servidores, 1):
            print(f"{i} - Servidor com ID fkServer = {servidor[0]}.")

        try:
            escolha = int(input("\nDigite o número correspondente ao servidor escolhido: "))
            if 1 <= escolha <= len(servidores):
                servidor_escolhido = servidores[escolha - 1][0]  # Pega o ID do servidor
                consultar_server_log(servidor_escolhido)
            else:
                print("Número de servidor inválido.\n")
        except (ValueError, IndexError):
            print(ValueError, IndexError, "Escolha inválida. Tente novamente.\n")


except Exception as e:
    print(f"Erro ao consultar servidores: {e}. \n")

cursor.close()
mydb.close()
