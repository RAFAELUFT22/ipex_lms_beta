import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "https://rag.ipexdesenvolvimento.cloud/api/v1"
API_KEY = "W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def ask_rag(workspace_slug, message):
    url = f"{URL}/workspace/{workspace_slug}/chat"
    payload = {
        "message": message,
        "mode": "chat"
    }
    res = requests.post(url, headers=HEADERS, json=payload, verify=False)
    if res.status_code == 200:
        return res.json().get("textResponse")
    else:
        return f"Error {res.status_code}: {res.text}"

prompt = """
Você é o especialista do projeto TDS (Território de Desenvolvimento Social). 
Com base nos documentos disponíveis no workspace 'tds', extraia e prepare as seguintes informações:

1. Estilos e Branding: Quais são as cores oficiais, logos e como devem ser aplicados para padronizar o portal IPEX e outras aplicações?
2. Mensagens de Comunicação: Prepare templates de mensagens de boas-vindas para alunos e professores no WhatsApp e E-mail.
3. Certificados: Qual o texto padrão e os campos obrigatórios que devem constar nos certificados de conclusão de curso do TDS?
4. Textos para o Framework: Prepare descrições padronizadas para o Portal LMS, Tutor Cognitivo e Painel de Gestão.

Responda em formato Markdown estruturado.
"""

print("Consultando AnythingLLM (Workspace: tds)...")
response = ask_rag("tds", prompt)
print(response)
