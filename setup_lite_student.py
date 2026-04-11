import requests
import json

# Script para criar aluno de teste no Novo LMS Lite
URL = "http://localhost:8000/student"

student_data = {
    "whatsapp": "5563999374165",
    "name": "Rafael Teste LMS Lite",
    "email": "rafael@tds.local",
    "sisec_data": {
        "localidade": "Palmas-TO",
        "interesse": "Audiovisual",
        "objetivo": "Aprender a editar vídeos para divulgar minha pequena produção de mel."
    }
}

try:
    res = requests.post(URL, json=student_data)
    if res.status_code == 200:
        print("✅ Aluno de teste criado no LMS Lite com sucesso!")
    else:
        print(f"⚠️ Aviso: {res.json().get('detail', 'Erro desconhecido')}")
except Exception as e:
    print(f"❌ Erro ao conectar na API: {e}")
