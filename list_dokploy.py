import requests
import json
import sys

TOKEN = "aaaaaagYZfLAfSOkZtePbYJRhdFUiBkDvuxMizVrMioQdKbRPqmVHVNzXKqzpngnjDHanU"
BASE_URL = "http://46.202.150.132:3000/api/trpc"

headers = {
    "x-api-key": TOKEN,
    "Content-Type": "application/json"
}

def call_trpc(endpoint):
    query = {"0": {"json": None, "meta": {"values": ["undefined"]}}}
    encoded_input = json.dumps(query)
    url = f"{BASE_URL}/{endpoint}?batch=true&input={encoded_input}"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

print("--- PROJECTS ---")
projects = call_trpc("project.all")
print(json.dumps(projects, indent=2))

print("\n--- COMPOSES ---")
composes = call_trpc("compose.all")
print(json.dumps(composes, indent=2))
