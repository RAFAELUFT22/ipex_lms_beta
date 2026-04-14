import requests
import json
import time

API_BASE = "https://api-lms.ipexdesenvolvimento.cloud"
ADMIN_KEY = "admin-tds-2026"
TEST_PHONE = "5563999374165"

def smoke_test():
    print(f"🧪 INICIANDO TESTE DE FUMAÇA — ALUNO {TEST_PHONE}\n")

    # 1. Health Check
    try:
        res = requests.get(f"{API_BASE}/health")
        print(f"[1] API Health: {'✅ OK' if res.status_code == 200 else '❌ Falha'}")
    except: print("[1] API Health: ❌ Erro de Conexão")

    # 2. Testar Atualização SISEC (Novo Endpoint)
    print(f"[2] Enviando dados SISEC simulados...")
    sisec_payload = {
        "whatsapp": TEST_PHONE,
        "data": {
            "campo_6": "Rafael Teste Gemini",
            "campo_40": "Sim", # Trabalhador Rural
            "campo_63": "Produção de Mel e Hortaliças",
            "localidade": "Araguaína-TO"
        }
    }
    headers = {"X-Admin-Key": ADMIN_KEY, "Content-Type": "application/json"}
    res_sisec = requests.post(f"{API_BASE}/student/sisec", json=sisec_payload, headers=headers)
    if res_sisec.status_code == 200:
        print(f"   ✅ SISEC gravado com sucesso ({res_sisec.json().get('fields')} campos)")
    else:
        print(f"   ❌ Falha ao gravar SISEC: {res_sisec.status_code} {res_sisec.text}")

    # 3. Validar Persistência no Perfil
    res_profile = requests.get(f"{API_BASE}/student/{TEST_PHONE}")
    if res_profile.status_code == 200:
        data = res_profile.json()
        name = data.get('name')
        is_rural = "Sim" if TEST_PHONE in str(data) else "N/A" # Checagem bruta nos dados
        print(f"[3] Perfil recuperado: {name} | Localidade: {data.get('localidade')}")
    else:
        print(f"[3] ❌ Falha ao recuperar perfil")

    # 4. Testar Inteligência (Contexto SISEC)
    print(f"[4] Testando Tutor IA com contexto SISEC...")
    chat_payload = {
        "phone": TEST_PHONE,
        "message": "Sou trabalhador rural? O que eu produzo?"
    }
    res_chat = requests.post(f"{API_BASE}/chat/query", json=chat_payload)
    if res_chat.status_code == 200:
        reply = res_chat.json().get('reply', '')
        print(f"   🤖 Resposta da IA: {reply[:100]}...")
        if "rural" in reply.lower() or "mel" in reply.lower():
            print("   ✅ SUCESSO: A IA reconheceu o contexto SISEC do aluno!")
        else:
            print("   ⚠️ AVISO: A IA respondeu, mas pode não ter usado o contexto SISEC.")
    else:
        print(f"   ❌ Falha no Chat IA: {res_chat.status_code}")

    print("\n--- FIM DO TESTE ---")

if __name__ == "__main__":
    smoke_test()
