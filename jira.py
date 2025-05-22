import requests as r
import json


id_projeto = "10001"
url = "https://plcvision.atlassian.net/rest/api/3"

email = "grigor12f@gmail.com"

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

query = url + "/search?jql=issuetype=Task&fields=summary,description"

response = r.request(
    "GET",
    query, 
    headers=headers,
    auth= r.auth.HTTPBasicAuth(email,token)
)

data = json.loads(response.text)

# print(json.dumps(data, indent=2))

# extraindo os dados do json
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
        elif "Métrica:" in linha:
            dados["metrica"] = linha.split("Métrica:")[1].strip()
        elif "Valor Capturado:" in linha:
            dados["valor"] = linha.split("Valor Capturado:")[1].strip()
        elif "ID do Alerta no Banco:" in linha:
            dados["id_alerta_banco"] = linha.split("ID do Alerta no Banco:")[1].strip()

    return dados

# percorre todos os dados
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

    print(dados)

