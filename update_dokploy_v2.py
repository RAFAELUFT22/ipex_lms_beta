import requests
import json
import os

TOKEN = "aaaaaagYZfLAfSOkZtePbYJRhdFUiBkDvuxMizVrMioQdKbRPqmVHVNzXKqzpngnjDHanU"
IP = "46.202.150.132"
BASE_URL = f"http://{IP}:3000/api"
COMPOSE_ID = "oal_DlgbJpbKfLvIL0wO2"

headers = {
    "x-api-key": TOKEN,
    "Content-Type": "application/json"
}

def update_dokploy_env():
    # 1. Carregar .env atual do projeto-tds
    env_vars = {}
    with open("/root/projeto-tds/.env", "r") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                env_vars[key] = val

    # 2. Adicionar/Sobrescrever novas configurações
    env_vars["CHATWOOT_API_KEY"] = "w8BYLTQc1s5VMowjQw433rGy"
    env_vars["EMAIL_COORDENACAO"] = "coordenacao@ipexdesenvolvimento.cloud"
    env_vars["EMAIL_ATENDIMENTO"] = "atendimento@ipexdesenvolvimento.cloud"
    env_vars["EMAIL_FINANCEIRO"] = "financeiro@ipexdesenvolvimento.cloud"
    env_vars["EMAIL_PASSWORD"] = "Admin@TDS2024"
    env_vars["SMTP_SERVER"] = "kreativ-mail"
    env_vars["IMAP_SERVER"] = "kreativ-mail"
    env_vars["CHATWOOT_URL"] = "https://chat.ipexdesenvolvimento.cloud"

    # 3. Converter de volta para formato .env
    env_content = "# TDS Project — Updated via Gemini CLI (2026-04-14)\n"
    for key, val in env_vars.items():
        env_content += f"{key}={val}\n"

    # 4. Atualizar no Dokploy usando a API direta (não tRPC)
    print(f"Sincronizando .env no Dokploy para o Compose {COMPOSE_ID}...")
    res = requests.post(f"{BASE_URL}/compose.update", headers=headers, json={
        "composeId": COMPOSE_ID,
        "env": env_content
    })
    
    if res.status_code < 400:
        print("✅ Dokploy atualizado com sucesso!")
        # Trigger deploy
        deploy_res = requests.post(f"{BASE_URL}/compose.deploy", headers=headers, json={"composeId": COMPOSE_ID})
        if deploy_res.status_code < 400:
            print("🚀 Deploy disparado!")
        else:
            print(f"⚠️ Erro no deploy: {deploy_res.status_code} {deploy_res.text}")
    else:
        print(f"❌ Erro ao atualizar Dokploy: {res.status_code} {res.text}")

if __name__ == "__main__":
    update_dokploy_env()
