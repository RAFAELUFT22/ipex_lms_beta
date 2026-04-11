import requests
import json

# --- CREDENCIAIS ---
TOKEN = "aaaaaagYZfLAfSOkZtePbYJRhdFUiBkDvuxMizVrMioQdKbRPqmVHVNzXKqzpngnjDHanU"
BASE_URL = "http://46.202.150.132:3000/api/trpc"
PROJECT_ID = "Sbtfrs7UTzDILt4ixSVSG"

headers = {
    "x-api-key": TOKEN,
    "Content-Type": "application/json"
}

def call_trpc_get(endpoint, payload):
    # Formato correto para GET no tRPC Dokploy
    input_str = json.dumps({"0": {"json": payload}})
    url = f"{BASE_URL}/{endpoint}?batch=true&input={input_str}"
    res = requests.get(url, headers=headers)
    return res.json() if res.status_code == 200 else None

def call_trpc_post(endpoint, payload):
    # Formato correto para POST no tRPC Dokploy
    url = f"{BASE_URL}/{endpoint}?batch=true"
    mutation_payload = {"0": {"json": payload}}
    res = requests.post(url, headers=headers, json=mutation_payload)
    return res.json() if res.status_code in [200, 201] else None

def deploy():
    print("🚀 Tentativa Final de Deploy via Dokploy API...")

    # Tenta localizar o compose no projeto
    print("🔍 Localizando ID do compose...")
    proj_data = call_trpc_get("project.one", {"projectId": PROJECT_ID})
    
    if not proj_data:
        print("❌ Falha ao acessar projeto.")
        return

    composes = proj_data[0]['result']['data']['json']['environments'][0]['compose']
    # Buscamos um compose que já exista para reaproveitar ou identificamos que precisamos criar
    # Como criar via API está dando erro de schema, vamos tentar atualizar o 'projeto-tds' que já existe
    compose_obj = next((c for c in composes if c['name'] == "projeto-tds"), None)
    
    if not compose_obj:
        print("❌ Compose 'projeto-tds' não encontrado para atualização.")
        return

    compose_id = compose_obj['composeId']
    print(f"✅ Compose ID encontrado: {compose_id}")

    with open("/root/projeto-tds/docker-compose.lite.yml", "r") as f:
        compose_content = f.read()

    print("📝 Atualizando Docker Compose...")
    call_trpc_post("compose.update", {
        "composeId": compose_id,
        "composeFile": compose_content
    })

    print("🔥 Disparando Deploy...")
    call_trpc_post("compose.deploy", {"composeId": compose_id})

    print("\n✅ Deploy comandado para o compose 'projeto-tds'!")
    print("🔗 Dashboard em: https://ops.ipexdesenvolvimento.cloud")
    print("🔗 API em: https://api-lms.ipexdesenvolvimento.cloud")

if __name__ == "__main__":
    deploy()
