import requests
import json
import os
import sys

# Script para Injetar Regras e RAG do TDS no AnythingLLM automaticamente

API_KEY = os.getenv("ANYTHINGLLM_API_KEY", "W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0") # Chave lida do seu .env
ANYTHINGLLM_URL = "http://kreativ-rag:3001" # Nome do container AnythingLLM na rede
WORKSPACE_SLUG = "producao-audiovisual"

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

# 1. Cria o txt temporário
context_content = """
Você é o Tutor Virtual do Projeto TDS (Territórios de Desenvolvimento Social) - IPEX.
Especialidade: Curso Livre de Produção Audiovisual.

Regras de Atendimento:
1. Seja acolhedor e ajude os alunos de forma resumida e usando emojis educacionais.
2. Você resolve dúvidas unicamente sobre a grade curricular composta por:
  - Módulo 1: Roteiro e Decupagem
  - Módulo 2: Gravação e Equipamentos
  - Módulo 3: Edição no Premiere Pro
  - Módulo 4: Marketing para Audiovisual
3. Certificados: Para emitir o certificado, o aluno deve completar 100% dos módulos na plataforma LMS.
4. Qualquer dúvida operacional fora da grade (exemplo: financeiro, senhas sumidas, horários específicos de lives não cadastrados) ou se você não souber a resposta:
Diga obrigatoriamente que vai transferir para a equipe humana. A transferência ocorre automaticamente se estiver fora do escopo.
"""

file_path = "TDS_Audiovisual_Regras.txt"
with open(file_path, "w") as f:
    f.write(context_content)

print("1. Arquivo de contexto gerado localmente.")

def upload_document():
    print("2. Fazendo upload para o AnythingLLM...")
    url = f"{ANYTHINGLLM_URL}/api/v1/document/upload"
    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(url, headers=headers, files=files)
            if response.status_code == 200:
                data = response.json()
                location = data['documents'][0]['location']
                print(f"✅ Upload realizado com sucesso! Location: {location}")
                return location
            else:
                print("⚠️ Erro no Upload:", response.text)
                return None
    except Exception as e:
        print("Erro na conexão com AnythingLLM:", e)
        return None

def update_embeddings(location):
    print("3. Adicionando contexto ao Workspace e realizando Embeddings...")
    url = f"{ANYTHINGLLM_URL}/api/v1/workspace/{WORKSPACE_SLUG}/update-embeddings"
    payload = {
        "adds": [location],
        "deletes": []
    }
    headers_embed = headers.copy()
    headers_embed["Content-Type"] = "application/json"
    
    response = requests.post(url, headers=headers_embed, json=payload)
    if response.status_code == 200:
        print("✅ Embeddings atualizados com sucesso! O Bot já está treinado com o conteúdo.")
    else:
        print("⚠️ Erro no Embedding:", response.text)

if __name__ == "__main__":
    location = upload_document()
    if location:
        update_embeddings(location)
    os.remove(file_path)
