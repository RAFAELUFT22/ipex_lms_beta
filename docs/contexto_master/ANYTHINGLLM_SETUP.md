# Guia de Uso Inteligente do AnythingLLM

## Acesso
- **URL:** https://rag.ipexdesenvolvimento.cloud
- **Quem usa:** Coordenadores, professores, equipe TDS
- **API Key (admin):** `W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0`

---

## 1. Para que serve o AnythingLLM neste projeto

O AnythingLLM é o **"cérebro"** do sistema. Ele:
1. Armazena o material dos cursos (PDFs, textos, apresentações)
2. Responde perguntas dos alunos usando esse material (RAG)
3. Gera as perguntas dos quizzes automaticamente
4. Mantém histórico das conversas

Cada **Workspace** = um curso diferente. Os alunos não acessam diretamente —
eles conversam via WhatsApp e o n8n consulta o AnythingLLM nos bastidores.

---

## 2. Como um coordenador adiciona material de curso

**Passo a passo (sem precisar de técnico):**

1. Acesse https://rag.ipexdesenvolvimento.cloud
2. Clique no Workspace do seu curso (ex: "Gestão Financeira")
3. Clique em **"Upload Documents"** (ícone de clipe)
4. Envie os arquivos: PDF, DOCX, TXT, ou cole texto diretamente
5. Clique em **"Save & Embed"** — aguarde a barra de progresso

O conteúdo fica disponível para os alunos imediatamente após o embed.

**Formatos aceitos:**
- PDF (apostilas, cartilhas do SEBRAE, manuais)
- Word (.docx) — ementas, planos de aula
- Texto simples (.txt)
- Links de sites (via URL Scraper)

---

## 3. Estrutura de Workspaces por Curso

| Workspace Slug | Curso | Responsável |
| :--- | :--- | :--- |
| `gestao-financeira` | Gestão Financeira para Empreendimentos | Coordenação TDS |
| `seguranca-alimentar` | Boas Práticas na Manipulação de Alimentos | Coordenação TDS |
| `organizacao-producao` | Organização da Produção para o Mercado | Coordenação TDS |
| `marketing-digital` | Marketing Digital para Pequenos Negócios | Coordenação TDS |
| `matricula-baseline` | Workspace do bot de matrícula | Equipe Kreativ |

**Para criar um novo workspace (novo curso):**
1. AnythingLLM → "New Workspace"
2. Nome = título do curso
3. Anote o slug gerado (URL amigável)
4. Registre na tabela `courses` do banco de dados
5. Atualize o nó de mapeamento no n8n

---

## 4. Configuração do System Prompt por Workspace

Cada workspace deve ter um **System Prompt** que define como o tutor se
comporta. Configure em: Workspace → Settings → LLM Preference → System Prompt.

**Template base (adaptar por curso):**

```
Você é o Tutor do curso "[NOME DO CURSO]" do programa TDS — Transformação
Digital para Inclusão Social.

Seu papel é ser um companheiro de aprendizado, não um professor que apenas
deposita informação. Responda sempre com base nos documentos deste workspace.

Diretrizes de linguagem:
- Use português simples, direto e acolhedor
- Evite termos técnicos sem explicar o significado
- Reconheça o conhecimento que o aluno já traz da sua experiência de vida
- Se não souber a resposta pelo material, diga: "Essa pergunta vai além do
  material que tenho aqui. Vou chamar um orientador para te ajudar."

Quando o aluno pedir para fazer o quiz, responda:
"Ótimo! Vou preparar algumas perguntas sobre o que você estudou. Pode levar
um momento..." — e gere 5 questões de múltipla escolha em formato JSON.
```

---

## 5. Como o RAG funciona na prática

```
Aluno no WhatsApp: "O que é ponto de equilíbrio?"
         ↓
n8n encaminha para: POST /api/v1/workspace/gestao-financeira/chat
{
  "message": "O que é ponto de equilíbrio?",
  "mode": "chat",
  "sessionId": "whatsapp_5563999999999"
}
         ↓
AnythingLLM busca nos documentos do workspace a resposta mais relevante
         ↓
Resposta formatada é retornada ao n8n → enviada ao aluno pelo WhatsApp
```

O `sessionId` garante que a conversa tem memória dentro da mesma sessão.

---

## 6. Geração de Quiz via API

O n8n usa este prompt para gerar quizzes:

```http
POST /api/v1/workspace/{slug}/chat
{
  "message": "Gere exatamente 5 questões de múltipla escolha sobre os documentos deste workspace. Retorne SOMENTE um JSON válido no formato: [{\"question\": \"...\", \"options\": {\"a\": \"...\", \"b\": \"...\", \"c\": \"...\", \"d\": \"...\"}, \"correct\": \"a\", \"chapter\": \"...\"}]. Não adicione texto fora do JSON.",
  "mode": "query",
  "sessionId": "quiz-generator"
}
```

O modo `query` foca nos documentos (sem memória de conversa) — ideal para
geração de quizzes consistentes.

---

## 7. Lista de Alunos — Como visualizar

O AnythingLLM **não** armazena lista de alunos. Os dados dos alunos ficam em:
- **PostgreSQL** → tabela `students` (dados cadastrais)
- **Chatwoot** → histórico de conversas com identificação por telefone
- **n8n** → logs de execução de fluxos

Para visualizar progresso: acesse o portal em https://ipexdesenvolvimento.cloud/dashboard
(quando implementado) ou consulte o banco via n8n.

---

## 8. Boas Práticas para Coordenadores

| Faça | Evite |
| :--- | :--- |
| Upload de materiais em PDF (menos de 50MB) | Arquivos de imagem sem texto |
| Dividir cursos longos em workspaces menores | Um workspace com conteúdo de múltiplos cursos |
| Testar o bot após cada upload novo | Subir material sem verificar se o embed funcionou |
| Usar linguagem simples nos documentos | Termos muito técnicos sem glossário |

---

## 9. Modelo de IA Ativo

| Ambiente | Modelo | Provedor |
| :--- | :--- | :--- |
| Testes | `google/gemini-2.0-flash-lite:free` | OpenRouter |
| Produção | `google/gemini-2.0-flash-001` | OpenRouter (com crédito) |

Para trocar o modelo: AnythingLLM → Settings → LLM Provider → OpenAI Compatible
- Base URL: `https://openrouter.ai/api/v1`
- API Key: (ver variável `OPENROUTER_API_KEY` no Dokploy)
- Model: nome do modelo desejado
