import requests
import os

TOKEN = "aaaaaagYZfLAfSOkZtePbYJRhdFUiBkDvuxMizVrMioQdKbRPqmVHVNzXKqzpngnjDHanU"
IP = "46.202.150.132"
BASE_URL = f"http://{IP}:3000/api"
COMPOSE_ID = "oal_DlgbJpbKfLvIL0wO2"

headers = {
    "x-api-key": TOKEN,
    "Content-Type": "application/json"
}

def load_env_content(filepath):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found")
        return ""
    with open(filepath, "r") as f:
        return f.read()

def sync():
    env_content = load_env_content("/root/projeto-tds/.env")
    if not env_content:
        return

    # Dokploy API for updating compose env
    # Based on search, the endpoint is likely compose.update with "env" field
    payload = {
        "composeId": COMPOSE_ID,
        "env": env_content
    }
    
    print(f"Syncing environment variables to Dokploy (Compose ID: {COMPOSE_ID})...")
    res = requests.post(f"{BASE_URL}/compose.update", headers=headers, json=payload)
    print(f"Update response: {res.status_code} | {res.text}")
    
    if res.status_code == 200:
        print("Triggering redeploy to apply changes...")
        res_deploy = requests.post(f"{BASE_URL}/compose.deploy", headers=headers, json={"composeId": COMPOSE_ID})
        print(f"Deploy response: {res_deploy.status_code} | {res_deploy.text}")

if __name__ == "__main__":
    sync()
