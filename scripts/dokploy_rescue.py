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

def update_domain(domain_id, port):
    payload = {"domainId": domain_id, "port": port}
    return requests.post(f"{BASE_URL}/domain.update", headers=headers, json=payload).json()

def deploy_compose(compose_id):
    payload = {"composeId": compose_id}
    return requests.post(f"{BASE_URL}/compose.deploy", headers=headers, json=payload).json()

# 1. Find Domain ID and Compose ID
projects = get_projects()
compose_id = "oal_DlgbJpbKfLvIL0wO2"
domain_id = None

for p in projects:
    for env in p.get('environments', []):
        for comp in env.get('compose', []):
            if comp['composeId'] == compose_id:
                # In Dokploy, domains might be inside 'domains' list in the response
                pass

# Re-list all domains via specialized script if possible, or just try to find it in the project JSON
print("Project Data:")
# print(json.dumps(projects, indent=2))

# I'll try to find the domain ID for 'chat.ipex...'
# Since my previous attempt 'domain.all' failed, I'll search the project structure deeply.
for p in projects:
    for env in p.get('environments', []):
        for comp in env.get('compose', []):
            for domain in comp.get('domains', []):
                if domain['host'] == 'chat.ipexdesenvolvimento.cloud':
                    domain_id = domain['domainId']
                    print(f"Found Chat Domain ID: {domain_id}")

if not domain_id:
    # Fallback: search applications too
    for p in projects:
        for env in p.get('environments', []):
            for app in env.get('applications', []):
                for domain in app.get('domains', []):
                    if domain['host'] == 'chat.ipexdesenvolvimento.cloud':
                        domain_id = domain['domainId']
                        print(f"Found App Domain ID: {domain_id}")

if domain_id:
    print(f"Updating domain {domain_id} to port 3005...")
    res = update_domain(domain_id, 3005)
    print(res)

print(f"Triggering Deploy for Compose {compose_id}...")
res_deploy = deploy_compose(compose_id)
print(res_deploy)
