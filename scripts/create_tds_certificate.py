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

# Caminhos das logos (já enviadas no branding anterior)
LOGO_TDS = "/files/logo_tds_oficial.png"
LOGO_UFT = "/files/uft logo.png"

JINJA_TEMPLATE = """
<div class="certificate-container" style="padding: 40px; border: 15px solid #003366; background-color: #fff; font-family: 'Inter', sans-serif; position: relative; min-height: 600px;">
    
    <!-- Cabeçalho Institucional -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 50px;">
        <img src="{{ logo_uft }}" style="max-height: 70px;">
        <div style="text-align: center;">
            <h4 style="margin: 0; color: #003366; font-weight: bold;">PROJETO TDS</h4>
            <p style="margin: 0; font-size: 12px; color: #666;">Inclusão Produtiva e Inovação Territorial</p>
        </div>
        <img src="{{ logo_tds }}" style="max-height: 80px;">
    </div>

    <!-- Título Celebrativo -->
    <div style="text-align: center; margin-bottom: 40px;">
        <h1 style="color: #008080; font-size: 48px; margin-bottom: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px;">
            Certificado de Conquista
        </h1>
        <div style="width: 100px; height: 4px; background-color: #F9C300; margin: 0 auto;"></div>
    </div>

    <!-- Texto Cativo -->
    <div style="text-align: center; padding: 0 50px; line-height: 1.8; color: #333; font-size: 20px;">
        Certificamos com alegria que 
        <br>
        <strong style="font-size: 28px; color: #003366; border-bottom: 2px solid #F9C300;">{{ doc.member_name }}</strong>
        <br>
        concluiu com êxito sua jornada de aprendizado no curso
        <br>
        <strong style="color: #008080;">{{ doc.course_title }}</strong>
        <br>
        sendo parte fundamental do ecossistema de transformação social e inovação regional do Tocantins.
    </div>

    <!-- Dados Dinâmicos -->
    <div style="margin-top: 50px; display: flex; justify-content: space-around; text-align: center; color: #555;">
        <div>
            <span style="display: block; font-size: 14px; text-transform: uppercase;">Carga Horária</span>
            <strong style="font-size: 18px; color: #003366;">{{ frappe.get_value("LMS Course", doc.course, "duration") or "20" }} horas</strong>
        </div>
        <div>
            <span style="display: block; font-size: 14px; text-transform: uppercase;">Conclusão em</span>
            <strong style="font-size: 18px; color: #003366;">{{ frappe.utils.format_date(doc.issue_date, "dd/mm/yyyy") }}</strong>
        </div>
    </div>

    <!-- Assinaturas e Selo -->
    <div style="margin-top: 80px; display: flex; justify-content: space-between; align-items: flex-end;">
        <div style="text-align: center; width: 250px;">
            <div style="border-top: 1px solid #999; padding-top: 5px;">
                <p style="margin: 0; font-size: 14px; font-weight: bold;">IPEX / UFT</p>
                <p style="margin: 0; font-size: 12px;">Coordenação Acadêmica</p>
            </div>
        </div>
        
        <!-- QR Code Placeholder (O Frappe gera automaticamente se configurado) -->
        <div style="text-align: center;">
             <p style="font-size: 10px; color: #999; margin-bottom: 5px;">Autenticidade garantida via ID: {{ doc.name }}</p>
             <div style="width: 60px; height: 60px; background: #eee; margin: 0 auto; display: flex; align-items: center; justify-content: center; font-size: 8px;">QR CODE</div>
        </div>

        <div style="text-align: center; width: 250px;">
            <div style="border-top: 1px solid #999; padding-top: 5px;">
                <p style="margin: 0; font-size: 14px; font-weight: bold;">PROJETO TDS</p>
                <p style="margin: 0; font-size: 12px;">Gestão de Inovação</p>
            </div>
        </div>
    </div>

    <!-- Faixa de Rodapé -->
    <div style="position: absolute; bottom: 0; left: 0; width: 100%; height: 10px; background: linear-gradient(to right, #003366, #008080, #F9C300);"></div>
</div>
"""

def create_print_format():
    print("🎨 Criando Print Format do Certificado TDS...")
    
    # Injetar variáveis fixas no template via substituição simples antes de enviar para o Jinja do Frappe
    full_html = JINJA_TEMPLATE.replace("{{ logo_uft }}", LOGO_UFT).replace("{{ logo_tds }}", LOGO_TDS)

    payload = {
        "name": "Certificado Oficial TDS",
        "doc_type": "LMS Certificate",
        "format": "Jinja",
        "standard": "No",
        "custom_format": 1,
        "html": full_html,
        "print_format_type": "Jinja",
        "font_size": 14,
        "margin_top": 0,
        "margin_bottom": 0,
        "margin_left": 0,
        "margin_right": 0,
        "page_number": "Hide",
        "disabled": 0
    }

    # Verificar se já existe e atualizar, ou criar novo
    check_res = requests.get(f"{BASE_URL}/api/resource/Print Format/Certificado Oficial TDS", headers=headers)
    
    if check_res.status_code == 200:
        print("📝 Atualizando Print Format existente...")
        res = requests.put(f"{BASE_URL}/api/resource/Print Format/Certificado Oficial TDS", headers=headers, json=payload)
    else:
        print("🆕 Criando novo Print Format...")
        res = requests.post(f"{BASE_URL}/api/resource/Print Format", headers=headers, json=payload)

    if res.status_code in [200, 201]:
        print("✅ Certificado Oficial TDS configurado com sucesso!")
    else:
        print(f"❌ Erro ao configurar certificado: {res.status_code} {res.text}")

if __name__ == "__main__":
    create_print_format()
