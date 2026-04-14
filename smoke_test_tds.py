import requests
import json
import os
import sys

# --- CONFIG ---
ADMIN_KEY = "admin-tds-2026"
LMS_API_URL = "https://api-lms.ipexdesenvolvimento.cloud"
CHATWOOT_URL = "https://chat.ipexdesenvolvimento.cloud"
CHATWOOT_TOKEN = "w8BYLTQc1s5VMowjQw433rGy" # Correct Admin Token
OPENROUTER_API_KEY = "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"

def test_api_health():
    print("[1/5] Testing API Health...")
    try:
        res = requests.get(f"{LMS_API_URL}/health", timeout=10)
        if res.status_code == 200:
            print("✅ API Health OK")
            return True
        else:
            print(f"❌ API Health Failed: {res.status_code}")
    except Exception as e:
        print(f"❌ API Health Connection Error: {e}")
    return False

def test_chatwoot_auth():
    print("[2/5] Testing Chatwoot Auth...")
    headers = {"api_access_token": CHATWOOT_TOKEN, "Content-Type": "application/json"}
    try:
        res = requests.get(f"{CHATWOOT_URL}/api/v1/profile", headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            print(f"✅ Chatwoot Auth OK (User: {data['name']}, Account: {data['accounts'][0]['name']})")
            return True
        else:
            print(f"❌ Chatwoot Auth Failed: {res.status_code} {res.text}")
    except Exception as e:
        print(f"❌ Chatwoot Connection Error: {e}")
    return False

def test_chatwoot_inboxes():
    print("[3/5] Testing Chatwoot Inboxes...")
    headers = {"api_access_token": CHATWOOT_TOKEN, "Content-Type": "application/json"}
    try:
        res = requests.get(f"{CHATWOOT_URL}/api/v1/accounts/1/inboxes", headers=headers, timeout=10)
        if res.status_code == 200:
            inboxes = res.json()["payload"]
            print(f"✅ Found {len(inboxes)} inboxes")
            for ib in inboxes:
                status = "ENABLED" if ib.get("imap_enabled") or ib.get("smtp_enabled") or ib.get("channel_type") == "Channel::Api" else "DISABLED/IDLE"
                print(f"   - ID {ib['id']}: {ib['name']} ({ib['channel_type']}) [{status}]")
            return inboxes
        else:
            print(f"❌ Failed to list inboxes: {res.status_code}")
    except Exception as e:
        print(f"❌ Inboxes Test Error: {e}")
    return None

def test_openrouter():
    print("[4/5] Testing OpenRouter AI...")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://ipexdesenvolvimento.cloud",
        "X-Title": "TDS Smoke Test"
    }
    payload = {
        "model": "google/gemini-2.0-flash-lite-001",
        "messages": [{"role": "user", "content": "Ping"}]
    }
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=15)
        if res.status_code == 200:
            print("✅ OpenRouter OK")
            return True
        else:
            print(f"❌ OpenRouter Failed: {res.status_code} {res.text}")
    except Exception as e:
        print(f"❌ OpenRouter Error: {e}")
    return False

def test_frappe_lms():
    print("[5/5] Testing Frappe LMS...")
    FRAPPE_URL = "https://lms.ipexdesenvolvimento.cloud"
    try:
        res = requests.get(f"{FRAPPE_URL}/api/method/frappe.auth.get_logged_user", timeout=10)
        # 403 is expected since we don't provide credentials, but it confirms server is up
        if res.status_code in (200, 403):
            print("✅ Frappe LMS Server Reached")
            return True
        else:
            print(f"❌ Frappe LMS Failed: {res.status_code}")
    except Exception as e:
        print(f"❌ Frappe LMS Error: {e}")
    return False

def main():
    print("--- TDS SMOKE TEST 2026 ---")
    results = [
        test_api_health(),
        test_chatwoot_auth(),
        test_chatwoot_inboxes() is not None,
        test_openrouter(),
        test_frappe_lms()
    ]
    
    if all(results):
        print("\n🏆 TODOS OS TESTES PASSARAM!")
        sys.exit(0)
    else:
        print("\n⚠️ ALGUNS TESTES FALHARAM!")
        sys.exit(1)

if __name__ == "__main__":
    main()
