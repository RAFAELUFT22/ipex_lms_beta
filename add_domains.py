import requests
import json

TOKEN = "aaaaaagYZfLAfSOkZtePbYJRhdFUiBkDvuxMizVrMioQdKbRPqmVHVNzXKqzpngnjDHanU"
IP = "46.202.150.132"
BASE_URL = f"http://{IP}:3000/api/trpc"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def call_trpc(endpoint, json_input=None):
    url = f"{BASE_URL}/{endpoint}"
    if json_input:
        query = {"0": {"json": json_input}}
        response = requests.post(url, headers=headers, json=query)
    else:
        query = {"0": {"json": None, "meta": {"values": ["undefined"]}}}
        url += f"?batch=true&input={json.dumps(query)}"
        response = requests.get(url, headers=headers)
    
    return response.json()

# 1. Get Compose application ID
print("Fetching composes...")
composes = call_trpc("compose.all")
print(json.dumps(composes, indent=2))

# Assuming we find the ID, we will add domains.
# Example: domain.create
