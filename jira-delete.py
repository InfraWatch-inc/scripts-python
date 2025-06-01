from jira import JIRA
import os
from datetime import datetime, timedelta

id_projeto = "10001" 
url = "https://plcvision.atlassian.net/rest/api/3"
email = "grigor12f@gmail.com"

# --- Conexão com o Jira ---
try:
    jira = JIRA(
        server=url,
        basic_auth=(email, token)
    )
    print("Conexão com o Jira estabelecida com sucesso!")
except Exception as e:
    print(f"Erro ao conectar ao Jira: {e}")
   

# --- Função Principal para Apagar Chamados com Mais de 24 Horas ---

def delete_old_open_issues(project_key=None):

    jql_query = 'statusCategory in ("Pendente", "Andamento") AND created <= "-1d"'

    if project_key:
        jql_query = f'project = "{project_key}" AND {jql_query}'

    print(f"\nProcurando chamados para apagar com a JQL: '{jql_query}'...")

    try:
        # Busca os chamados. maxResults define quantos chamados serão buscados por vez.
        # Ajuste conforme sua necessidade, Jira tem limite padrão (geralmente 50 ou 100).
        issues_to_delete = jira.search_issues(jql_query, maxResults=100) 

        if not issues_to_delete:
            print("Nenhum chamado encontrado")
            return

        print(f"** ATENÇÃO: {len(issues_to_delete)} CHAMADO(S) ENCONTRADO(S) PARA EXCLUSÃO AUTOMÁTICA! **")
        print("Lista dos chamados que serão apagados:")
        for issue in issues_to_delete:
            created_time = datetime.strptime(issue.fields.created.split('.')[0], "%Y-%m-%dT%H:%M:%S")
            print(f"- {issue.key}: {issue.fields.summary} (Criado em: {created_time.strftime('%Y-%m-%d %H:%M:%S')}, Status: {issue.fields.status.name})")

        # --- AQUI É ONDE A AÇÃO DE EXCLUSÃO OCORRE SEM CONFIRMAÇÃO MANUAL ---
        for issue in issues_to_delete:
            try:
                print(f"Apagando chamado '{issue.key}'...")
                issue.delete()
            except Exception as e:
                print(f"ERRO: Não foi possível apagar o chamado '{issue.key}': {e}")
        
        print(f"\nProcesso de exclusão concluído. {len(issues_to_delete)} chamados foram tentados para exclusão.")

    except Exception as e:
        print(f"Erro geral ao executar a busca ou exclusão: {e}")

# --- Execução do Script ---
if __name__ == "__main__":
    print("--- Script de Exclusão AUTOMÁTICA de Chamados Antigos do Jira ---")
    print("Este script apagará chamados em aberto com mais de 24 horas sem confirmação.")
    print("USE COM EXTREMA CAUTELA! A exclusão é irreversível.")
    
    # Exemplo de como chamar a função:
    # Para apagar chamados de todos os projetos que atendam ao critério:
    delete_old_open_issues() 
    
    # OU, para apagar chamados de um projeto específico (substitua 'NOME_DO_PROJETO' pela chave do seu projeto):
    # delete_old_open_issues(project_key='PLC') # Exemplo: 'PLC' se for a chave do seu projeto
    
    print("\nScript finalizado.")