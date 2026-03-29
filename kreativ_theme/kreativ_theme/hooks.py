# =============================================================================
# kreativ_theme/hooks.py
# Custom App: Tema Premium TDS/UFT para Frappe LMS
#
# ESTRATÉGIA (conforme documentação oficial Frappe):
# - app_include_css: injeta estilos na interface administrativa (Desk)
# - web_include_css: injeta estilos nas páginas web/portal (inclui _lms route)
#
# Ref: https://frappeframework.com/docs/user/en/python-api/hooks#include-css-js
# =============================================================================

from . import __version__ as app_version

app_name = "kreativ_theme"
app_title = "Kreativ Theme"
app_publisher = "IPEX / UFT"
app_description = "Tema visual premium TDS/UFT para o Frappe LMS — identidade IPEX/UFT/MDS"
app_icon = "octicon octicon-paintcan"
app_color = "#003366"
app_email = "ti@ipexdesenvolvimento.cloud"
app_license = "MIT"

# ─── DESK (Interface Administrativa) ─────────────────────────────────────────
# Hook para injetar CSS no Desk (painel admin, Login do Desk)
app_include_css = "/assets/kreativ_theme/css/desk_theme.css"

# ─── PORTAL / WEB (Inclui o LMS SPA via _lms.html) ──────────────────────────
# Este é o hook CORRETO para atingir o portal do LMS.
# O Frappe injeta esses arquivos no <head> das páginas Jinja (web templates),
# incluindo o _lms.html que serve como shell do Vue SPA.
web_include_css = "/assets/kreativ_theme/css/lms_theme.css"

# ─── WEBSITE ROUTES OVERRIDE ──────────────────────────────────────────────────
# Redireciona as rotas do LMS original para o nosso shell customizado Kreativ
website_route_rules = [
    {"from_route": "/lms", "to_route": "lms_custom"},
    {"from_route": "/lms/<path:app_path>", "to_route": "lms_custom"}
]

# ─── CONFIGURAÇÕES DO SITE ────────────────────────────────────────────────────
# Sobrescrever as configurações do Website via hook (sem alterar Website Settings)
website_theme_scss = "kreativ_theme/public/scss/website"
