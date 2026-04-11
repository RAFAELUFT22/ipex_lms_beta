import requests
import json
import os

# Script para Configurar AnythingLLM com OpenRouter e RAG do Curso de Produção Audiovisual

ANYTHINGLLM_URL = "http://localhost:3001" # Ajuste se necessário rodar de fora
API_KEY = os.getenv("ANYTHINGLLM_API_KEY", "SUA_CHAVE_ANYTHINGLLM")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "SUA_CHAVE_OPENROUTER")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def setup_openrouter():
    print("Configurando OpenRouter como provedor LLM...")
    url = f"{ANYTHINGLLM_URL}/api/v1/system/preferences"
    payload = {
        "LLMProvider": "openrouter",
        "OpenRouterApiKey": OPENROUTER_API_KEY,
        "OpenRouterModelPref": "meta-llama/llama-3-8b-instruct" # Modelo Econômico
    }
    # Nota: A rota exata de preferences do AnythingLLM pode variar dependendo da versão, 
    # se falhar, a configuração via painel admin web (porta 3001) é recomendada.
    try:
        response = requests.post(url, json=payload, headers=headers)
        print("Response LLM Setup:", response.status_code)
    except Exception as e:
        print("Aviso: Configuração de env deve ser ajustada via UI admin se a API falhar ->", e)

def create_workspace():
    print("Criando turma 'Produção Audiovisual' (Workspace)...")
    url = f"{ANYTHINGLLM_URL}/api/v1/workspace/new"
    payload = {
        "name": "Produção Audiovisual"
    }
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        slug = data.get("workspace", {}).get("slug", "producao-audiovisual")
        print(f"✅ Workspace '{slug}' criado com sucesso!")
        return slug
    else:
        print(f"⚠️ Erro ao criar workspace: {response.text}")
        return "producao-audiovisual"

def print_instructions(slug):
    print("\n=======================================================")
    print("🎯 PRÓXIMOS PASSOS (Atualização de Bot via RAG):")
    print("1. Acesse o painel do AnythingLLM: http://<ip-do-servidor>:3001")
    print(f"2. Entre no workspace '{slug}'")
    print("3. Faça o upload de um arquivo PDF ou Texto com as instruções do chatbot.")
    print("   Ex: Como responder, regras da turma, cronograma.")
    print("4. Clique em 'Save and Embed'.")
    print("O Chatwoot / Whatsapp automaticamente respeitará este documento no roteamento do N8N!")
    print("=======================================================\n")

if __name__ == "__main__":
    if API_KEY == "SUA_CHAVE_ANYTHINGLLM":
        print("❌ ERRO: Substitua 'SUA_CHAVE_ANYTHINGLLM' no arquivo antes de executar.")
    else:
        setup_openrouter()
        slug = create_workspace()
        print_instructions(slug)
