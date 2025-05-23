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

# json_text = json.dumps(data, indent=4)

# print(len(json_text.splitlines()))
# Extraindo os dados do json
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

    # Extraindo o texto da descrição
    if isinstance(desc, dict):
        try:
            texto = desc["content"][0]["content"][0]["text"]
        except (KeyError, IndexError):
            texto = ""
    elif isinstance(desc, str):
        texto = desc

    # Extraindo dados principais
    dados = extrair_dados(texto)

    # Buscando o operador responsável dentro da mesma estrutura
    for item in issue["fields"]["description"]["content"]:
        if item["type"] == "bulletList":
            for sub_item in item["content"]:
                for sub_sub_item in sub_item["content"]:
                    for text_item in sub_sub_item["content"]:
                        if "Operador Responsável:" in text_item["text"]:
                            dados["operador_responsavel"] = text_item["text"].split(": ")[1]

    print(dados)

# json_dados = json.dumps(dados, indent=4)
# print(len(json_dados.splitlines()))




# enviar = r.post("http://127.0.0.1:8000/desempenho/buscar/chamado", method="POST", data=dados #headers='Content-Type': 'application/json' 
#                ) 
