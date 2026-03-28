import requests
import json

TOKEN = "aaaaaagYZfLAfSOkZtePbYJRhdFUiBkDvuxMizVrMioQdKbRPqmVHVNzXKqzpngnjDHanU"
IP = "46.202.150.132"
BASE_URL = f"http://{IP}:3000/api"

headers = {
    "x-api-key": TOKEN,
    "Content-Type": "application/json"
}

def get_projects():
    return requests.get(f"{BASE_URL}/project.all", headers=headers).json()

def update_domain(domain_id, service_name, port):
    # Dokploy API expects serviceName specifically for compose domains
    payload = {
        "domainId": domain_id,
        "serviceName": service_name,
        "port": port
    }
    return requests.post(f"{BASE_URL}/domain.update", headers=headers, json=payload).json()

def deploy_compose(compose_id):
    payload = {"composeId": compose_id}
    return requests.post(f"{BASE_URL}/compose.deploy", headers=headers, json=payload).json()

# Mapping domains to service names and ports
MAPPING = {
    "lms.ipexdesenvolvimento.cloud": ("frappe_frontend", 8080),
    "evolution.ipexdesenvolvimento.cloud": ("evolution", 8080),
    "n8n.ipexdesenvolvimento.cloud": ("n8n", 5678),
    "rag.ipexdesenvolvimento.cloud": ("anythingllm", 3001),
    "chat.ipexdesenvolvimento.cloud": ("chatwoot", 3005)
}

projects = get_projects()
compose_id = "oal_DlgbJpbKfLvIL0wO2"

print("Scanning projects for domains...")
for p in projects:
    for env in p.get('environments', []):
        # Check Compose apps
        for comp in env.get('compose', []):
            if comp['composeId'] == compose_id:
                for domain in comp.get('domains', []):
                    host = domain['host']
                    if host in MAPPING:
                        service_name, port = MAPPING[host]
                        print(f"Updating {host} -> Service: {service_name}, Port: {port}")
                        res = update_domain(domain['domainId'], service_name, port)
                        print(res)

print(f"Triggering Deploy for Compose {compose_id}...")
res_deploy = deploy_compose(compose_id)
print(res_deploy)
