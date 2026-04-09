import sys
sys.path.insert(0, '/home/frappe/frappe-bench/apps/frappe')
import frappe

def apply_global_js():
    print("Injetando JS via bench execute...")

    JS_CODE = """
    frappe.ready(function() {
        if (window.location.pathname === '/' || window.location.pathname === '/home-tds') {
            const contentArea = document.querySelector('.web-page-content') || document.querySelector('.page_content');
            if (contentArea) {
                console.log('TDS: Renderizando Landing Page Segura...');
                contentArea.innerHTML = `
                    <div style="background: linear-gradient(135deg, #003366 0%, #008080 100%); color: white; padding: 100px 20px; text-align: center; border-bottom: 8px solid #F9C300;">
                        <img src="/files/logos_act/tds_main.png" style="height: 120px; background: white; padding: 15px; border-radius: 20px; margin-bottom: 30px;">
                        <h1 style="font-size: 3.5rem; font-weight: 800; margin-bottom: 20px;">Territórios de Desenvolvimento Social</h1>
                        <p style="font-size: 1.5rem; max-width: 800px; margin: 0 auto 40px; opacity: 0.9;">Inclusão Produtiva e Inovação Territorial para o Tocantins. Uma iniciativa UFT / IPEX / MDS.</p>
                        <a href="/login" style="background: #F9C300; color: #003366; padding: 18px 45px; border-radius: 50px; font-weight: 800; text-decoration: none; display: inline-block; font-size: 1.2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">ACESSAR PLATAFORMA</a>
                    </div>
                    <div style="padding: 80px 20px; background: white; text-align: center;">
                        <div style="display: flex; justify-content: center; gap: 30px; flex-wrap: wrap; max-width: 1200px; margin: 0 auto;">
                            <div style="flex: 1; min-width: 300px; padding: 40px; background: #f8f9fa; border-radius: 24px; border: 1px solid #eee;">
                                <h3 style="color: #003366; font-weight: 700;">📚 Trilhas de Formação</h3>
                                <p style="color: #666; line-height: 1.6;">Cursos focados em empreendedorismo, agricultura familiar e economia solidária.</p>
                            </div>
                            <div style="flex: 1; min-width: 300px; padding: 40px; background: #f8f9fa; border-radius: 24px; border: 1px solid #eee;">
                                <h3 style="color: #003366; font-weight: 700;">🤖 Tutor Cognitivo</h3>
                                <p style="color: #666; line-height: 1.6;">Suporte pedagógico 24/7 com Inteligência Artificial integrada ao conteúdo.</p>
                            </div>
                        </div>
                    </div>
                    <div style="padding: 40px; text-align: center; background: #fff; border-top: 1px solid #eee; opacity: 0.8;">
                        <img src="/files/logos_act/ipex.png" style="height: 40px; margin: 0 15px;">
                        <img src="/files/logos_act/uft.png" style="height: 40px; margin: 0 15px;">
                        <img src="/files/logos_act/fapt.png" style="height: 40px; margin: 0 15px;">
                        <img src="/files/logos_act/mds.png" style="height: 40px; margin: 0 15px;">
                    </div>
                `;
            }
        }
    });
    """

    ws = frappe.get_single("Website Settings")
    ws.javascript = JS_CODE
    ws.save(ignore_permissions=True)
    frappe.db.commit()
    print("✅ Javascript global injetado.")

    frappe.clear_cache()
    print("✅ Cache limpo.")

