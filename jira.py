import pandas as pd
import requests as r
import numpy as np
import time
import json


id_projeto = "10001"
url = "https://plcvision.atlassian.net/rest/api/3"
email = "grigor12f@gmail.com"

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

query = url + "/search?jql=issuetype=Task"

response = r.request(
    "GET",
    query, 
    headers=headers,
    auth= r.auth.HTTPBasicAuth(email,token)
)

data = json.loads(response.text)
print(data)