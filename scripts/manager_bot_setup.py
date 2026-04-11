import json
import os
import requests
from pathlib import Path

SETTINGS_FILE = "/root/projeto-tds/settings.json"

def load_settings():
    if not Path(SETTINGS_FILE).exists():
        print("Settings file not found.")
        return {}
    with open(SETTINGS_FILE) as f:
        return json.load(f)

def setup_manager_bot():
    settings = load_settings()
    url = settings.get("evolution_url")
    key = settings.get("evolution_key")
    instance_name = "tds_gestor_turmas"

    if not url or not key:
        print("Evolution URL or Key missing in settings.json")
        return

    print(f"[*] Provisioning instance: {instance_name}...")
    
    # Check if instance exists or create it
    create_url = f"{url}/instance/create"
    payload = {
        "instanceName": instance_name,
        "token": "tds_manager_token_2026", # fixed token for this instance
        "number": "", # empty for QR code connection
        "description": "TDS Gestor de Turmas — WhatsApp Business",
        "qrcode": True
    }
    
    headers = {"apikey": key, "Content-Type": "application/json"}
    
    try:
        resp = requests.post(create_url, json=payload, headers=headers)
        if resp.status_code in [201, 200]:
            print(f"[+] Instance {instance_name} created successfully!")
            print("[!] Scan the QR Code in the Evolution Panel to connect.")
        else:
            data = resp.json()
            if "already exists" in data.get("message", "").lower():
                print(f"[!] Instance {instance_name} already exists.")
            else:
                print(f"[-] Error creating instance: {data}")
    except Exception as e:
        print(f"[-] Request failed: {e}")

if __name__ == "__main__":
    setup_manager_bot()
