import requests
import json

TOKEN = "aaaaaagYZfLAfSOkZtePbYJRhdFUiBkDvuxMizVrMioQdKbRPqmVHVNzXKqzpngnjDHanU"
IP = "46.202.150.132"
BASE_URL = f"http://{IP}:3000/api"

headers = {
    "x-api-key": TOKEN,
    "Content-Type": "application/json"
}

# 1. List Projects to find the domain ID for chat.ipexdesenvolvimento.cloud
print("Fetching projects...")
response = requests.get(f"{BASE_URL}/project.all", headers=headers)
projects = response.json()

domain_id = None
for p in projects:
    for env in p.get('environments', []):
        for comp in env.get('compose', []):
            if comp['name'] == 'projeto-tds':
               # Compose domains are usually listed here or we need to find them elsewhere
               pass

# 2. Try to list all domains directly
print("Fetching all domains...")
response = requests.get(f"{BASE_URL}/domain.all", headers=headers)
if response.status_code == 200:
    domains = response.json()
    for d in domains:
        if d['host'] == 'chat.ipexdesenvolvimento.cloud':
            domain_id = d['domainId']
            print(f"Found Domain ID: {domain_id}")

if domain_id:
    print(f"Updating domain {domain_id} to port 3005...")
    # domain.update endpoint
    update_url = f"{BASE_URL}/domain.update"
    payload = {
        "domainId": domain_id,
        "port": 3005
    }
    res = requests.post(update_url, headers=headers, json=payload)
    print(json.dumps(res.json(), indent=2))
else:
    print("Domain not found.")

