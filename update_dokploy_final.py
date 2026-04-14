import requests
import json
import os

TOKEN = "aaaaaagYZfLAfSOkZtePbYJRhdFUiBkDvuxMizVrMioQdKbRPqmVHVNzXKqzpngnjDHanU"
IP = "46.202.150.132"
BASE_URL = f"http://{IP}:3000/api/trpc"
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
    env_content = "# TDS Project — Updated via Gemini CLI\n"
    for key, val in env_vars.items():
        env_content += f"{key}={val}\n"

    # 4. Ler o compose file (vamos usar o NEW_ARCH como base ou o lite se for o caso)
    # De acordo com o docker ps, o projeto-tds-lms-lite-api-1 está rodando.
    # Vou usar o docker-compose.lite.yml que parece ser o que está no Dokploy.
    with open("/root/projeto-tds/docker-compose.lite.yml", "r") as f:
        compose_content = f.read()

    # 5. Atualizar no Dokploy
    url = f"{BASE_URL}/compose.update?batch=true"
    payload = {
        "0": {
            "json": {
                "composeId": COMPOSE_ID,
                "composeFile": compose_content,
                "env": env_content
            }
        }
    }
    
    print(f"Sincronizando .env e Compose no Dokploy ({COMPOSE_ID})...")
    res = requests.post(url, headers=headers, json=payload)
    
    if res.status_code == 200:
        print("✅ Dokploy atualizado com sucesso!")
        # Trigger deploy para aplicar as envs
        deploy_url = f"{BASE_URL}/compose.deploy?batch=true"
        requests.post(deploy_url, headers=headers, json={"0": {"json": {"composeId": COMPOSE_ID}}})
        print("🚀 Deploy disparado!")
    else:
        print(f"❌ Erro ao atualizar Dokploy: {res.status_code} {res.text}")

if __name__ == "__main__":
    update_dokploy_env()
