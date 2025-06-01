import random
from datetime import datetime, timedelta

# Função para gerar o script SQL com um único INSERT
def gerar_script_sql(data_inicio, data_fim):
    # Inicializando a lista para armazenar os valores dos inserts
    alertas_values = []

    current_date = data_inicio
    
    # Loop sobre o intervalo de datas
    while current_date <= data_fim:
        # Escolher aleatoriamente o tipo de alerta: Disco ou RAM
        tipo_alerta = random.choice(['Disco', 'RAM'])
        
        # Gerar horário aleatório baseado nos períodos
        periodo = random.choices(['Noturno', 'Manha', 'Tarde'], [0.6, 0.2, 0.2])[0]
        
        if periodo == 'Noturno':
            hora = random.randint(0, 5)  # 00:00 a 05:59
        elif periodo == 'Manha':
            hora = random.randint(6, 11)  # 06:00 a 11:59
        else:
            hora = random.randint(12, 17)  # 12:00 a 17:59
            
        minuto = random.randint(0, 59)
        segundo = random.randint(0, 59)

        horario_alerta = f"{str(hora).zfill(2)}:{str(minuto).zfill(2)}:{str(segundo).zfill(2)}"
        
        # Gerar um valor de fkConfiguracaoMonitoramento aleatório entre 6, 8, e 13
        fk_configuracao_monitoramento = random.choice([8, 20, 18])
        
        # Gerar valor do alerta e nível (agora apenas 1 para Moderado ou 2 para Crítico)
        nivel = random.choice([1, 2])  # Nível do alerta (1: Moderado, 2: Crítico)
        valor = round(random.uniform(30, 90), 2)  # Valor de uso (30 a 90)

        # Adicionando o alerta
        alertas_values.append(f"({nivel}, '{current_date.strftime('%Y-%m-%d')} {horario_alerta}', {valor}, {fk_configuracao_monitoramento})")
        
        # Avançando para o próximo dia
        current_date += timedelta(days=1)
    
    # Gerando o insert final para a tabela Alerta
    alertas_insert = f"INSERT INTO Alerta (nivel, dataHora, valor, fkConfiguracaoMonitoramento) VALUES\n" + ",\n".join(alertas_values) + ";\n"

    # Escrevendo no arquivo SQL
    with open('inserts_alertas.sql', 'w') as file:
        file.write(alertas_insert)

    print("Script SQL gerado com sucesso! O arquivo 'inserts_alertas.sql' foi criado.")

# Definindo as datas de início e fim
data_inicio = datetime(2024, 12, 1) 
data_fim = datetime(2025, 5, 29) 

# Gerar o script SQL
gerar_script_sql(data_inicio, data_fim)
