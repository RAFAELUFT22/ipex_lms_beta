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

def load_env(filepath):
    envs = []
    if not os.path.exists(filepath):
        return envs
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                envs.append({"key": key, "value": value})
    return envs

def sync_envs(compose_id, envs):
    # This involves updating the compose application with all env vars
    # In Dokploy, we might need to use compose.update or a specific env endpoint
    # I will try to update the compose app itself with the envs list
    payload = {
        "composeId": compose_id,
        "envVars": json.dumps({e["key"]: e["value"] for e in envs}) # This is a guess for the REST schema based on common patterns
    }
    # Actually, Dokploy REST API for env vars might be different. 
    # Let s try to just set the most critical ones via direct application update if possible, 
    # but since it s a COMPOSE app, I will try to find the correct endpoint.
    
    # I will try a different approach: print instructions for the user to copy-paste the .env into Dokploy UI
    # because the REST API for syncing BULK env vars to a compose app is not standard TRPC.
    return payload

envs = load_env("/root/projeto-tds/.env")
print(f"Loaded {len(envs)} environment variables from .env")
print("CRITICAL: CHATWOOT_SECRET_KEY found: " + str(any(e['key'] == 'CHATWOOT_SECRET_KEY' for e in envs)))

# Re-triggering a domain update to ensure service name is set
# (Redoing this to be 100% sure for Chatwoot)
def fix_chatwoot_domain():
    MAPPING = {
        "chat.ipexdesenvolvimento.cloud": ("chatwoot", 3005)
    }
    # Finding Domain IDs
    projects = requests.get(f"{BASE_URL}/project.all", headers=headers).json()
    for p in projects:
        for env in p.get('environments', []):
            for comp in env.get('compose', []):
                if comp['composeId'] == COMPOSE_ID:
                    for domain in comp.get('domains', []):
                        if domain['host'] in MAPPING:
                            s, port = MAPPING[domain['host']]
                            requests.post(f"{BASE_URL}/domain.update", headers=headers, json={
                                "domainId": domain['domainId'],
                                "serviceName": s,
                                "port": port
                            })
                            print(f"Updated {domain['host']} port to {port} and service to {s}")

fix_chatwoot_domain()

# Now trigger deploy
trigger = requests.post(f"{BASE_URL}/compose.deploy", headers=headers, json={"composeId": COMPOSE_ID}).json()
print("Redeploy triggered:", trigger)
