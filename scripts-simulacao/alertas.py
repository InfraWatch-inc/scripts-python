import mysql.connector
import random
from datetime import datetime, timedelta

# Configurações do banco (ajuste conforme seu ambiente)
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
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

for i in range(total_alertas):
    data_alerta = inicio + timedelta(days=i//2, hours=random.randint(0, 23), minutes=random.randint(0, 59))

    # Selecionar aleatoriamente uma configuração de monitoramento
    conf = random.choice(configuracoes)
    limite_atencao = conf['limiteAtencao']
    limite_critico = conf['limiteCritico']
    id_config = conf['idConfiguracaoMonitoramento']

    # Gerar valor de alerta: 50% chance de ser crítico
    nivel = random.choice([1, 2])
    if nivel == 1:
        valor = round(random.uniform(limite_atencao + 0.1, limite_critico - 0.1), 2)
    else:
        valor = round(random.uniform(limite_critico + 0.1, limite_critico + 30.0), 2)

    # Inserir alerta
    cursor.execute("""
        INSERT INTO Alerta (nivel, dataHora, valor, fkConfiguracaoMonitoramento)
        VALUES (%s, %s, %s, %s)
    """, (nivel, data_alerta, valor, id_config))
    id_alerta = cursor.lastrowid

    # Simular processo vinculado ao alerta
    nome_processo = random.choice(processos_validos)
    uso_cpu = round(random.uniform(10, 95), 2)
    uso_gpu = round(random.uniform(5, 90), 2)
    uso_ram = round(random.uniform(500, 16000), 2)  # em MB

    id_servidor = random.choice(servidores)

    cursor.execute("""
        INSERT INTO Processo (nomeProcesso, usoCpu, usoGpu, usoRam, fkAlerta, fkServidor, dataHora)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (nome_processo, uso_cpu, uso_gpu, uso_ram, id_alerta, id_servidor, data_alerta))

    if i % 30 == 0:
        print(f"{i} alertas inseridos...")

# Commit e fechar conexão
conn.commit()
cursor.close()
conn.close()
print("✅ Dados simulados com sucesso!")
