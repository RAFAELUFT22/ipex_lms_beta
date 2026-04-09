import requests
import json

TOKEN = "aaaaaagYZfLAfSOkZtePbYJRhdFUiBkDvuxMizVrMioQdKbRPqmVHVNzXKqzpngnjDHanU"
IP = "46.202.150.132"
BASE_URL = f"http://{IP}:3000/api"

headers = {
    "x-api-key": TOKEN,
    "Content-Type": "application/json"
}

def get_apps():
    url = f"{BASE_URL}/project.all"
    response = requests.get(url, headers=headers)
    return response.json()

def add_domain(host, compose_id, service_name, port):
    url = f"{BASE_URL}/domain.create"
    payload = {
        "host": host,
        "composeId": compose_id,
        "composeServiceName": service_name,
        "domainType": "compose",
        "port": port,
        "https": True,
        "certificateType": "letsencrypt"
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

print("Fetching project data...")
projects = get_apps()
# Find the project and compose
compose_id = None
for p in projects:
    for env in p.get('environments', []):
        for comp in env.get('compose', []):
            if comp['name'] == 'projeto-tds':
                compose_id = comp['composeId']
                print(f"Found Compose ID: {compose_id}")

if compose_id:
    domains = [
        {"host": "evolution.ipexdesenvolvimento.cloud", "service": "evolution-api", "port": 8080},
        {"host": "n8n.ipexdesenvolvimento.cloud", "service": "n8n", "port": 5678},
        {"host": "rag.ipexdesenvolvimento.cloud", "service": "anythingllm", "port": 3001},
        {"host": "lms.ipexdesenvolvimento.cloud", "service": "frappe_frontend", "port": 8080},
        {"host": "chat.ipexdesenvolvimento.cloud", "service": "chatwoot", "port": 3005}
    ]
    for d in domains:
        print(f"Adding domain {d['host']}...")
        res = add_domain(d['host'], compose_id, d['service'], d['port'])
        print(json.dumps(res, indent=2))
else:
    print("Compose 'projeto-tds' not found.")

