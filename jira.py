import requests as r
import json
import time
from datetime import datetime


id_projeto = "10001"

url = "https://plcvision.atlassian.net/rest/api/3"
email = "grigor12f@gmail.com"

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

query = url + "/search?jql=issuetype=Task&fields=summary,description"

# Função para extrair os dados da descrição
def extrair_dados(texto):
    linhas = texto.splitlines()
    dados = {}

    for linha in linhas:
        if "Componente:" in linha:
            dados["componente"] = linha.split("Componente:")[1].strip()
        elif "Servidor:" in linha:
            dados["servidor"] = linha.split("Servidor:")[1].strip()
        elif "Data/Hora:" in linha:
            dados["data_hora"] = linha.split("Data/Hora:")[1].strip()
        elif "Tipo de Alerta:" in linha:
            dados["tipo_alerta"] = linha.split("Tipo de Alerta:")[1].strip()
        elif "ID do Alerta no Banco:" in linha:
            dados["id_alerta_banco"] = linha.split("ID do Alerta no Banco:")[1].strip()
        elif "Operador Responsável:" in linha:
            dados["operador_responsavel"] = linha.split("Operador Responsável:")[1].strip()

    return dados


while True:
    response = r.request(
        "GET",
        query,
        headers=headers,
        auth=r.auth.HTTPBasicAuth(email, token)
    )

    data = json.loads(response.text)

    for issue in data["issues"]:
        desc = issue["fields"].get("description", "")
        texto = ""

        if isinstance(desc, dict):
            try:
                texto = desc["content"][0]["content"][0]["text"]
            except (KeyError, IndexError):
                texto = ""
        elif isinstance(desc, str):
            texto = desc

        dados = extrair_dados(texto)

        # calcula a data em minutos
        if "data_hora" in dados and dados["data_hora"]:
            try:
                data_alerta = datetime.strptime(dados["data_hora"], "%Y-%m-%d %H:%M:%S")
                agora = datetime.now()
                diferenca = agora - data_alerta
                minutos = int(diferenca.total_seconds() // 60)
                dados["minutos_aberto"] = minutos
            except Exception as e:
                print(f"Erro ao calcular minutos_aberto: {e}")
                dados["minutos_aberto"] = None
        else:
            dados["minutos_aberto"] = None

        # pra não ficar undefined
        campos_obrigatorios = [
            "componente", "servidor", "data_hora",
            "tipo_alerta", "id_alerta_banco", "operador_responsavel"
        ]

        if all(dados.get(campo) for campo in campos_obrigatorios):
            print(json.dumps(dados, indent=2, ensure_ascii=False))

            enviar = r.post(
                "http://127.0.0.1:8000/desempenho/buscar/chamado",
                data=json.dumps(dados),
                headers={'Content-Type': 'application/json'}
            )

            print(enviar.status_code)
            print(enviar.text)
        else:
            print("Chamado ignorado por dados incompletos:")
            print(json.dumps(dados, indent=2, ensure_ascii=False))

    time.sleep(20)
