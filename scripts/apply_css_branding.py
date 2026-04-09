import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://lms.ipexdesenvolvimento.cloud"
API_KEY = os.getenv("FRAPPE_API_KEY")
API_SECRET = os.getenv("FRAPPE_API_SECRET")

headers = {
    "Authorization": f"token {API_KEY}:{API_SECRET}",
    "Content-Type": "application/json"
}

custom_css = """
/* Branding TDS - UFT/IPEX */
:root {
    --primary-color: #003366 !important;
    --navbar-bg: #003366 !important;
}
.navbar {
    background-color: #003366 !important;
}
.navbar-brand img {
    max-height: 40px !important;
}
.navbar-light .navbar-nav .nav-link {
    color: #ffffff !important;
}
.btn-primary {
    background-color: #003366 !important;
    border-color: #003366 !important;
}
.btn-primary:hover {
    background-color: #008080 !important;
    border-color: #008080 !important;
}
.card-header {
    background-color: #003366 !important;
    color: white !important;
}
/* Estilo para o Hero Section do Dashboard */
.hero-section {
    background: linear-gradient(135deg, #003366 0%, #008080 100%) !important;
    color: white !important;
    padding: 40px 20px !important;
    border-radius: 8px !important;
}
"""

def apply_branding():
    print("Injetando CSS de branding nas Website Settings...")
    
    payload = {
        "custom_css": custom_css,
        "app_name": "Territórios de Desenvolvimento Social e Inclusão Produtiva",
        "brand_html": '<img src="/files/logo_tds_oficial.png" style="max-height: 40px;">'
    }
    
    res = requests.put(f"{BASE_URL}/api/resource/Website Settings/Website Settings", 
                       headers=headers, 
                       json=payload)
    
    if res.status_code == 200:
        print("✅ CSS e Branding aplicados com sucesso!")
    else:
        print(f"❌ Erro ao aplicar branding: {res.status_code} {res.text}")

if __name__ == "__main__":
    apply_branding()
