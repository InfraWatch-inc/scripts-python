import os
import json
import time
import psutil
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

INTERVALO = 60  # Intervalo padrão de 60 segundos
FUSO_HORARIO = timezone(timedelta(hours=-3))

def obter_informacoes_sistema():
    info = {
        "cpu": psutil.cpu_percent(interval=1),
        "temperatura": psutil.sensors_temperatures().get("coretemp",[])[0].current,
        "memoria": psutil.virtual_memory().percent,
        "disco": psutil.disk_usage('/').percent,
        "tempo_ativo": str(datetime.now(timezone.utc) - datetime.fromtimestamp(psutil.boot_time(), timezone.utc)),
        "data_hora": datetime.now(FUSO_HORARIO).strftime('%Y-%m-%d %H:%M:%S')
    }
    return info

def monitorar():
    while True:
        data = obter_informacoes_sistema()
        try:
            response = requests.post(
                f'{os.getenv("WEB_URL")}/monitoramento/instancia',
                headers={"Content-Type": "application/json"},
                data=json.dumps(data)
            )

            if response.status_code == 200:
                print(f"Dados enviados com sucesso: {data}")
            else:
                print(f"Erro ao enviar dados: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"Erro de conexão: {e}")

        time.sleep(INTERVALO)

if __name__ == "__main__":
    load_dotenv()

    monitorar()
