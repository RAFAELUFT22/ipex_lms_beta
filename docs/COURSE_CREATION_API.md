# Criação de Cursos via API — Frappe LMS

> Guia completo para criar cursos, capítulos, lições e quizzes via REST API.
> Referência para scripts automatizados e assistentes IA.

---

## Autenticação

Todos os requests usam **Token Auth**:

```http
Authorization: token {API_KEY}:{API_SECRET}
Content-Type: application/json
Accept: application/json
```

Base URL: `https://lms.extensionista.site` (ou `FRAPPE_LMS_URL` do `.env`)

---

## Hierarquia de DocTypes

```
LMS Course                    # Curso principal
├── Course Chapter            # Capítulo (agrupamento temático)
│   └── Course Lesson         # Lição (conteúdo individual)
│       └── (quiz_id → LMS Quiz)
│
LMS Quiz                      # Quiz independente
├── LMS Quiz Question         # Pergunta (child table inline)
│   └── LMS Option            # Opção de resposta (child table)
│
LMS Enrollment                # Matrícula aluno ↔ curso
LMS Certificate               # Certificado gerado
LMS Batch                     # Turma (agrupa cursos + alunos)
LMS Category                  # Categoria de cursos
```

---

## 1. Criar um Curso (`LMS Course`)

```bash
curl -X POST "https://lms.extensionista.site/api/resource/LMS Course" \
  -H "Authorization: token KEY:SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Gestão Financeira para Empreendimentos",
    "short_introduction": "Controle caixa, custos e margens.",
    "description": "<p>Aprenda gestão financeira para seu negócio.</p>",
    "published": 1,
    "status": "Approved",
    "paid_course": 0,
    "currency": "BRL",
    "image": "",
    "video_link": "",
    "instructors": [
      {"instructor": "Administrator"}
    ]
  }'
```

### Campos do `LMS Course`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|:-----------:|-----------|
| `title` | String | ✅ | Título do curso |
| `short_introduction` | String | | Descrição curta (catálogo) |
| `description` | HTML | | Descrição longa (rich text) |
| `published` | 0/1 | | Publicar no portal |
| `status` | String | | `"Under Review"`, `"Approved"` |
| `paid_course` | 0/1 | | Curso pago? |
| `course_price` | Float | | Preço (se pago) |
| `currency` | String | | `"BRL"`, `"USD"` |
| `image` | String | | URL da imagem de capa |
| `video_link` | String | | URL do vídeo introdutório |
| `instructors` | Child Table | | Lista de `{"instructor": "user@email"}` |

### Resposta

```json
{
  "data": {
    "name": "gestao-financeira-para-empreendimentos",
    "title": "Gestão Financeira para Empreendimentos",
    "creation": "2026-03-04 19:00:00",
    ...
  }
}
```

> ⚠️ O campo `name` (slug) é gerado automaticamente pelo Frappe. Use-o como referência para criar capítulos.

---

## 2. Criar um Capítulo (`Course Chapter`)

```bash
curl -X POST "https://lms.extensionista.site/api/resource/Course Chapter" \
  -H "Authorization: token KEY:SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fundamentos Financeiros",
    "course": "gestao-financeira-para-empreendimentos",
    "idx": 1
  }'
```

### Campos do `Course Chapter`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|:-----------:|-----------|
| `title` | String | ✅ | Título do capítulo |
| `course` | Link | ✅ | `name` do LMS Course pai |
| `idx` | Int | | Ordem (1, 2, 3...) |
| `description` | Text | | Descrição do capítulo |

---

## 3. Criar uma Lição (`Course Lesson`)

```bash
curl -X POST "https://lms.extensionista.site/api/resource/Course Lesson" \
  -H "Authorization: token KEY:SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "O que é gestão financeira?",
    "chapter": "CHAPTER-NAME-HERE",
    "course": "gestao-financeira-para-empreendimentos",
    "body": "### Introdução\n\nConteúdo em **Markdown** renderizado como HTML.",
    "content": "{\"blocks\": []}",
    "published": 1,
    "idx": 1,
    "youtube": "dQw4w9WgXcQ",
    "quiz_id": ""
  }'
```

### Campos do `Course Lesson`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|:-----------:|-----------|
| `title` | String | ✅ | Título da lição |
| `chapter` | Link | ✅ | `name` do Course Chapter |
| `course` | Link | ✅ | `name` do LMS Course |
| `body` | HTML/MD | | Conteúdo principal (Markdown ou HTML) |
| `content` | JSON | | EditorJS content blocks |
| `youtube` | String | | YouTube video ID (sem URL completa) |
| `quiz_id` | Link | | `name` do LMS Quiz vinculado |
| `published` | 0/1 | | Publicar a lição |
| `idx` | Int | | Ordem dentro do capítulo |
| `include_in_preview` | 0/1 | | Disponível sem matrícula |

### Tipos de Conteúdo Suportados

1. **Rich Text** — campo `body` com HTML/Markdown
2. **Vídeo YouTube** — campo `youtube` com o ID do vídeo
3. **EditorJS Blocks** — campo `content` com JSON estruturado
4. **Quiz** — vinculado via `quiz_id`
5. **Upload de Arquivo** — via `/api/method/upload_file` separado

---

## 4. Criar um Quiz (`LMS Quiz`)

```bash
curl -X POST "https://lms.extensionista.site/api/resource/LMS Quiz" \
  -H "Authorization: token KEY:SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Quiz — Fundamentos Financeiros",
    "max_attempts": 3,
    "passing_percentage": 70,
    "show_submission_history": 1
  }'
```

### Campos do `LMS Quiz`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|:-----------:|-----------|
| `title` | String | ✅ | Título do quiz |
| `max_attempts` | Int | | Máximo de tentativas (0 = ilimitado) |
| `passing_percentage` | Float | | % mínimo para aprovação |
| `show_submission_history` | 0/1 | | Mostrar histórico ao aluno |

### 4.1 Adicionar Questão Separadamente (`LMS Question`)

```bash
curl -X POST "https://lms.extensionista.site/api/resource/LMS Question" \
  -H "Authorization: token KEY:SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Qual é a diferença entre custo e despesa?",
    "type": "Choices",
    "multiple_correct_answer": 0,
    "options": [
      {"option": "Não há diferença", "is_correct": 0},
      {"option": "Custo é produção, despesa é fixo", "is_correct": 1},
      {"option": "Custo é variável, despesa é receita", "is_correct": 0}
    ]
  }'
```

### 4.2 Vincular Questão ao Quiz (`LMS Quiz Question`)

```bash
curl -X POST "https://lms.extensionista.site/api/resource/LMS Quiz Question" \
  -H "Authorization: token KEY:SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": "QUIZ-NAME-HERE",
    "parenttype": "LMS Quiz",
    "parentfield": "questions",
    "question": "QUESTION-NAME-HERE",
    "marks": 1
  }'
```

---

## 5. Matricular Aluno (`LMS Enrollment`)

```bash
curl -X POST "https://lms.extensionista.site/api/resource/LMS Enrollment" \
  -H "Authorization: token KEY:SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "member": "aluno@email.com",
    "course": "gestao-financeira-para-empreendimentos"
  }'
```

> ⚠️ O aluno (`member`) precisa ser um **User** existente no Frappe.

---

## 6. Upload de Arquivo

```bash
curl -X POST "https://lms.extensionista.site/api/method/upload_file" \
  -H "Authorization: token KEY:SECRET" \
  -F "file=@/path/to/image.jpg" \
  -F "doctype=LMS Course" \
  -F "docname=gestao-financeira-para-empreendimentos" \
  -F "fieldname=image" \
  -F "is_private=0"
```

---

## 7. Listar com Filtros

```bash
# Listar cursos publicados
curl "https://lms.extensionista.site/api/resource/LMS Course?\
fields=[\"name\",\"title\",\"short_introduction\"]&\
filters=[[\"published\",\"=\",1]]&\
limit_page_length=20" \
  -H "Authorization: token KEY:SECRET"

# Buscar lições de um curso
curl "https://lms.extensionista.site/api/resource/Course Lesson?\
filters=[[\"course\",\"=\",\"gestao-financeira-para-empreendimentos\"]]&\
fields=[\"name\",\"title\",\"idx\"]&\
order_by=idx asc" \
  -H "Authorization: token KEY:SECRET"
```

### Operadores de Filtro

| Operador | Exemplo | Descrição |
|----------|---------|-----------|
| `=` | `["status","=","Approved"]` | Igualdade |
| `!=` | `["status","!=","Draft"]` | Diferente |
| `like` | `["title","like","%financ%"]` | Contém texto |
| `>`, `<`, `>=`, `<=` | `["progress",">",50]` | Comparação numérica |
| `in` | `["status","in",["Approved","Draft"]]` | Está na lista |
| `between` | `["creation","between",["2026-01-01","2026-12-31"]]` | Intervalo |

---

## 8. Atualizar Documento (PUT)

```bash
curl -X PUT "https://lms.extensionista.site/api/resource/LMS Course/COURSE-NAME" \
  -H "Authorization: token KEY:SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "short_introduction": "Nova descrição atualizada"
  }'
```

---

## 9. Deletar Documento (DELETE)

```bash
curl -X DELETE "https://lms.extensionista.site/api/resource/LMS Course/COURSE-NAME" \
  -H "Authorization: token KEY:SECRET"
```

---

## Fluxo Completo: Criar Curso com 1 Capítulo + 2 Lições + Quiz

```python
import requests

URL = "https://lms.extensionista.site"
HEADERS = {
    "Authorization": "token KEY:SECRET",
    "Content-Type": "application/json"
}

def create(doctype, data):
    r = requests.post(f"{URL}/api/resource/{doctype}", headers=HEADERS, json=data)
    r.raise_for_status()
    return r.json()["data"]

# 1. Curso
course = create("LMS Course", {
    "title": "Meu Curso",
    "short_introduction": "Descrição curta",
    "published": 1,
    "status": "Approved",
    "paid_course": 0,
    "instructors": [{"instructor": "Administrator"}]
})

# 2. Capítulo
chapter = create("Course Chapter", {
    "title": "Capítulo 1",
    "course": course["name"],
    "idx": 1
})

# 3. Lição
lesson = create("Course Lesson", {
    "title": "Lição 1",
    "chapter": chapter["name"],
    "course": course["name"],
    "body": "Conteúdo da lição em Markdown",
    "published": 1,
    "idx": 1
})

# 4. Quiz
quiz = create("LMS Quiz", {
    "title": "Quiz Cap 1",
    "max_attempts": 3,
    "passing_percentage": 70
})

# 5. Questão
question = create("LMS Question", {
    "question": "Qual a resposta?",
    "type": "Choices",
    "options": [
        {"option": "A", "is_correct": 0},
        {"option": "B (correta)", "is_correct": 1},
        {"option": "C", "is_correct": 0}
    ]
})

# 6. Vincular quiz ao lesson
requests.put(
    f"{URL}/api/resource/Course Lesson/{lesson['name']}",
    headers=HEADERS,
    json={"quiz_id": quiz["name"]}
)

print(f"✅ Curso criado: {course['name']}")
```

---

## Referências Oficiais

- [Frappe REST API](https://frappeframework.com/docs/user/en/api/rest) — Documentação oficial
- [Frappe Document API v2](https://frappeframework.com/docs/user/en/api/document) — API v2 (Frappe v15+)
- [Frappe LMS GitHub](https://github.com/frappe/lms) — Código-fonte dos doctypes
- [Frappe LMS Docs](https://frappelms.com) — Site oficial do LMS
- [Frappe Filtering](https://frappeframework.com/docs/user/en/api/listing) — Filtros e paginação
