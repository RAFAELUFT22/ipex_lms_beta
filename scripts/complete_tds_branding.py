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

# Cores TDS/UFT
COLORS = {
    "navy": "#003366",
    "teal": "#008080",
    "yellow": "#F9C300",
    "white": "#FFFFFF"
}

CUSTOM_CSS = f"""
/* TDS BRANDING - REFINADO E COMPLETO */
:root {{
    --uft-blue: {COLORS['navy']};
    --uft-teal: {COLORS['teal']};
    --uft-yellow: {COLORS['yellow']};
    --text-on-dark: {COLORS['white']};
}}

/* Navbar */
.navbar {{
    background-color: var(--uft-blue) !important;
    border-bottom: 4px solid var(--uft-yellow) !important;
    padding: 0.8rem 1rem !important;
}}

.navbar .nav-link, .navbar .navbar-brand {{
    color: var(--text-on-dark) !important;
    font-weight: 500 !important;
}}

.navbar .nav-link:hover {{
    color: var(--uft-yellow) !important;
}}

/* Buttons */
.btn-primary {{
    background-color: var(--uft-teal) !important;
    border-color: var(--uft-teal) !important;
    color: white !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}}

.btn-primary:hover {{
    background-color: var(--uft-blue) !important;
    border-color: var(--uft-blue) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}}

/* Dashboard & Course Cards */
.hero-section, .lms-hero {{
    background: linear-gradient(135deg, var(--uft-blue) 0%, var(--uft-teal) 100%) !important;
    color: white !important;
    padding: 3rem 2rem !important;
    border-bottom: 6px solid var(--uft-yellow) !important;
}}

.course-card, .card {{
    border-top: 4px solid var(--uft-teal) !important;
    border-radius: 8px !important;
    transition: transform 0.2s !important;
}}

.course-card:hover, .card:hover {{
    transform: scale(1.02) !important;
    border-top-color: var(--uft-yellow) !important;
}}

/* Footer */
footer, .footer {{
    background-color: var(--uft-blue) !important;
    color: white !important;
    border-top: 5px solid var(--uft-yellow) !important;
    padding: 2rem 0 !important;
}}

footer a {{
    color: var(--uft-yellow) !important;
}}

footer a:hover {{
    color: white !important;
    text-decoration: underline !important;
}}
"""

def apply_branding():
    print("🚀 Aplicando Branding TDS Simplificado (Seguro)...")
    
    # Header HTML (TDS + UFT)
    # Note: Using hardcoded paths that we know exist
    url_tds = "/files/logo_tds_oficial.png"
    url_uft = "/files/uft%20logo.png"

    brand_html = f'<div style="display: flex; align-items: center; gap: 10px;">' \
                 f'<img src="{url_tds}" style="max-height: 45px;">' \
                 f'<div style="width: 2px; height: 30px; background: white; opacity: 0.5;"></div>' \
                 f'<img src="{url_uft}" style="max-height: 40px;">' \
                 f'</div>'

    payload = {
        "app_name": "Territórios de Desenvolvimento Social e Inclusão Produtiva",
        "brand_html": brand_html,
        "custom_css": CUSTOM_CSS,
        "banner_image": url_tds,
        "favicon": url_tds,
        "copyright": "© 2026 IPEX / UFT / MDS — Projeto TDS",
        "hide_footer_signup": 1
    }
    
    res = requests.put(f"{BASE_URL}/api/resource/Website Settings/Website Settings", 
                       headers=headers, 
                       json=payload)
    
    if res.status_code == 200:
        print("✅ Website Settings atualizadas com sucesso!")
    else:
        print(f"❌ Erro ao atualizar Website Settings: {res.status_code} {res.text}")

if __name__ == "__main__":
    apply_branding()
