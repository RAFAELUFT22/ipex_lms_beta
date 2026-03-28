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

/* Footer Refinado com Logos de Parceiros */
footer, .footer {{
    background-color: var(--uft-blue) !important;
    color: white !important;
    border-top: 5px solid var(--uft-yellow) !important;
    padding: 3rem 0 !important;
}}

.footer-logo-grid {{
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
    gap: 30px;
    margin-top: 20px;
    padding: 20px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
}}

.footer-logo-grid img {{
    max-height: 50px;
    filter: brightness(0) invert(1); /* Deixa as logos brancas para o fundo escuro */
    opacity: 0.9;
    transition: all 0.3s ease;
}}

.footer-logo-grid img:hover {{
    filter: none; /* Volta a cor original ao passar o mouse */
    opacity: 1;
    transform: scale(1.1);
}}

footer a {{
    color: var(--uft-yellow) !important;
}}

footer a:hover {{
    color: white !important;
    text-decoration: underline !important;
}}
"""

def upload_file(file_path):
    print(f"Uploading {file_path}...")
    if not os.path.exists(file_path):
        print(f" ❌ File not found: {file_path}")
        return None
    url = f"{BASE_URL}/api/method/upload_file"
    files = {'file': (os.path.basename(file_path), open(file_path, 'rb'))}
    upload_headers = {"Authorization": f"token {API_KEY}:{API_SECRET}"}
    response = requests.post(url, headers=upload_headers, files=files)
    if response.status_code == 200:
        file_url = response.json().get("message", {}).get("file_url")
        print(f" ✅ Uploaded: {file_url}")
        return file_url
    print(f" ❌ Upload failed: {response.text}")
    return None

def apply_branding():
    print("🚀 Aplicando Branding TDS Completo com todos os parceiros...")
    
    logo_dir = "/root/projeto-tds/arquivos_do_projeto/logos"
    logo_files = [
        "logo_tds_oficial.png",
        "uft logo.png",
        "logo-ipex.jpg",
        "logo mds.png",
        "fapto logo.svg",
        "cd centro logo.svg"
    ]
    
    uploaded_logos = {}
    for filename in logo_files:
        path = os.path.join(logo_dir, filename)
        url = upload_file(path)
        if url:
            uploaded_logos[filename] = url
        else:
            # Fallback
            uploaded_logos[filename] = f"/files/{filename.replace(' ', '%20')}"

    # Header HTML (TDS + UFT)
    brand_html = f'<div style="display: flex; align-items: center; gap: 10px;">' \
                 f'<img src="{uploaded_logos["logo_tds_oficial.png"]}" style="max-height: 45px;">' \
                 f'<div style="width: 2px; height: 30px; background: white; opacity: 0.5;"></div>' \
                 f'<img src="{uploaded_logos["uft logo.png"]}" style="max-height: 40px;">' \
                 f'</div>'

    # Footer Template com Grid de Parceiros
    footer_template = f"""
    <div class="container text-center">
        <h5 style="color: {COLORS['yellow']}; font-weight: bold; margin-bottom: 20px;">Realização e Parceria</h5>
        <div class="footer-logo-grid">
            <img src="{uploaded_logos["logo_tds_oficial.png"]}" title="Projeto TDS">
            <img src="{uploaded_logos["uft logo.png"]}" title="UFT">
            <img src="{uploaded_logos["logo-ipex.jpg"]}" title="IPEX">
            <img src="{uploaded_logos["logo mds.png"]}" title="MDS">
            <img src="{uploaded_logos["fapto logo.svg"]}" title="FAPTO">
            <img src="{uploaded_logos["cd centro logo.svg"]}" title="CD Centro">
        </div>
        <div style="margin-top: 30px; font-size: 14px; opacity: 0.8;">
            © 2026 IPEX / UFT / MDS - Projeto Território de Desenvolvimento Social (TDS)
            <br>
            <a href="/privacy">Privacidade</a> | <a href="/terms">Termos de Uso</a>
        </div>
    </div>
    """

    payload = {
        "app_name": "Kreativ Education (TDS)",
        "brand_html": brand_html,
        "custom_css": CUSTOM_CSS,
        "footer_template": footer_template,
        "banner_image": uploaded_logos["logo_tds_oficial.png"],
        "favicon": uploaded_logos["logo_tds_oficial.png"],
        "copyright": "© 2026 IPEX / UFT / MDS - Projeto TDS",
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
