import frappe

def fix_branding():
    frappe.init(site="lms.ipexdesenvolvimento.cloud")
    frappe.connect()
    
    # 1. Update Website Settings
    website_settings = frappe.get_doc("Website Settings")
    website_settings.app_name = "Territórios de Desenvolvimento Social e Inclusão Produtiva"
    website_settings.app_logo = "/files/logo_tds_oficial.png"
    website_settings.brand_html = "<img src='/files/logo_tds_oficial.png' style='height: 40px;'>"
    website_settings.hide_footer_signup = 1
    website_settings.save(ignore_permissions=True)
    
    # 2. Update System Settings
    system_settings = frappe.get_doc("System Settings")
    system_settings.app_name = "Territórios de Desenvolvimento Social e Inclusão Produtiva"
    system_settings.save(ignore_permissions=True)
    
    frappe.db.commit()
    print("✅ Branding atualizado no banco de dados.")

fix_branding()
