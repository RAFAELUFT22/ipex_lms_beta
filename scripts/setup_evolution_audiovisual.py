import requests
import json
import os
import sys

# Script para Provisionar Instância na Evolution API
# e conectar ao N8N e Chatwoot.

# === CONFIGURAÇÕES ===
EVOLUTION_URL = "http://kreativ-evolution:8080"
# Use a mesma API KEY que está no seu docker-compose.yml (EVOLUTION_API_KEY)
API_KEY = os.getenv("EVOLUTION_API_KEY", "SUA_API_KEY_AQUI") 
INSTANCE_NAME = "tds_suporte_audiovisual"

N8N_WEBHOOK_URL = "https://n8n.ipexdesenvolvimento.cloud/webhook/whatsapp-kreativ"
CHATWOOT_URL = "https://chat.ipexdesenvolvimento.cloud"
CHATWOOT_ACCOUNT_ID = 2 # Ajuste conforme o ID da sua conta no Chatwoot

headers = {
    "apikey": API_KEY,
    "Content-Type": "application/json"
}

def create_instance():
    url = f"{EVOLUTION_URL}/instance/create"
    payload = {
        "instanceName": INSTANCE_NAME,
        "token": "",
        "qrcode": True, # Permite gerar QR Code
        "integration": "WHATSAPP-BAILEYS" # ou WHATSAPP-BUSINESS se for WABA, Evolution trata de forma nativa.
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            print(f"✅ Instância '{INSTANCE_NAME}' criada/verificada com sucesso!")
        else:
            print(f"⚠️ Resposta criar instância: {response.status_code} - {response.text}")
    except Exception as e:
        print("Erro ao conectar na Evolution API:", e)
        sys.exit(1)

def configure_webhook():
    url = f"{EVOLUTION_URL}/webhook/set/{INSTANCE_NAME}"
    payload = {
        "webhook": {
            "enabled": True,
            "url": N8N_WEBHOOK_URL,
            "byEvents": False,
            "base64": False,
            "events": ["MESSAGES_UPSERT"]
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print("✅ Webhook do N8N configurado!")
    else:
        print(f"⚠️ Resposta webhook: {response.text}")

def configure_chatwoot():
    url = f"{EVOLUTION_URL}/chatwoot/set/{INSTANCE_NAME}"
    payload = {
        "enabled": True,
        "accountId": str(CHATWOOT_ACCOUNT_ID),
        "token": "seu_chatwoot_access_token_aqui_se_necessario",
        "url": CHATWOOT_URL,
        "signMsg": True,
        "reopenConversation": True,
        "conversationPending": False
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print("✅ Integração Chatwoot configurada! Inboxes criadas automaticamente no Chatwoot.")
    else:
        print(f"⚠️ Resposta Chatwoot: {response.text}")

def connect_qr_code():
    print("\n==================================")
    print("📲 Para conectar o WhatsApp escaneando o QR Code:")
    print(f"1. Obtenha a URL base64 ou imagem JSON acessando:")
    print(f"   GET {EVOLUTION_URL}/instance/connect/{INSTANCE_NAME}")
    print(f"   Header: apikey: {API_KEY}")
    print("==================================\n")

if __name__ == "__main__":
    if API_KEY == "SUA_API_KEY_AQUI":
        print("❌ ERRO: Substitua 'SUA_API_KEY_AQUI' pela chave da API ou rode `export EVOLUTION_API_KEY=xxx`")
        sys.exit(1)
        
    print("Iniciando setup da Evolution API...")
    create_instance()
    configure_webhook()
    configure_chatwoot()
    connect_qr_code()
