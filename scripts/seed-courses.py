#!/usr/bin/env python3
"""
seed-courses.py — Cria cursos no Frappe LMS via REST API

Lê arquivos JSON de courses/templates/ ou courses/tds/ e cria:
  LMS Course → Course Chapter → Course Lesson → LMS Quiz (com questões)

USO:
  python3 scripts/seed-courses.py                    # cria cursos de courses/tds/
  python3 scripts/seed-courses.py --dir courses/templates  # de outro diretório
  python3 scripts/seed-courses.py --dry-run           # apenas exibe o que faria

VARIÁVEIS DE AMBIENTE (.env):
  FRAPPE_LMS_URL, FRAPPE_API_KEY, FRAPPE_API_SECRET
"""

import os
import sys
import json
import glob
import argparse
import requests
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
FRAPPE_URL = os.getenv("FRAPPE_LMS_URL", "https://lms.extensionista.site")
API_KEY    = os.getenv("FRAPPE_API_KEY", "")
API_SECRET = os.getenv("FRAPPE_API_SECRET", "")

HEADERS = {
    "Authorization": f"token {API_KEY}:{API_SECRET}",
    "Content-Type":  "application/json",
    "Accept":        "application/json",
}


def api_get(doctype: str, filters: list | None = None, fields: list | None = None):
    """GET /api/resource/{doctype} com filtros."""
    params = {}
    if filters:
        params["filters"] = json.dumps(filters)
    if fields:
        params["fields"] = json.dumps(fields)
    resp = requests.get(f"{FRAPPE_URL}/api/resource/{doctype}", headers=HEADERS, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("data", [])


def api_post(doctype: str, data: dict):
    """POST /api/resource/{doctype} — cria um documento."""
    resp = requests.post(f"{FRAPPE_URL}/api/resource/{doctype}", headers=HEADERS, json=data, timeout=30)
    if resp.status_code == 200:
        return resp.json().get("data")
    elif resp.status_code == 409:
        print(f"    ⚠️  {doctype} já existe — pulando")
        return None
    else:
        print(f"    ❌ Erro ao criar {doctype}: {resp.status_code} — {resp.text[:200]}")
        return None


def course_exists(title: str) -> bool:
    """Verifica se um curso com este título já existe."""
    results = api_get("LMS Course", filters=[["title", "=", title]], fields=["name"])
    return len(results) > 0


def create_course_from_json(data: dict, dry_run: bool = False):
    """Cria um curso completo a partir de um dict JSON."""
    title = data["title"]

    if course_exists(title):
        print(f"  ⚠️  Curso '{title}' já existe — pulando")
        return

    if dry_run:
        chapters = data.get("chapters", [])
        lessons = sum(len(ch.get("lessons", [])) for ch in chapters)
        quizzes = sum(1 for ch in chapters for le in ch.get("lessons", []) if le.get("quiz"))
        print(f"  🔍 [DRY-RUN] Criaria: '{title}' ({len(chapters)} caps, {lessons} lições, {quizzes} quizzes)")
        return

    print(f"\n📘 Criando curso: {title}")

    # 1. Criar o curso
    course = api_post("LMS Course", {
        "title":              title,
        "short_introduction": data.get("description", ""),
        "description":        f"<p>{data.get('description', '')}</p>",
        "published":          1,
        "status":             "Approved",
        "paid_course":        0,
        "currency":           "BRL",
        "instructors":        [{"instructor": data.get("instructor", "Administrator")}],
    })
    if not course:
        return

    course_name = course["name"]

    # 2. Criar capítulos
    for i, ch_data in enumerate(data.get("chapters", []), start=1):
        print(f"  📂 Capítulo {i}: {ch_data['title']}")
        chapter = api_post("Course Chapter", {
            "title":  ch_data["title"],
            "course": course_name,
            "idx":    i,
        })
        if not chapter:
            continue

        chapter_name = chapter["name"]

        # 3. Criar lições
        for j, le_data in enumerate(ch_data.get("lessons", []), start=1):
            print(f"    📄 Lição {j}: {le_data['title']}")

            lesson_payload = {
                "title":     le_data["title"],
                "chapter":   chapter_name,
                "course":    course_name,
                "body":      le_data.get("body", le_data.get("content", "")),
                "content":   le_data.get("editor_content", '{"blocks": []}'),
                "published": 1,
                "idx":       j,
            }

            # YouTube video
            if le_data.get("youtube_video_id"):
                lesson_payload["youtube"] = le_data["youtube_video_id"]

            lesson = api_post("Course Lesson", lesson_payload)

            # 4. Criar quiz se existir
            if lesson and le_data.get("quiz"):
                quiz_data = le_data["quiz"]
                print(f"      📝 Quiz: {quiz_data['title']}")

                questions = []
                for q in quiz_data.get("questions", []):
                    options = [
                        {"option": opt["text"], "is_correct": opt.get("correct", False)}
                        for opt in q.get("options", [])
                    ]
                    questions.append({
                        "question": q["question"],
                        "type": q.get("type", "Choices"),
                        "multiple_correct_answer": 0,
                        "options": options,
                    })

                quiz = api_post("LMS Quiz", {
                    "title":                quiz_data["title"],
                    "max_attempts":         quiz_data.get("max_attempts", 3),
                    "passing_percentage":   quiz_data.get("passing_percentage", 70),
                    "show_submission_history": 1,
                    "questions": [{"question": q["question"], "question_detail": questions[i]}
                                  for i, q in enumerate(quiz_data.get("questions", []))],
                })

                # Vincular quiz à lição (se suportado pela versão do LMS)
                if quiz:
                    try:
                        requests.put(
                            f"{FRAPPE_URL}/api/resource/Course Lesson/{lesson['name']}",
                            headers=HEADERS,
                            json={"quiz_id": quiz["name"]},
                            timeout=10,
                        )
                    except Exception:
                        pass

    print(f"  ✅ Curso '{title}' criado com sucesso!")


def main():
    parser = argparse.ArgumentParser(description="Seed cursos no Frappe LMS via REST API")
    parser.add_argument("--dir", default="courses/tds", help="Diretório com JSONs de cursos")
    parser.add_argument("--file", help="Arquivo JSON específico para criar")
    parser.add_argument("--dry-run", action="store_true", help="Apenas mostra o que faria")
    args = parser.parse_args()

    if not API_KEY or not API_SECRET:
        print("❌ FRAPPE_API_KEY e FRAPPE_API_SECRET devem estar definidos no .env")
        print("   Execute: source .env")
        sys.exit(1)

    # Testar conexão
    try:
        resp = requests.get(f"{FRAPPE_URL}/api/method/ping", headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            print(f"❌ Frappe LMS inacessível em {FRAPPE_URL} (status {resp.status_code})")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Erro de conexão com {FRAPPE_URL}: {e}")
        sys.exit(1)

    print(f"✅ Conectado ao Frappe LMS: {FRAPPE_URL}")

    if args.file:
        files = [args.file]
    else:
        files = sorted(glob.glob(os.path.join(args.dir, "*.json")))

    if not files:
        print(f"⚠️  Nenhum JSON encontrado em {args.dir}/")
        sys.exit(0)

    print(f"📦 {len(files)} arquivo(s) encontrado(s)")

    for f in files:
        with open(f) as fp:
            data = json.load(fp)

        if isinstance(data, list):
            for course in data:
                create_course_from_json(course, dry_run=args.dry_run)
        else:
            create_course_from_json(data, dry_run=args.dry_run)

    print("\n🎉 Seed concluído!")


if __name__ == "__main__":
    main()
