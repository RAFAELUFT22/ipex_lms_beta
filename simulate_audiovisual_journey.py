import requests
import json
import sys
import os

# Ensure we can import lms_lite_tutor
sys.path.append("/root/projeto-tds")
from lms_lite_tutor import ask_tutor_lite

LMS_API_URL = "http://localhost:8000"
COURSES_FILE = "/root/projeto-tds/courses/tds/tds-courses-2026.json"
STUDENT_WHATSAPP = "5563999374165"
COURSE_SLUG = "audiovisual-e-produ-o-de-conte-do-digital-2"

def main():
    # 1. Register student if not exists (to be safe)
    print(f"--- Registrando/Atualizando Aluno {STUDENT_WHATSAPP} (Rafael) ---")
    student_data = {
        "whatsapp": STUDENT_WHATSAPP,
        "name": "Rafael",
        "sisec_data": {
            "municipio": "Araguaína",
            "perfil": "Pequeno Produtor",
            "objetivo": "Aprender a divulgar meus produtos"
        }
    }
    try:
        res = requests.post(f"{LMS_API_URL}/student", json=student_data)
        if res.status_code == 200:
            print("Aluno registrado com sucesso.\n")
        else:
            print(f"Erro ao registrar aluno: {res.status_code}\n")
    except Exception as e:
        print(f"Falha ao conectar na API: {e}\n")
        return

    # 2. Load courses and find the Audiovisual one
    print(f"--- Lendo lições do curso: {COURSE_SLUG} ---")
    with open(COURSES_FILE, 'r') as f:
        courses = json.load(f)
    
    course = next((c for c in courses if c['slug'] == COURSE_SLUG), None)
    if not course:
        print(f"Erro: Curso '{COURSE_SLUG}' não encontrado!")
        return

    # Flatten lessons
    lessons = []
    for chapter in course['chapters']:
        for lesson in chapter['lessons']:
            lessons.append(lesson['title'])
    
    total_lessons = len(lessons)
    print(f"Total de lições: {total_lessons}\n")

    # 3. Simulate journey
    for i, lesson_title in enumerate(lessons):
        progress = int(((i + 1) / total_lessons) * 100)
        print(f"--- [Lição {i+1}/{total_lessons}] {lesson_title} (Progresso: {progress}%) ---")
        
        # Update progress
        try:
            update_res = requests.post(f"{LMS_API_URL}/update_progress", json={
                "whatsapp": STUDENT_WHATSAPP,
                "course_slug": COURSE_SLUG,
                "progress": progress
            })
            if update_res.status_code != 200:
                print(f"Aviso: Erro ao atualizar progresso: {update_res.status_code}")
        except Exception as e:
            print(f"Aviso: Falha ao atualizar progresso: {e}")

        # Simulate student question
        question = f"Sobre a lição '{lesson_title}', como isso pode me ajudar na prática em Araguaína?"
        print(f"👤 Aluno: {question}")
        
        # Call tutor
        try:
            answer = ask_tutor_lite(STUDENT_WHATSAPP, question, course_context=course['title'])
            print(f"🤖 Tutor: {answer}\n")
        except Exception as e:
            print(f"🤖 Tutor: Erro ao obter resposta da IA: {e}\n")

    # 4. Final Status
    print(f"--- Status Final do Aluno {STUDENT_WHATSAPP} ---")
    try:
        final_res = requests.get(f"{LMS_API_URL}/student/{STUDENT_WHATSAPP}")
        if final_res.status_code == 200:
            print(json.dumps(final_res.json(), indent=2, ensure_ascii=False))
        else:
            print(f"Erro ao consultar status final: {final_res.status_code}")
    except Exception as e:
        print(f"Falha ao consultar status final: {e}")

if __name__ == "__main__":
    main()
