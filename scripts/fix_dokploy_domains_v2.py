import requests
import json

TOKEN = "aaaaaagYZfLAfSOkZtePbYJRhdFUiBkDvuxMizVrMioQdKbRPqmVHVNzXKqzpngnjDHanU"
IP = "46.202.150.132"
BASE_URL = f"http://{IP}:3000/api"
headers = {"x-api-key": TOKEN, "Content-Type": "application/json"}
COMPOSE_ID = "oal_DlgbJpbKfLvIL0wO2"

MAPPING = [
    {"host": "evolution.ipexdesenvolvimento.cloud", "serviceName": "evolution", "port": 8080},
    {"host": "n8n.ipexdesenvolvimento.cloud", "serviceName": "n8n", "port": 5678},
    {"host": "rag.ipexdesenvolvimento.cloud", "serviceName": "anythingllm", "port": 3001},
    {"host": "chat.ipexdesenvolvimento.cloud", "serviceName": "chatwoot", "port": 3005},
    {"host": "lms.ipexdesenvolvimento.cloud", "serviceName": "frappe_frontend", "port": 8080}
]

def run():
    print("Starting domain registration...")
    for m in MAPPING:
        payload = {
            "composeId": COMPOSE_ID,
            "host": m["host"],
            "serviceName": m["serviceName"],
            "port": m["port"]
        }
        res = requests.post(f"{BASE_URL}/domain.create", headers=headers, json=payload)
        print(f"Adding {m['host']} -> Status: {res.status_code} | Response: {res.text}")

    print("Triggering deployment...")
    res_deploy = requests.post(f"{BASE_URL}/compose.deploy", headers=headers, json={"composeId": COMPOSE_ID})
    print(f"Deploy triggered -> Status: {res_deploy.status_code} | Body: {res_deploy.text}")

if __name__ == "__main__":
    run()
