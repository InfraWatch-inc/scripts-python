from jiraChamados import JIRA 
import os
from datetime import datetime

# --- Configurações ---
# Tente obter as credenciais e a URL de variáveis de ambiente para maior segurança
# Defina estas variáveis no seu ambiente: JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN
# Exemplo de como definir no terminal (Linux/macOS):
# export JIRA_URL="https://sua-instancia-jira.atlassian.net"
# export JIRA_EMAIL="seu_email@exemplo.com"
# export JIRA_API_TOKEN="seu_token_aqui"
# No Windows, use 'set' ou configure através das Propriedades do Sistema.

JIRA_BASE_URL = os.getenv("JIRA_URL", "") # URL base do Jira
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "") # Seu email do Jira
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "") # Seu token da API Jira

# ID do projeto padrão para operar. Pode ser a chave do projeto (ex: "PLC") ou o ID numérico.
# Se for usar a chave, a JQL abaixo já lida com isso.
DEFAULT_PROJECT_KEY = "REBUSFARM"

# --- Conexão com o Jira ---
jira_connection = None
try:
    jira_connection = JIRA(
        server=JIRA_BASE_URL,
        basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN)
    )
    print(f"Conexão com o Jira ({JIRA_BASE_URL}) estabelecida com sucesso!")
except Exception as e:
    print(f"Erro ao conectar ao Jira: {e}")
    # Se não houver conexão, não adianta continuar o script
    exit()

# --- Função Principal para Apagar Chamados ---
def delete_old_open_issues(jira_client, project_key=None):
    """
    Busca e apaga chamados em categorias 'Pendente' ou 'Andamento'
    criados há mais de 24 horas.

    Args:
        jira_client: Instância da conexão com o Jira.
        project_key: Chave do projeto (opcional). Se None, busca em todos os projetos
                     (conforme permissões do usuário).
    """

    # Nota sobre JQL:
    # - 'statusCategory in ("Pendente", "Andamento")': Certifique-se que estas são
    #   as categorias de status corretas e nos idiomas configurados na sua instância Jira.
    #   As categorias padrão em inglês são "To Do" e "In Progress".
    # - 'created <= "-1d"': Chamados criados há 24 horas ou mais.
    jql_query_parts = ['statusCategory in ("In Progress", "To Do", "Done")']

    if project_key:
        jql_query_parts.insert(0, f'project = "{project_key}"')

    jql_query = " AND ".join(jql_query_parts)

    print(f"\nProcurando chamados para apagar com a JQL: '{jql_query}'...")

    try:
        # Nota sobre paginação:
        # A busca abaixo é limitada por 'maxResults'. Se houver mais chamados
        # que o limite, apenas o primeiro lote será processado.
        # Para uma exclusão completa, implemente a paginação (buscando em loop
        # com o parâmetro 'startAt').
        issues_to_delete = jira_client.search_issues(jql_query, maxResults=1000, fields="summary,created,status")

        if not issues_to_delete:
            print("Nenhum chamado encontrado com os critérios especificados.")
            return

        print(f"\n** ATENÇÃO: {len(issues_to_delete)} CHAMADO(S) ENCONTRADO(S) PARA POSSÍVEL EXCLUSÃO! **")
        print("Lista dos chamados que seriam apagados:")
        for issue in issues_to_delete:
            # JIRA retorna 'created' como string em UTC. Ex: '2023-10-27T10:15:30.500-0300'
            # Vamos simplificar o parsing e ignorar o sub-segundo e timezone para exibição.
            created_str_simple = issue.fields.created.split('.')[0]
            created_time = datetime.strptime(created_str_simple, "%Y-%m-%dT%H:%M:%S")
            print(f"- {issue.key}: {issue.fields.summary} (Criado em: {created_time.strftime('%Y-%m-%d %H:%M:%S')}, Status: {issue.fields.status.name})")

        # --- CONFIRMAÇÃO MANUAL ANTES DA EXCLUSÃO ---
        print("\n----------------------------------------------------------------------")
        print("!! AVISO IMPORTANTE !!")
        print("Os chamados listados acima serão EXCLUÍDOS PERMANENTEMENTE.")
        print("Esta ação é IRREVERSÍVEL.")
        print("----------------------------------------------------------------------")
        
        confirm = input(f"Você tem CERTEZA que deseja excluir estes {len(issues_to_delete)} chamado(s)? (digite 'sim' para confirmar): ")

        if confirm.lower() != 'sim':
            print("\nExclusão cancelada pelo usuário.")
            return

        print("\nIniciando processo de exclusão...")
        deleted_count = 0
        failed_count = 0
        for issue in issues_to_delete:
            try:
                print(f"Apagando chamado '{issue.key}'...")
                issue.delete()
                deleted_count += 1
            except Exception as e:
                print(f"ERRO: Não foi possível apagar o chamado '{issue.key}': {e}")
                failed_count += 1
        
        print(f"\nProcesso de exclusão concluído.")
        if deleted_count > 0:
            print(f"{deleted_count} chamado(s) foram apagados com sucesso.")
        if failed_count > 0:
            print(f"{failed_count} chamado(s) não puderam ser apagados.")

    except Exception as e:
        print(f"Erro geral ao executar a busca ou exclusão: {e}")

# --- Execução do Script ---
if __name__ == "__main__":
    if not JIRA_EMAIL or not JIRA_API_TOKEN or JIRA_EMAIL == "" or JIRA_API_TOKEN == "":
        print("AVISO: Usando credenciais padrão do código. É ALTAMENTE RECOMENDADO")
        print("       configurar as variáveis de ambiente JIRA_URL, JIRA_EMAIL e JIRA_API_TOKEN.")

    print("\n--- Script de Exclusão de Chamados Antigos do Jira ---")
    print("Este script procurará chamados em aberto com mais de 24 horas.")
    print("USE COM EXTREMA CAUTELA! A exclusão é irreversível e requer confirmação.")
    
    # Para apagar chamados do projeto padrão definido em DEFAULT_PROJECT_KEY:
    delete_old_open_issues(jira_connection, project_key=DEFAULT_PROJECT_KEY)
    
    # OU, para apagar chamados de um projeto específico (substitua 'SUA_CHAVE_DE_PROJETO'):
    # delete_old_open_issues(jira_connection, project_key='SUA_CHAVE_DE_PROJETO')

    # OU, para apagar chamados de todos os projetos (CUIDADO EXTRA):
    # delete_old_open_issues(jira_connection)
    
    print("\nScript finalizado.")