"""
SCRIPT: apply_theme_tds.py
PURPOSE: Aplicar tema visual premium TDS/UFT ao Frappe LMS usando:
  1) Website Theme (método oficial Frappe) com CSS Variables corretas do frappe-ui
  2) CSS baseado nos seletores REAIS do lms.bundle.css (não classes genéricas)
  3) Limpar cache após aplicação

Seletores confirmados pelo lms.bundle.SWM3KSNB.css:
  .course-card, .common-card-style, .common-page-style
  .course-card-title, .course-card-content, .course-card-footer
  .page-title, .bold-title, .bold-heading
  .btn-primary, .btn-outline-primary
  .course-image, .course-card-pills, .course-card-meta
  .cards-parent, .chapter-parent, .chapter-title
  .batch-details
"""
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://lms.ipexdesenvolvimento.cloud"
API_KEY = os.getenv("FRAPPE_API_KEY")
API_SECRET = os.getenv("FRAPPE_API_SECRET")
SITE_NAME = os.getenv("FRAPPE_SITE_NAME", "lms.ipexdesenvolvimento.cloud")

headers = {
    "Authorization": f"token {API_KEY}:{API_SECRET}",
    "Content-Type": "application/json"
}

# ============================================================
# CSS baseado nos seletores REAIS do Frappe LMS
# Usa as variáveis CSS do frappe-ui, não seletores inventados
# ============================================================
TDS_THEME_CSS = """
/* =========================================================
   TEMA TDS/UFT - KREATIV EDUCATION
   Aplicado sobre os seletores reais do frappe-ui/lms.bundle
   Paleta: Azul Marinho #003366 | Teal #008080 | Amarelo #F9C300
   ========================================================= */

/* 1. Sobrescrever as CSS Variables do frappe-ui na raiz */
:root {
    /* Core color tokens usados pelo frappe-ui */
    --primary: #008080 !important;
    --primary-color: #003366 !important;

    /* Blue scale reutilizado como base da UI */
    --blue-500: #008080 !important;
    --blue-50: #e6f7f7 !important;

    /* Melhorar legibilidade de texto */
    --heading-color: #003366 !important;

    /* Bordas e sombras */
    --shadow-sm: 0 1px 3px 0 rgba(0,0,0,0.1), 0 1px 2px 0 rgba(0,0,0,0.06) !important;

    /* Fontes modernas (carregadas via font-face abaixo) */
    --font-stack: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* 2. Carregar fontes modernas via Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Montserrat:wght@400;500;600;700&display=swap');

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ============ BARRA DE NAVEGAÇÃO ============ */

/* O LMS usa o Frappe Navbar — seletores reais */
.navbar,
.navbar-expand-lg,
header nav {
    background-color: #003366 !important;
    border-bottom: 3px solid #F9C300 !important;
    box-shadow: 0 2px 8px rgba(0, 51, 102, 0.3) !important;
}

.navbar-brand,
.navbar-brand span,
.nav-item .nav-link,
.navbar .nav-link {
    color: #ffffff !important;
    font-weight: 500 !important;
}

.navbar .nav-link:hover,
.navbar .nav-link.active {
    color: #F9C300 !important;
}

.navbar .btn-primary {
    background: #008080 !important;
    border-color: #008080 !important;
    color: #fff !important;
}

/* ============ TÍTULOS DE PÁGINA ============ */

/* .page-title é o selector real do Frappe LMS */
.page-title {
    color: #003366 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
}

.bold-title,
.bold-heading {
    color: #003366 !important;
    font-weight: 700 !important;
}

/* ============ CARDS DE CURSO ============ */

/* .common-card-style é o container base de TODOS os cards do LMS */
.common-card-style {
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -1px rgba(0,0,0,0.04) !important;
    transition: transform 0.25s ease, box-shadow 0.25s ease !important;
    overflow: hidden !important;
}

.common-card-style:hover {
    transform: translateY(-6px) !important;
    box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04) !important;
    border-color: #008080 !important;
}

/* .course-card é subclasse específica para cursos */
.course-card {
    border-radius: 12px !important;
}

/* Barra superior colorida para identificar o card como "curso" */
.course-card .course-image {
    border-radius: 12px 12px 0 0 !important;
}

/* Título do card de curso */
.course-card-title {
    color: #003366 !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
}

/* Meta info (instrutor, alunos, etc.) */
.course-card-meta {
    color: #4a5568 !important;
}

/* Footer do card: mantém alinhado e com cor de acento */
.course-card-footer {
    border-top: 2px solid #e6f7f7 !important;
    padding-top: 0.75rem !important;
}

/* Pills de categoria (ex: "Empreendedorismo") */
.course-card-pills {
    background: #e6f7f7 !important;
    color: #008080 !important;
    border: 1px solid #008080 !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
}

/* ============ BOTÕES ============ */

.btn-primary {
    background: linear-gradient(135deg, #008080 0%, #00a3a3 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
    color: #ffffff !important;
    box-shadow: 0 4px 6px rgba(0, 128, 128, 0.2) !important;
    transition: all 0.25s ease !important;
}

.btn-primary:hover,
.btn-primary:focus {
    background: linear-gradient(135deg, #003366 0%, #004080 100%) !important;
    box-shadow: 0 8px 15px rgba(0, 51, 102, 0.25) !important;
    transform: translateY(-1px) !important;
    color: #ffffff !important;
}

.btn-outline-primary {
    color: #008080 !important;
    border-color: #008080 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

.btn-outline-primary:hover {
    background: #008080 !important;
    color: #ffffff !important;
}

/* ============ PÁGINA DE CURSOS (lista) ============ */

.common-page-style {
    background-color: #f8f9fa !important;
}

/* ============ CAPÍTULOS E LIÇÕES ============ */

.chapter-parent {
    border-left: 3px solid #e2e8f0 !important;
    padding-left: 1rem !important;
    transition: border-color 0.2s !important;
}

.chapter-parent:hover {
    border-left-color: #008080 !important;
}

.chapter-title {
    color: #003366 !important;
    font-weight: 600 !important;
}

.active-lesson {
    background: #e6f7f7 !important;
    border-radius: 6px !important;
    color: #008080 !important;
}

/* ============ BREADCRUMB ============ */

.breadcrumb-destination {
    color: #008080 !important;
}

/* ============ BATCH/TURMA DETAILS ============ */

.batch-details {
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
}

/* ============ FOOTER ============ */

footer,
.website-footer,
[class*="footer"] {
    background: #003366 !important;
    color: #ffffff !important;
    border-top: 4px solid #F9C300 !important;
}

footer a,
.website-footer a {
    color: #F9C300 !important;
}

footer a:hover,
.website-footer a:hover {
    color: #ffffff !important;
    text-decoration: underline !important;
}

/* ============ FORMULÁRIO DE LOGIN ============ */

.for-login .page-card,
.page-card {
    border-radius: 16px !important;
    box-shadow: 0 25px 50px -12px rgba(0,0,0,0.15) !important;
}

/* ============ BADGE DE PROGRESSO ============ */

.progress-bar,
.progress-bar-container > div {
    background: #008080 !important;
}

/* ============ LINKS ============ */

a.bold-heading,
a.clickable {
    color: #008080 !important;
}

a.bold-heading:hover,
a.clickable:hover {
    color: #003366 !important;
}
"""

def apply_website_theme():
    """
    Estratégia oficial Frappe:
    - O tema 'Standard' é o ativo. Atualizamos 'custom_overrides' nele.
    - Como fallback garantido, também injetamos via Website Settings.custom_css.
    """

    # --- PASSO 1: Atualizar o tema 'Standard' com custom_overrides ---
    print("\n  1. Atualizando tema 'Standard' com custom_overrides (método oficial)...")
    res = requests.put(
        f"{BASE_URL}/api/resource/Website Theme/Standard",
        headers=headers,
        json={
            "custom_overrides": TDS_THEME_CSS
        }
    )
    if res.status_code == 200:
        print("  ✅ Website Theme 'Standard' atualizado com sucesso!")
    else:
        print(f"  ⚠️  Erro no Website Theme: {res.status_code} — {res.text[:300]}")

    # --- PASSO 2: Fallback via Website Settings.custom_css (carregado em toda página) ---
    print("\n  2. Aplicando CSS via Website Settings (fallback garantido)...")
    res2 = requests.put(
        f"{BASE_URL}/api/resource/Website Settings/Website Settings",
        headers=headers,
        json={
            "website_theme": "Standard",
            "custom_css": TDS_THEME_CSS,
            "app_name": "Kreativ Education (TDS)",
            "copyright": "© 2026 IPEX / UFT / MDS — Projeto TDS",
            "hide_footer_signup": 1,
        }
    )
    if res2.status_code == 200:
        print("  ✅ Website Settings atualizado com sucesso!")
        return True
    else:
        print(f"  ❌ Erro no Website Settings: {res2.status_code} — {res2.text[:300]}")
        return False


def clear_cache():
    """Limpa o cache do Frappe via API."""
    print("\n  3. Limpando cache do Frappe...")
    
    res = requests.post(
        f"{BASE_URL}/api/method/frappe.website.doctype.website_settings.website_settings.clear_cache",
        headers=headers
    )
    
    if res.status_code == 200:
        print("  ✅ Cache limpo!")
    else:
        # Tentar método alternativo
        res2 = requests.post(
            f"{BASE_URL}/api/method/frappe.client.clear_cache",
            headers=headers
        )
        if res2.status_code == 200:
            print("  ✅ Cache limpo (método alternativo)!")
        else:
            print(f"  ⚠️  Cache não foi limpo via API. Execute manualmente: docker exec kreativ-frappe-backend bench --site {SITE_NAME} clear-website-cache")


if __name__ == "__main__":
    print("=" * 65)
    print("  🎨 APLICANDO TEMA PREMIUM TDS/UFT (Método Oficial Frappe)")
    print("=" * 65)
    
    ok2 = apply_website_theme()
    clear_cache()
    
    print("\n" + "=" * 65)
    if ok2:
        print("  🚀 TEMA APLICADO COM SUCESSO!")
        print(f"  Portal: https://{SITE_NAME}")
        print("  → Recarregue o navegador com Ctrl+F5 para ver as mudanças")
    else:
        print("  ⚠️  Houve erros. Verifique a API Key e Secret no .env")
    print("=" * 65)
