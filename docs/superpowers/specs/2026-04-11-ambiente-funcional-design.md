# TDS — Ambiente Funcional (Plataforma Completa) — Design Spec
**Data:** 2026-04-11
**Status:** Aprovado

---

## Contexto

O ambiente TDS tem todos os serviços rodando (n8n, rag, chat, ops, api-lms), 7 cursos carregados e a instância WhatsApp `tds_suporte_audiovisual` conectada (`open`). O bloqueio atual é que todas as chaves de integração no `settings.json` da `lms_lite_api` estão vazias, e o fluxo OTP não tem o workflow n8n correspondente.

**Critério de sucesso:** aluno envia número no portal → recebe OTP no WhatsApp → loga → consome curso → recebe certificado. Admin vê dados reais em todos os tabs do dashboard.

**Abordagem:** flow-first com 1 aluno piloto. Fluxo E2E funcionando com 1 pessoa antes de importar os 2.160 do CadÚnico.

---

## Arquitetura do Fluxo Completo

```
ALUNO (WhatsApp físico)
    │
    │  1. acessa ops.ipexdesenvolvimento.cloud → aba Portal
    │  2. informa número WhatsApp
    ▼
Portal React (StudentPortal)
    │  POST /otp/send { phone }
    ▼
lms_lite_api (api-lms.ipexdesenvolvimento.cloud)
    │  gera código 6 dígitos, salva _otp_store (TTL 5min)
    │  POST n8n_webhook_url { phone, code }
    ▼
n8n Workflow "TDS OTP Send"
    │  POST Evolution /message/sendText/tds_suporte_audiovisual
    ▼
Evolution API → WhatsApp → ALUNO recebe código
    │
    │  3. aluno digita código no portal
    ▼
Portal → POST /otp/verify { phone, code }
    ▼
lms_lite_api → valida → gera token (secrets.token_urlsafe)
    │  retorna { token, student }
    ▼
Portal carrega: cursos, progresso, certificados
    │  GET /student/{phone}  (Authorization: Bearer {token})
    │  POST /update_progress
    │  POST /issue_cert
    ▼
ADMIN (ops dashboard)
    │  tabs: Grupos, Transmissão, IA Insight, Tutores, Métricas
    │  RAG chat: POST /chat/query → AnythingLLM workspace
    └──────────────────────────────────────────────────────────
```

---

## Componente 1 — Configuração de Chaves (`PUT /settings`)

Aplicação via API sem rebuild. Persiste em `/app/settings.json` dentro do container.

| Campo | Valor |
|---|---|
| `anythingllm_url` | `https://rag.ipexdesenvolvimento.cloud` |
| `anythingllm_key` | `W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0` |
| `anythingllm_workspace` | `tds-lms-knowledge` |
| `evolution_url` | `https://evolution.ipexdesenvolvimento.cloud` |
| `evolution_key` | `tds_evolution_key_50f5aacc` |
| `evolution_instance` | `tds_suporte_audiovisual` |
| `chatwoot_url` | `https://chat.ipexdesenvolvimento.cloud` |
| `chatwoot_token` | `w8BYLTQc1s5VMowjQw433rGy` |
| `openrouter_key` | `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` |
| `openrouter_model` | `openai/gpt-4o-mini` |
| `n8n_webhook_url` | `https://n8n.ipexdesenvolvimento.cloud/webhook/otp-send` (a criar) |

**Nota:** `n8n_webhook_url` é campo novo — precisa ser adicionado a `SETTINGS_DEFAULTS` em `lms_lite_api.py`.

---

## Componente 2 — n8n Workflow "TDS OTP Send"

Workflow simples, 3 nós:

```
[Webhook]  POST /webhook/otp-send  (método: POST, path: otp-send)
  body recebido: { "phone": "556399...", "code": "123456" }
        │
        ▼
[HTTP Request]
  Method: POST
  URL: https://evolution.ipexdesenvolvimento.cloud/message/sendText/tds_suporte_audiovisual
  Headers: { "apikey": "tds_evolution_key_50f5aacc", "Content-Type": "application/json" }
  Body (JSON):
    {
      "number": "={{ $json.phone }}",
      "text": "🔐 Seu código TDS: *{{ $json.code }}*\n\nVálido por 5 minutos. Não compartilhe com ninguém."
    }
        │
        ▼
[Respond to Webhook]
  Status: 200
  Body: { "sent": true }
```

Webhook URL resultante: `https://n8n.ipexdesenvolvimento.cloud/webhook/otp-send`

---

## Componente 3 — Modificação `otp_send()` em `lms_lite_api.py`

Mudança mínima: quando `n8n_webhook_url` estiver configurado, chama n8n em vez de Evolution diretamente. Retro-compatível — fallback para Evolution direto se `n8n_webhook_url` vazio.

```python
# Trecho a substituir no otp_send():
n8n_url = settings.get("n8n_webhook_url", "")
if n8n_url:
    try:
        requests.post(n8n_url, json={"phone": phone, "code": code}, timeout=10)
    except Exception as e:
        print(f"[OTP] Falha ao chamar n8n: {e}")
elif evo_key and evo_url:
    try:
        requests.post(
            f"{evo_url}/message/sendText/{evo_inst}",
            json={"number": phone, "text": f"🔐 Seu código TDS: *{code}*\n\nVálido por 5 minutos."},
            headers={"apikey": evo_key},
            timeout=10,
        )
    except Exception as e:
        print(f"[OTP] Falha ao enviar via Evolution: {e}")
```

Rebuild do container necessário após esta mudança.

---

## Componente 4 — Estudante Piloto (Teste E2E)

Sequência de validação em ordem — cada passo verificado antes do próximo:

```
1. POST /student
   { "phone": "556399374165", "name": "Rafael Piloto",
     "course": "audiovisual-e-producao-de-conteudo-digital-2",
     "municipality": "Palmas" }
   → 200 OK

2. POST /otp/send { "phone": "556399374165" }
   → WhatsApp recebe mensagem com código

3. POST /otp/verify { "phone": "556399374165", "code": "XXXXXX" }
   → { token: "...", student: { ... } }

4. GET /session/me  Authorization: Bearer {token}
   → dados do aluno

5. GET /courses
   → 7 cursos listados

6. POST /update_progress
   { phone, course_id, lesson_id: "L1", score: 100 }
   → progresso salvo

7. POST /issue_cert { phone, course_id }
   → { cert_hash: "...", url: "/validate/..." }

8. GET /validate_cert/{hash}
   → certificado válido
```

---

## Componente 5 — Script CSV Import (`import_students_csv.py`)

Executado **após** piloto E2E aprovado. Roda localmente contra a API em produção.

**Formato CSV (SISEC/MDS):**
```csv
telefone,nome,municipio,curso_slug,nis
5563991234567,Maria Silva,Palmas,agricultura-sustentavel,123456789012
5511988887777,João Souza,Araguaína,audiovisual-e-producao-de-conteudo-digital-2,987654321098
```

**Comportamento do script:**
- Lê CSV via `sys.argv[1]`
- Para cada linha: `POST /student` com `X-Admin-Key: admin-tds-2026`
- Trata duplicatas (409) como skip silencioso
- Imprime progresso: `[OK] Maria Silva | [SKIP] João Souza (já existe) | [ERR] ...`
- Gera `import_errors.csv` com linhas que falharam para reprocessamento
- Retorna exit code 0 se ≥ 95% de sucesso, 1 caso contrário

**Capacidade:** 2.160 registros em ~3min com 1 req/100ms de throttle.

---

## Dependências e Ordem de Execução

```
[1] Configurar chaves (PUT /settings)
        │
        ▼
[2] Criar workflow n8n OTP
        │
        ▼
[3] Modificar otp_send() + rebuild container
        │
        ▼
[4] Testar piloto E2E (1 aluno real)
        │  ← gate: só avança se 100% das 8 etapas OK
        ▼
[5] Executar import_students_csv.py com planilha SISEC
```

---

## O que NÃO está no escopo desta fase

- Autenticação Supabase (JWT do lms_lite_api é suficiente para beta)
- TTS e imagens para cursos 3-7 (conteúdo independente da plataforma)
- Frappe LMS (excluído conforme decisão de escopo beta)
- Chatwoot widget embed no portal (pode ser adicionado pós-piloto)
- Gemma 4 / autenticação Ollama Cloud
