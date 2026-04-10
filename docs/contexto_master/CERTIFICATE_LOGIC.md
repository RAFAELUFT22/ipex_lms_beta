# Lógica de Emissão de Certificados

## Conceito Central

O certificado é emitido **automaticamente** pelo n8n quando o aluno conclui
**todos os quizzes** vinculados ao material do curso que está registrado como
Workspace no AnythingLLM.

---

## 1. Estrutura de Dados Necessária (PostgreSQL)

```sql
-- Cursos cadastrados (espelha workspaces do AnythingLLM)
CREATE TABLE courses (
    id          SERIAL PRIMARY KEY,
    tenant_id   VARCHAR(50) NOT NULL,          -- ex: 'tds_001'
    slug        VARCHAR(100) UNIQUE NOT NULL,  -- espelha workspace slug
    title       VARCHAR(255) NOT NULL,
    total_quizzes INT NOT NULL DEFAULT 0
);

-- Quizzes gerados por curso
CREATE TABLE quizzes (
    id          SERIAL PRIMARY KEY,
    course_id   INT REFERENCES courses(id),
    question    TEXT NOT NULL,
    options     JSONB NOT NULL,               -- {"a":"..","b":"..","c":"..","d":".."}
    correct     CHAR(1) NOT NULL,             -- 'a' | 'b' | 'c' | 'd'
    chapter     VARCHAR(100)
);

-- Progresso individual do aluno
CREATE TABLE student_progress (
    id            SERIAL PRIMARY KEY,
    student_phone VARCHAR(20) NOT NULL,       -- identificador principal (WhatsApp)
    course_id     INT REFERENCES courses(id),
    quiz_id       INT REFERENCES quizzes(id),
    answered_at   TIMESTAMPTZ DEFAULT NOW(),
    is_correct    BOOLEAN NOT NULL,
    UNIQUE(student_phone, quiz_id)
);

-- Certificados emitidos
CREATE TABLE certificates (
    id            SERIAL PRIMARY KEY,
    student_phone VARCHAR(20) NOT NULL,
    course_id     INT REFERENCES courses(id),
    issued_at     TIMESTAMPTZ DEFAULT NOW(),
    pdf_url       TEXT,                       -- link S3/MinIO do PDF
    UNIQUE(student_phone, course_id)          -- 1 certificado por curso por aluno
);
```

---

## 2. Fluxo de Conclusão (n8n)

```
Aluno responde quiz
      |
      v
[n8n: Registrar resposta] --> student_progress
      |
      v
[n8n: Verificar conclusão]
  SELECT COUNT(*) FROM student_progress
  WHERE student_phone = ? AND course_id = ? AND is_correct = true
      |
      v
  COUNT == courses.total_quizzes ?
      |              |
     NÃO            SIM
      |              |
  Continuar     [n8n: Gerar Certificado]
                     |
                     v
            [Puppeteer/HTML → PDF]
                     |
                     v
            [Upload → MinIO/S3]
                     |
                     v
            INSERT INTO certificates
                     |
                     v
            [Enviar PDF via WhatsApp]
```

---

## 3. Geração do Certificado (PDF)

**Ferramenta recomendada:** Nó `HTTP Request` do n8n chamando um serviço leve de
PDF. Opções:

| Opção | Implementação | Custo |
| :--- | :--- | :--- |
| **Gotenberg** | Container Docker (`gotenberg/gotenberg`) | Free / Self-hosted |
| **Puppeteer via n8n Code** | Script JS no nó Code | Free |
| **API HTML2PDF.io** | Chamada REST externa | Freemium |

**Recomendação:** Usar **Gotenberg** (já rodando no Dokploy como serviço auxiliar).

### Template HTML do Certificado

O certificado deve conter:
- Logo do parceiro (tenant) — carregado do banco via `tenant_id`
- Nome do aluno
- Título do curso
- Data de conclusão
- Código de verificação único (`UUID`)
- Assinatura digital visual (imagem)

---

## 4. Endpoint de Validação Pública

Após emissão, o certificado deve ser verificável publicamente:

```
GET /certificado/verificar?codigo={UUID}
```

Retorna: Nome do aluno, curso, data, instituição — sem expor dados sensíveis.

---

## 5. Critério de Aprovação

| Parâmetro | Valor Padrão | Onde configurar |
| :--- | :--- | :--- |
| Nota mínima para aprovação | **70%** de acertos | Variável no n8n |
| Tentativas por quiz | **3 tentativas** | Variável no n8n |
| Geração automática de quiz | Via AnythingLLM API | Workspace slug |

### Como o n8n gera os quizzes do AnythingLLM:

```http
POST /api/v1/workspace/{slug}/chat
{
  "message": "Gere 5 questões de múltipla escolha sobre o conteúdo deste workspace. Formato: JSON com campos: question, options (a/b/c/d), correct.",
  "mode": "chat"
}
```

O n8n parseia o JSON retornado e insere na tabela `quizzes`.
