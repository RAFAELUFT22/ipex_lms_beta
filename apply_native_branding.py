import frappe

def run():
    # Website Settings
    ws = frappe.get_doc("Website Settings")
    ws.app_name = "Territórios de Desenvolvimento Social e Inclusão Produtiva"
    ws.app_logo = "/files/logo_tds_oficial.png"
    ws.brand_html = "<img src='/files/logo_tds_oficial.png' style='height: 40px;'>"
    ws.favicon = "/files/logo_tds_oficial.png"
    ws.save(ignore_permissions=True)

    # System Settings
    ss = frappe.get_doc("System Settings")
    ss.app_name = "Territórios de Desenvolvimento Social e Inclusão Produtiva"
    ss.save(ignore_permissions=True)

    frappe.db.commit()
    print("✅ Banco de dados atualizado com sucesso.")

if __name__ == "__main__":
    run()
