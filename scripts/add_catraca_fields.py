import requests
import os
import json
from dotenv import load_dotenv

# Load credentials from .env.real
load_dotenv('/root/kreativ-setup/.env.real')

BASE_URL = os.getenv("FRAPPE_URL", "https://lms.ipexdesenvolvimento.cloud")
API_KEY = os.getenv("FRAPPE_API_KEY")
API_SECRET = "7c78dcba6e3c5d1" # From HANDOFF.md/credenciais-finais.md
# API_SECRET = os.getenv("FRAPPE_API_SECRET") # Old/incorrect in .env.real?

headers = {
    "Authorization": f"token {API_KEY}:{API_SECRET}",
    "Content-Type": "application/json"
}

def add_fields():
    print(f"Connecting to {BASE_URL}...")
    
    # 1. Get the existing Doctype structure
    res = requests.get(f"{BASE_URL}/api/resource/DocType/TDS Aluno", headers=headers)
    if res.status_code != 200:
        print(f"❌ Error fetching Doctype: {res.text}")
        return

    doctype = res.json()["data"]
    existing_fields = [f["fieldname"] for f in doctype.get("fields", [])]
    
    new_fields = [
        {"fieldname": "estado_catraca", "label": "Estado Catraca", "fieldtype": "Select", "options": "\ninativo\naguardando_leitura\naguardando_mcq\nmodulo_completo\ncertificado_emitido"},
        {"fieldname": "modulo_atual", "label": "Módulo Atual", "fieldtype": "Int", "default": "1"},
        {"fieldname": "secao_atual", "label": "Seção Atual", "fieldtype": "Int", "default": "1"},
        {"fieldname": "respostas_mcq", "label": "Respostas MCQ (JSON)", "fieldtype": "Small Text"},
        {"fieldname": "modulos_concluidos", "label": "Módulos Concluídos (JSON)", "fieldtype": "Small Text"},
        {"fieldname": "data_ultimo_acesso_whatsapp", "label": "Último Acesso WhatsApp", "fieldtype": "Datetime"},
        {"fieldname": "whatsapp_group_jid", "label": "WhatsApp Group JID", "fieldtype": "Data"},
        {"fieldname": "whatsapp_invite_link", "label": "WhatsApp Invite Link", "fieldtype": "Data"}
    ]
    
    added_count = 0
    for field in new_fields:
        if field["fieldname"] not in existing_fields:
            doctype["fields"].append(field)
            print(f"➕ Adding field: {field['fieldname']}")
            added_count += 1
        else:
            print(f"✅ Field already exists: {field['fieldname']}")
            
    if added_count > 0:
        # Update the Doctype
        # Note: In Frappe, to update a Doctype via API, you might need to be in developer mode 
        # or use a specific method. Usually, PUT to /api/resource/DocType works if allowed.
        update_res = requests.put(f"{BASE_URL}/api/resource/DocType/TDS Aluno", headers=headers, json={"fields": doctype["fields"]})
        if update_res.status_code == 200:
            print("✅ Doctype updated successfully.")
        else:
            print(f"❌ Error updating Doctype: {update_res.text}")
    else:
        print("🙌 No new fields to add.")

if __name__ == "__main__":
    add_fields()
