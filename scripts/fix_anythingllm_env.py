import requests
import os
import urllib3
import json

# Suppress SSL warnings for local connections
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ANYTHINGLLM_URL = "https://rag.ipexdesenvolvimento.cloud"
API_KEY = "W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def update_env():
    print(f"Updating AnythingLLM environment at {ANYTHINGLLM_URL}...")
    
    # Try both /api/v1/system/update-env and /api/system/update-env
    endpoints = ["/api/v1/system/update-env", "/api/system/update-env"]
    
    data = {
        "LLM_PROVIDER": "google",
        "GOOGLE_LLM_API_KEY": "AIzaSyABAw4K_KXK52ONaZlzT4S_j-BA6ZEutYo",
        "GOOGLE_LLM_MODEL_PREF": "gemini-1.5-flash"
    }
    
    for endpoint in endpoints:
        url = f"{ANYTHINGLLM_URL}{endpoint}"
        print(f"Trying {url}...")
        try:
            response = requests.post(url, headers=headers, json=data, verify=False, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            if response.status_code == 200:
                print(f" ✅ Environment updated successfully via {endpoint}")
                return True
        except Exception as e:
            print(f" ❌ Error with {endpoint}: {e}")
            
    return False

if __name__ == "__main__":
    if update_env():
        print("\n🚀 Configuration fix applied!")
    else:
        print("\n❌ Failed to apply configuration fix.")
