import requests
import json

TOKEN = "aaaaaagYZfLAfSOkZtePbYJRhdFUiBkDvuxMizVrMioQdKbRPqmVHVNzXKqzpngnjDHanU"
IP = "46.202.150.132"
BASE_URL = f"http://{IP}:3000/api"
COMPOSE_ID = "oal_DlgbJpbKfLvIL0wO2"

headers = {
    "x-api-key": TOKEN,
    "Content-Type": "application/json"
}

def sync():
    # 1. Ler o arquivo docker-compose.yml local
    with open("docker/docker-compose.yml", "r") as f:
        compose_content = f.read()

    # 2. Ler o arquivo .env para pegar as envs atuais
    # Nota: Vamos extrair apenas as chaves e valores simples
    env_content = ""
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            env_content = f.read()

    # 3. Atualizar o Compose no Dokploy
    update_url = f"{BASE_URL}/compose.update"
    payload = {
        "composeId": COMPOSE_ID,
        "composeFile": compose_content,
        "env": env_content
    }
    
    print(f"Updating Compose {COMPOSE_ID} in Dokploy...")
    res = requests.post(update_url, headers=headers, json=payload)
    print("Update Response:", res.status_code, res.text)

    # 4. Trigger Deploy (isso vai sincronizar o estado interno do Dokploy)
    # Como os containers já estão rodando com as mesmas labels e nomes (quase), 
    # o Dokploy deve apenas assumir o controle.
    deploy_url = f"{BASE_URL}/compose.deploy"
    res_deploy = requests.post(deploy_url, headers=headers, json={"composeId": COMPOSE_ID})
    print("Deploy Triggered:", res_deploy.status_code, res_deploy.text)

if __name__ == "__main__":
    import os
    sync()
