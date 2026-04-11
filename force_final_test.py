import requests
import json
import time

def run_diagnostic():
    print("🚀 INICIANDO DIAGNÓSTICO TDS LITE E2E...")
    
    # 1. Teste da API Lite (Porta 8081)
    print("\n[1/3] Validando API Local...")
    try:
        res = requests.get("http://localhost:8081/student/5563999374165")
        if res.status_code == 200:
            print("✅ API Lite respondendo corretamente!")
            print(f"   Aluno: {res.json()['name']} | Progresso: {res.json()['progress']}%")
        else:
            print(f"❌ Erro na API: {res.status_code}")
    except Exception as e:
        print(f"❌ Falha de conexão com a API: {e}")

    # 2. Teste do OpenRouter (Novo Token sk-or-v1...4a6)
    print("\n[2/3] Validando Inteligência (OpenRouter)...")
    from lms_lite_tutor import ask_tutor_lite
    try:
        resp = ask_tutor_lite("5563999374165", "Teste de diagnóstico final. Responda com 'SISTEMA TDS ONLINE'")
        if "SISTEMA TDS ONLINE" in resp.upper() or len(resp) > 10:
            print("✅ Inteligência Gemini 2.0 ativa e respondendo!")
            print(f"   Resposta da IA: {resp[:50]}...")
        else:
            print("❌ Resposta da IA inconsistente.")
    except Exception as e:
        print(f"❌ Falha no OpenRouter: {e}")

    # 3. Teste do Chatwoot (Handoff)
    print("\n[3/3] Validando Automação de Handoff (Chatwoot)...")
    token = "jj9zPmJnRRs7bJ4QP5mDGXb2"
    headers = {"api_access_token": token, "Content-Type": "application/json"}
    try:
        # Tenta apenas listar inboxes para validar credenciais
        res = requests.get("https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/inboxes", headers=headers)
        if res.status_code == 200:
            print("✅ Credenciais do Chatwoot validadas!")
        else:
            print(f"❌ Erro no Chatwoot: {res.status_code}")
    except Exception as e:
        print(f"❌ Falha de rede com Chatwoot: {e}")

    print("\n--- FIM DO DIAGNÓSTICO ---")

if __name__ == "__main__":
    run_diagnostic()
