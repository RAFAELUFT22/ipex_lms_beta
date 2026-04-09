import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("FRAPPE_LMS_URL")
API_KEY = os.getenv("FRAPPE_API_KEY")
API_SECRET = os.getenv("FRAPPE_API_SECRET")

headers = {
    "Authorization": f"token {API_KEY}:{API_SECRET}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def upload_file(file_path):
    print(f"Uploading {file_path}...")
    if not os.path.exists(file_path):
        print(f" ❌ File not found: {file_path}")
        return None
    url = f"{BASE_URL}/api/method/upload_file"
    files = {'file': (os.path.basename(file_path), open(file_path, 'rb'))}
    # Note: Authorization header is required
    upload_headers = {"Authorization": f"token {API_KEY}:{API_SECRET}"}
    response = requests.post(url, headers=upload_headers, files=files)
    if response.status_code == 200:
        file_url = response.json().get("message", {}).get("file_url")
        print(f" ✅ Uploaded: {file_url}")
        return file_url
    return None

def update_lms_settings(logo_url):
    print("Updating LMS Settings...")
    url = f"{BASE_URL}/api/resource/LMS Settings/LMS Settings"
    data = {
        "portal_name": "Territórios de Desenvolvimento Social e Inclusão Produtiva TDS",
        "portal_description": "Território de Desenvolvimento Social e Inclusão Produtiva",
        "brand_logo": logo_url
    }
    response = requests.put(url, headers=headers, json=data)
    if response.status_code == 200:
        print("✅ LMS Settings updated with TDS Logo.")
    else:
        print(f"❌ Error updating LMS Settings: {response.text}")

def create_course(title, intro, description, program_name):
    print(f"Creating Course '{title}'...")
    url = f"{BASE_URL}/api/resource/LMS Course"
    
    check = requests.get(f"{url}/{title}", headers=headers)
    if check.status_code == 200:
        print(f" ℹ️ Course '{title}' already exists.")
        return title

    data = {
        "title": title,
        "is_published": 1,
        "short_introduction": intro,
        "description": description,
        "instructors": [{"instructor": "Administrator"}]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f" ✅ Course '{title}' created.")
        link_to_program(title, program_name)
        return title
    return None

def link_to_program(course_name, program_name):
    print(f"Linking '{course_name}' to Program '{program_name}'...")
    url = f"{BASE_URL}/api/resource/LMS Program Course"
    data = {"parent": program_name, "parenttype": "LMS Program", "parentfield": "courses", "course": course_name}
    requests.post(url, headers=headers, json=data)

if __name__ == "__main__":
    # 1. Branding (OFFICIAL LOGO)
    logo_path = "/root/projeto-tds/arquivos_do_projeto/logos/logo_tds_oficial.png"
    logo_url = upload_file(logo_path)
    if logo_url:
        update_lms_settings(logo_url)
    
    # 2. Academy structure setup
    course_data = [
        {"title": "Atendimento ao Cliente", "program": "Empreendedorismo Popular e Gestão de Negócios", "intro": "Fundamentos para pequenos negócios.", "desc": "Aborda comunicação interpessoal e estratégias de fidelização."},
        {"title": "Educação Financeira", "program": "Empreendedorismo Popular e Gestão de Negócios", "intro": "Planejamento e gestão de recursos.", "desc": "Gestão de receitas, despesas e investimentos para microempreendedores."},
        {"title": "Inteligência Artificial", "program": "Empreendedorismo Popular e Gestão de Negócios", "intro": "IA para microempreendimentos.", "desc": "Uso prático de ferramentas de IA para automação e marketing."},
        {"title": "Associativismo e Cooperativismo", "program": "Formação Cooperativista Popular", "intro": "Fundamentos de organização coletiva.", "desc": "Princípios do cooperativismo e autogestão."},
        {"title": "Orientações SIM e SIMA", "program": "Agricultura Familiar e Políticas Públicas Federais", "intro": "Regularização sanitária.", "desc": "Acesso ao Serviço de Inspeção Municipal e certificações."},
        {"title": "Agricultura Sustentável", "program": "Sistemas Produtivos Sustentáveis e Tecnologias Sociais", "intro": "Produção em equilíbrio com a natureza.", "desc": "Agroecologia, manejo de solo e água."},
        {"title": "Audiovisual", "program": "Sistemas Produtivos Sustentáveis e Tecnologias Sociais", "intro": "Comunicação e valorização territorial.", "desc": "Produção de conteúdo audiovisual para promoção da região."},
        {"title": "Elaboração de Projetos", "program": "Inovação e Certificação Agroecológica", "intro": "Concepção de projetos produtivos.", "desc": "Escrita técnica e captação de recursos."},
    ]

    for c in course_data:
        create_course(c['title'], c['intro'], c['desc'], c['program'])
    
    print("\n🚀 Academy structure setup completed with final branding!")
