import sys
import os

# Adiciona o caminho dos apps para conseguir importar o frappe
sys.path.insert(0, '/home/frappe/frappe-bench/apps/frappe')
import frappe
import json

def force_fix_landing():
    print("Executando dentro do bench execute...")

    LANDING_HTML = """
    <div class="tds-landing-container" style="font-family: sans-serif;">
        <section style="background: linear-gradient(135deg, #003366 0%, #008080 100%); padding: 100px 20px; color: white; text-align: center; border-bottom: 8px solid #F9C300;">
            <img src="/files/logos_act/tds_main.png" style="height: 120px; margin-bottom: 30px; background: white; padding: 15px; border-radius: 20px;">
            <h1 style="font-size: 3.5rem; font-weight: 800; margin-bottom: 20px;">Territórios de Desenvolvimento Social</h1>
            <p style="font-size: 1.5rem; max-width: 800px; margin: 0 auto 40px; opacity: 0.9;">Inclusão Produtiva e Inovação Territorial para o Tocantins. Uma iniciativa UFT / IPEX / MDS.</p>
            <a href="/login" style="background: #F9C300; color: #003366; padding: 18px 45px; border-radius: 50px; font-weight: 800; text-decoration: none; display: inline-block; font-size: 1.2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">ENTRAR NA PLATAFORMA</a>
        </section>
        
        <section style="padding: 80px 20px; background: white;">
            <div style="max-width: 1200px; margin: 0 auto; display: flex; gap: 30px; flex-wrap: wrap; justify-content: center;">
                <div style="flex: 1; min-width: 300px; padding: 40px; background: #f8f9fa; border-radius: 24px; border: 1px solid #eee; text-align: center;">
                    <h2 style="color: #003366; font-weight: 700;">📚 Trilhas de Formação</h2>
                    <p style="color: #666; line-height: 1.6;">Cursos especializados em empreendedorismo, agricultura familiar e economia solidária.</p>
                </div>
                <div style="flex: 1; min-width: 300px; padding: 40px; background: #f8f9fa; border-radius: 24px; border: 1px solid #eee; text-align: center;">
                    <h2 style="color: #003366; font-weight: 700;">🤖 Tutor Cognitivo</h2>
                    <p style="color: #666; line-height: 1.6;">Suporte pedagógico inteligente via Inteligência Artificial para auxiliar sua jornada de aprendizado.</p>
                </div>
            </div>
        </section>

        <footer style="padding: 40px; text-align: center; background: #fff; border-top: 1px solid #eee; opacity: 0.8;">
            <div style="display: flex; justify-content: center; gap: 40px; align-items: center; flex-wrap: wrap;">
                <img src="/files/logos_act/ipex.png" style="height: 40px;">
                <img src="/files/logos_act/uft.png" style="height: 40px;">
                <img src="/files/logos_act/fapt.png" style="height: 40px;">
                <img src="/files/logos_act/mds.png" style="height: 40px;">
            </div>
        </footer>
    </div>
    """

    doc_name = "home-tds"
    print(f"Atualizando Web Page: {doc_name}...")
    
    if frappe.db.exists("Web Page", doc_name):
        wp = frappe.get_doc("Web Page", doc_name)
    else:
        wp = frappe.new_doc("Web Page")
        wp.name = doc_name
        wp.title = "Home TDS"
        wp.route = doc_name

    # Configuração correta para v15: Page Builder ATIVO
    wp.page_builder = 1
    wp.content_type = "Page Builder"
    wp.published = 1
    wp.full_width = 1
    wp.main_section = "" # Limpa a section antiga para evitar conflitos
    
    # Limpa blocos antigos e adiciona o novo bloco Markdown
    wp.set("page_blocks", [])
    wp.append("page_blocks", {
        "web_template": "Markdown",
        "values": json.dumps({
            "content": LANDING_HTML,
            "align": "Left"
        })
    })
    
    wp.save(ignore_permissions=True)
    frappe.db.commit()
    print("✅ Web Page atualizada com sucesso no banco de dados.")

    print("Configurando Website Settings...")
    ws = frappe.get_single("Website Settings")
    ws.home_page = "home-tds"
    ws.app_name = "Projeto TDS"
    ws.save(ignore_permissions=True)
    frappe.db.commit()
    print("✅ Website Settings atualizado.")

    frappe.clear_cache()
    print("✅ Cache global limpo.")

# Fim do script
