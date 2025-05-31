import mysql.connector
import random
from datetime import datetime, timedelta
import json

# Configurações do banco (ajuste conforme seu ambiente)
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'GTech0100#@',
    'database': 'infrawatch'
}

# Lista de processos possíveis
processos_validos = ['Blender', 'Maya', 'Paint 3D']

# Conectar ao banco
conn = mysql.connector.connect(**config)
cursor = conn.cursor(dictionary=True)

# Buscar configurações válidas para monitoramento
cursor.execute("SELECT * FROM ConfiguracaoMonitoramento")
configuracoes = cursor.fetchall()

# Buscar servidores disponíveis
cursor.execute("SELECT idServidor FROM Servidor")
servidores = [row['idServidor'] for row in cursor.fetchall()]

# Simular 360 alertas nos últimos 6 meses
hoje = datetime.now()
inicio = hoje - timedelta(days=180)
total_alertas = 360

# Lista para armazenar os dados em formato SQL
valores_alertas = []
valores_processos = []

for i in range(total_alertas):
    # Ajustando para que o período noturno tenha mais chance
    if random.random() < 0.6:  # 60% chance de gerar alerta no período noturno (18h - 6h)
        hora_alerta = random.randint(18, 23) if random.random() < 0.5 else random.randint(0, 7)
    else:  # 40% chance de gerar alerta durante o dia
        hora_alerta = random.randint(7, 17)

    data_alerta = inicio + timedelta(days=i//2, hours=hora_alerta, minutes=random.randint(0, 59))

    # Selecionar aleatoriamente uma configuração de monitoramento
    conf = random.choice(configuracoes)
    limite_atencao = conf['limiteAtencao']
    limite_critico = conf['limiteCritico']
    id_config = conf['idConfiguracaoMonitoramento']

    # Gerar valor de alerta: 50% chance de ser crítico
    nivel = random.choice([1, 2])  # 1 = Atenção, 2 = Crítico
    if nivel == 1:
        valor = round(random.uniform(limite_atencao + 0.1, limite_critico - 0.1), 2)
        nome_processo = "Blender"  # Processo de atenção
    else:
        valor = round(random.uniform(limite_critico + 0.1, limite_critico + 30.0), 2)
        nome_processo = "Paint 3D"  # Processo crítico

    # Adicionar os valores de alerta à lista
    valores_alertas.append(f"({nivel}, '{data_alerta.strftime('%Y-%m-%d %H:%M:%S')}', {valor}, {id_config})")

    # Gerar um id de alerta fictício
    id_alerta = i + 1

    # Simular processo vinculado ao alerta
    uso_cpu = round(random.uniform(10, 95), 2)
    uso_gpu = round(random.uniform(5, 90), 2)
    uso_disco = round(random.uniform(5, 90), 2)
    uso_ram = round(random.uniform(55, 98), 2)  # Componente RAM: entre 55% e 98%

    id_servidor = random.choice(servidores)

    # Adicionar os valores de processo à lista
    valores_processos.append(f"('{nome_processo}', {uso_cpu}, {uso_gpu}, {uso_ram}, {id_alerta}, {id_servidor}, '{data_alerta.strftime('%Y-%m-%d %H:%M:%S')}')")

    if i % 30 == 0:
        print(f"{i} alertas inseridos...")

# Gerar o arquivo SQL com um único INSERT INTO
with open('inserts.sql', 'w') as f:
    # Gerar o comando INSERT para Alerta
    f.write("INSERT INTO Alerta (nivel, dataHora, valor, fkConfiguracaoMonitoramento) VALUES\n")
    f.write(",\n".join(valores_alertas) + ";\n\n")
    
    # Gerar o comando INSERT para Processo
    f.write("INSERT INTO Processo (nomeProcesso, usoCpu, usoGpu, usoRam, fkAlerta, fkServidor, dataHora) VALUES\n")
    f.write(",\n".join(valores_processos) + ";\n")

# Commit e fechar conexão
conn.commit()
cursor.close()
conn.close()

print("✅ Dados simulados com sucesso!")
