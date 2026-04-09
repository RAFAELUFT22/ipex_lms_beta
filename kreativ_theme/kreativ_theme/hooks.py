app_name = "kreativ_theme"
app_title = "Kreativ Theme"
app_publisher = "IPEX / UFT"
app_description = "Tema visual premium TDS/UFT para o Frappe LMS"
app_icon = "octicon octicon-paintcan"
app_color = "#003366"
app_email = "ti@ipexdesenvolvimento.cloud"
app_license = "MIT"

# Injections
app_include_css = "/assets/kreativ_theme/css/desk_theme.css"
web_include_css = "/assets/kreativ_theme/css/lms_theme.css"

# SEQUESTRO DE ROTA - Forçar o uso do nosso template customizado
website_route_rules = [
    {"from_route": "/lms", "to_route": "kreativ_lms"},
    {"from_route": "/lms/<path:app_path>", "to_route": "kreativ_lms"}
]
