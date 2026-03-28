import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://lms.ipexdesenvolvimento.cloud"
API_KEY = os.getenv("FRAPPE_API_KEY")
API_SECRET = os.getenv("FRAPPE_API_SECRET")

headers = {
    "Authorization": f"token {API_KEY}:{API_SECRET}",
    "Content-Type": "application/json"
}

# Cores TDS/UFT (Oficiais e Variações)
COLORS = {
    "navy": "#003366",
    "navy_light": "#004080",
    "teal": "#008080",
    "teal_light": "#00A3A3",
    "yellow": "#F9C300",
    "bg_light": "#F8F9FA",
    "white": "#FFFFFF"
}

PREMIUM_CSS = f"""
/* 🌟 PREMIUM BRANDING TDS - EFEITO WOW 🌟 */

/* 1. Fontes Modernas */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Montserrat:wght@400;500;700&display=swap');

:root {{
    --font-heading: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-body: 'Montserrat', -apple-system, BlinkMacSystemFont, sans-serif;
    --primary: {COLORS['navy']};
    --accent-teal: {COLORS['teal']};
    --accent-yellow: {COLORS['yellow']};
    --soft-bg: {COLORS['bg_light']};
    --card-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}}

body {{
    font-family: var(--font-body) !important;
    background-color: var(--soft-bg) !important;
    color: #333 !important;
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: var(--font-heading) !important;
    font-weight: 700 !important;
}}

/* 2. Navbar Premium */
.navbar {{
    background: rgba(0, 51, 102, 0.95) !important;
    backdrop-filter: blur(10px);
    border-bottom: 3px solid var(--accent-yellow) !important;
    padding: 0.8rem 1.5rem !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
}}

.navbar .nav-link {{
    color: rgba(255, 255, 255, 0.9) !important;
    font-weight: 500 !important;
    margin: 0 10px;
    transition: all 0.2s ease;
}}

.navbar .nav-link:hover {{
    color: var(--accent-yellow) !important;
    transform: translateY(-2px);
}}

/* 3. Hero Section (Degradê Dinâmico) */
.hero-section, .lms-hero {{
    background: linear-gradient(135deg, {COLORS['navy']} 0%, {COLORS['navy_light']} 50%, {COLORS['teal']} 100%) !important;
    color: white !important;
    padding: 5rem 2rem !important;
    border-radius: 0 0 40px 40px !important;
    margin-bottom: 30px !important;
    position: relative;
    overflow: hidden;
}}

.hero-section::after {{
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 300px;
    height: 300px;
    background: rgba(249, 195, 0, 0.1);
    border-radius: 50%;
    filter: blur(80px);
}}

/* 4. Cards de Curso (Design Moderno) */
.course-card, .card {{
    border: none !important;
    border-radius: 16px !important;
    box-shadow: var(--card-shadow) !important;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    background: white !important;
}}

.course-card:hover, .card:hover {{
    transform: translateY(-8px) !important;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04) !important;
}}

.course-card-image {{
    border-radius: 16px 16px 0 0 !important;
}}

.course-card .card-body {{
    padding: 1.5rem !important;
}}

.progress {{
    height: 8px !important;
    background-color: #E2E8F0 !important;
    border-radius: full !important;
}}

.progress-bar {{
    background: linear-gradient(90deg, {COLORS['teal']} 0%, {COLORS['teal_light']} 100%) !important;
}}

/* 5. Botões de Ação */
.btn-primary {{
    background: linear-gradient(135deg, {COLORS['teal']} 0%, {COLORS['teal_light']} 100%) !important;
    border: none !important;
    padding: 12px 24px !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px;
    box-shadow: 0 4px 6px rgba(0, 128, 128, 0.2) !important;
    transition: all 0.3s ease !important;
}}

.btn-primary:hover {{
    background: linear-gradient(135deg, {COLORS['navy']} 0%, {COLORS['teal']} 100%) !important;
    transform: scale(1.05) !important;
    box-shadow: 0 10px 15px rgba(0, 128, 128, 0.3) !important;
}}

/* 6. Footer (Elegant) */
footer, .footer {{
    background: {COLORS['navy']} !important;
    color: white !important;
    border-top: 5px solid var(--accent-yellow) !important;
    padding: 4rem 1rem 2rem !important;
    margin-top: 60px !important;
}}

.footer-links a {{
    color: #CBD5E0 !important;
    transition: color 0.2s;
}}

.footer-links a:hover {{
    color: var(--accent-yellow) !important;
}}

/* 7. Tela de Login (UFT/TDS) */
.login-content {{
    background: linear-gradient(135deg, {COLORS['navy']} 0%, {COLORS['bg_light']} 100%) !important;
}}

.form-signin {{
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(10px);
    border-radius: 24px !important;
    padding: 3rem !important;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25) !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
}}

.page-card-head img {{
    max-height: 80px !important;
    margin-bottom: 2rem !important;
}}

/* 8. Dashboard de Curso e Lições */
.chapter-item {{
    border-left: 4px solid #E2E8F0 !important;
    padding-left: 1.5rem !important;
    transition: all 0.2s ease !important;
}}

.chapter-item.active {{
    border-left-color: var(--accent-teal) !important;
    background: rgba(0, 128, 128, 0.05) !important;
}}

.lesson-item {{
    border-radius: 8px !important;
    margin: 5px 0 !important;
}}

.lesson-item:hover {{
    background: rgba(0, 51, 102, 0.05) !important;
}}

/* 9. Tutor Cognitivo Widget (Se existir) */
#chatwoot-widget-bubble {{
    background: {COLORS['teal']} !important;
    box-shadow: 0 10px 15px -3px rgba(0, 128, 128, 0.3) !important;
    border: 2px solid var(--accent-yellow) !important;
}}
"""

def apply_premium_branding():
    print("🚀 Elevando o Design do TDS para o nível Premium...")
    
    # URLs das imagens ja existentes no servidor
    url_tds = "/files/logo_tds_oficial.png"
    url_uft = "/files/uft_logo.png"

    brand_html = f'<div style="display: flex; align-items: center; gap: 15px;">' \
                 f'<img src="{url_tds}" style="max-height: 48px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));">' \
                 f'<div style="width: 2px; height: 35px; background: rgba(255,255,255,0.3); border-radius: 2px;"></div>' \
                 f'<img src="{url_uft}" style="max-height: 42px;">' \
                 f'</div>'

    payload = {
        "app_name": "Kreativ Education (TDS)",
        "brand_html": brand_html,
        "custom_css": PREMIUM_CSS,
        "banner_image": url_tds,
        "favicon": url_tds,
        "copyright": "© 2026 IPEX / UFT / MDS - Projeto TDS (Inovação para Inclusão)",
        "hide_footer_signup": 1
    }
    
    res = requests.put(f"{BASE_URL}/api/resource/Website Settings/Website Settings", 
                       headers=headers, 
                       json=payload)
    
    if res.status_code == 200:
        print("✅ Design Premium aplicado com sucesso! Limpe o cache do navegador para ver.")
    else:
        print(f"❌ Erro ao atualizar Website Settings: {res.status_code} {res.text}")

if __name__ == "__main__":
    apply_premium_branding()
