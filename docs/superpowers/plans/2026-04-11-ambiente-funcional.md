# TDS Ambiente Funcional — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fechar os 5 gaps que bloqueiam o ambiente funcional completo: chaves de API vazias, URL errada no AnythingLLM, OTP sem workflow n8n, sem aluno piloto E2E, sem script de import CSV para os 2.160 beneficiários.

**Architecture:** Flow-first com 1 aluno piloto — configurar chaves → adicionar campo n8n_webhook_url → modificar otp_send() para rotear via n8n → criar workflow n8n → validar E2E completo → script de import CSV em lote. Cada task produz artefato verificável antes de avançar.

**Tech Stack:** Python 3.12 / FastAPI (`lms_lite_api.py`), n8n (workflow via API REST), Evolution API (WhatsApp Baileys), Docker / nginx, React dashboard (ops.ipexdesenvolvimento.cloud)

---

### Task 1: Configurar todas as chaves de integração via PUT /settings

**Files:**
- External: `PUT https://api-lms.ipexdesenvolvimento.cloud/settings` (persiste em `/app/settings.json` no container, sem rebuild)

- [ ] **Step 1: Aplicar os 10 campos conhecidos de uma só vez**

```bash
curl -s -X PUT https://api-lms.ipexdesenvolvimento.cloud/settings \
  -H "X-Admin-Key: admin-tds-2026" \
  -H "Content-Type: application/json" \
  -d '{
    "anythingllm_url": "https://rag.ipexdesenvolvimento.cloud",
    "anythingllm_key": "W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0",
    "anythingllm_workspace": "tds-lms-knowledge",
    "evolution_url": "https://evolution.ipexdesenvolvimento.cloud",
    "evolution_key": "tds_evolution_key_50f5aacc",
    "evolution_instance": "tds_suporte_audiovisual",
    "chatwoot_url": "https://chat.ipexdesenvolvimento.cloud",
    "chatwoot_token": "w8BYLTQc1s5VMowjQw433rGy",
    "openrouter_key": "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",
    "openrouter_model": "openai/gpt-4o-mini"
  }'
```

Expected: `{"status":"ok"}` ou objeto com todos os campos refletidos.

- [ ] **Step 2: Verificar chaves salvas**

```bash
curl -s https://api-lms.ipexdesenvolvimento.cloud/settings \
  -H "X-Admin-Key: admin-tds-2026" | python3 -c "
import sys, json
s = json.load(sys.stdin)
checks = ['anythingllm_key', 'evolution_key', 'chatwoot_token', 'openrouter_key']
for k in checks:
    print(k + ':', 'OK' if s.get(k) else 'VAZIO')
print('anythingllm_url:', s.get('anythingllm_url'))
"
```

Expected:
```
anythingllm_key: OK
evolution_key: OK
chatwoot_token: OK
openrouter_key: OK
anythingllm_url: https://rag.ipexdesenvolvimento.cloud
```

- [ ] **Step 3: Verificar AnythingLLM RAG responde com a chave correta**

```bash
curl -s -X POST https://api-lms.ipexdesenvolvimento.cloud/chat/query \
  -H "Content-Type: application/json" \
  -d '{"message": "O que é o programa TDS?", "workspace": "tds-lms-knowledge"}'
```

Expected: JSON com campo `response` não vazio (pode demorar ~5s na primeira chamada).

- [ ] **Step 4: Verificar Evolution API alcançável e instância conectada**

```bash
curl -s https://evolution.ipexdesenvolvimento.cloud/instance/fetchInstances \
  -H "apikey: tds_evolution_key_50f5aacc" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for i in data:
    print(i.get('name'), '->', i.get('connectionStatus'))
"
```

Expected: `tds_suporte_audiovisual -> open`

---

### Task 2: Adicionar campo `n8n_webhook_url` ao SETTINGS_DEFAULTS

**Files:**
- Modify: `/root/projeto-tds/lms_lite_api.py` — `SETTINGS_DEFAULTS` dict (linha 71–89)

- [ ] **Step 1: Adicionar o campo ao final do dict**

No arquivo `/root/projeto-tds/lms_lite_api.py`, substituir a linha `"chatwoot_website_token": "",` seguida de `}` por:

```python
    "chatwoot_website_token": "",
    "n8n_webhook_url": "",
}
```

O `SETTINGS_DEFAULTS` completo deve ficar (linhas 71–90):

```python
SETTINGS_DEFAULTS = {
    "anythingllm_url": "https://llm.ipexdesenvolvimento.cloud",
    "anythingllm_key": "",
    "anythingllm_workspace": "tds-lms-knowledge",
    "openrouter_key": "",
    "openrouter_model": "openai/gpt-4o-mini",
    "evolution_url": "https://evolution.ipexdesenvolvimento.cloud",
    "evolution_key": "",
    "evolution_instance": "tds_suporte_audiovisual",
    "chatwoot_url": "https://chat.ipexdesenvolvimento.cloud",
    "chatwoot_token": "",
    "chatwoot_inbox_id": "",
    "wa_cloud_token": "",
    "wa_phone_number_id": "",
    "wa_business_id": "",
    "supabase_url": "https://api-lms.ipexdesenvolvimento.cloud",
    "supabase_service_key": "",
    "chatwoot_website_token": "",
    "n8n_webhook_url": "",
}
```

- [ ] **Step 2: Verificar que não há erro de sintaxe**

```bash
python3 -c "import ast; ast.parse(open('/root/projeto-tds/lms_lite_api.py').read()); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd /root/projeto-tds
git add lms_lite_api.py
git commit -m "feat(api): add n8n_webhook_url to SETTINGS_DEFAULTS"
```

---

### Task 3: Modificar otp_send() para rotear via n8n (com fallback Evolution direto)

**Files:**
- Modify: `/root/projeto-tds/lms_lite_api.py` — função `otp_send` (linha ~320), bloco de despacho (linhas 334–345)

- [ ] **Step 1: Substituir o bloco de envio Evolution pelo novo bloco n8n-first**

Localizar e substituir o trecho:

```python
    if evo_key and evo_url:
        try:
            requests.post(
                f"{evo_url}/message/sendText/{evo_inst}",
                json={"number": phone, "text": f"🔐 Seu código TDS: *{code}*\n\nVálido por 5 minutos. Não compartilhe."},
                headers={"apikey": evo_key},
                timeout=10,
            )
        except Exception as e:
            print(f"[OTP] Falha ao enviar via Evolution: {e}")
    else:
        print(f"[OTP DEV] Código para {phone}: {code}")
```

Pelo novo trecho:

```python
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
                json={
                    "number": phone,
                    "text": f"🔐 Seu código TDS: *{code}*\n\nVálido por 5 minutos. Não compartilhe com ninguém.",
                },
                headers={"apikey": evo_key},
                timeout=10,
            )
        except Exception as e:
            print(f"[OTP] Falha ao enviar via Evolution: {e}")
    else:
        print(f"[OTP DEV] Código para {phone}: {code}")
```

- [ ] **Step 2: Verificar sintaxe**

```bash
python3 -c "import ast; ast.parse(open('/root/projeto-tds/lms_lite_api.py').read()); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit e rebuild do container**

```bash
cd /root/projeto-tds
git add lms_lite_api.py
git commit -m "feat(api): route OTP via n8n webhook when configured, fallback to Evolution direct"
```

Rebuild (aguarda ~2 min):

```bash
cd /etc/dokploy/compose/compose-parse-primary-array-kmj9v7/code/docker
docker compose build --no-cache lms-lite-api 2>&1 | tail -8
docker compose up -d --force-recreate lms-lite-api 2>&1
```

- [ ] **Step 4: Confirmar que a API voltou**

```bash
sleep 5 && curl -s https://api-lms.ipexdesenvolvimento.cloud/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 5: Confirmar que settings ainda têm as chaves (não resetaram)**

```bash
curl -s https://api-lms.ipexdesenvolvimento.cloud/settings \
  -H "X-Admin-Key: admin-tds-2026" | python3 -c \
  "import sys,json; s=json.load(sys.stdin); print('evolution_key:', 'OK' if s.get('evolution_key') else 'PERDEU')"
```

Expected: `evolution_key: OK`

Se o rebuild resetou o `settings.json`, reaplicar o curl do Task 1 Step 1.

---

### Task 4: Criar workflow n8n "TDS OTP Send"

**Files:**
- External: n8n workflow criado via API REST do n8n

- [ ] **Step 1: Descobrir credenciais do n8n**

```bash
docker exec kreativ-n8n env 2>/dev/null | grep -iE "N8N_BASIC_AUTH|N8N_USER|PASSWORD|API_KEY" | head -5
```

Anotar usuário e senha (normalmente `admin` / senha configurada no compose).

- [ ] **Step 2: Obter API key do n8n**

```bash
# Substituir USER e PASSWORD pelos valores encontrados no Step 1
curl -s -u USER:PASSWORD \
  https://n8n.ipexdesenvolvimento.cloud/api/v1/credentials \
  -H "Content-Type: application/json" | head -20
```

Se retornar `401`, o n8n usa JWT. Gerar um API key em `https://n8n.ipexdesenvolvimento.cloud/settings/api`.
Definir: `N8N_API_KEY=<key obtida>`

- [ ] **Step 3: Criar o workflow via API**

```bash
curl -s -X POST https://n8n.ipexdesenvolvimento.cloud/api/v1/workflows \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TDS OTP Send",
    "nodes": [
      {
        "id": "webhook-node",
        "name": "Webhook",
        "type": "n8n-nodes-base.webhook",
        "typeVersion": 2,
        "position": [250, 300],
        "parameters": {
          "httpMethod": "POST",
          "path": "otp-send",
          "responseMode": "lastNode",
          "options": {}
        },
        "webhookId": "otp-send"
      },
      {
        "id": "http-node",
        "name": "Send WhatsApp OTP",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [500, 300],
        "parameters": {
          "method": "POST",
          "url": "https://evolution.ipexdesenvolvimento.cloud/message/sendText/tds_suporte_audiovisual",
          "sendHeaders": true,
          "headerParameters": {
            "parameters": [
              {"name": "apikey", "value": "tds_evolution_key_50f5aacc"},
              {"name": "Content-Type", "value": "application/json"}
            ]
          },
          "sendBody": true,
          "specifyBody": "json",
          "jsonBody": "={\"number\": \"{{ $json.phone }}\", \"text\": \"🔐 Seu código TDS: *{{ $json.code }}*\\n\\nVálido por 5 minutos. Não compartilhe com ninguém.\"}"
        }
      },
      {
        "id": "respond-node",
        "name": "Respond",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "position": [750, 300],
        "parameters": {
          "respondWith": "json",
          "responseBody": "{\"sent\": true}"
        }
      }
    ],
    "connections": {
      "Webhook": {
        "main": [[{"node": "Send WhatsApp OTP", "type": "main", "index": 0}]]
      },
      "Send WhatsApp OTP": {
        "main": [[{"node": "Respond", "type": "main", "index": 0}]]
      }
    },
    "active": true,
    "settings": {}
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('Workflow ID:', d.get('id'), '| active:', d.get('active'))"
```

Expected: `Workflow ID: <uuid> | active: True`

- [ ] **Step 4: Testar o webhook diretamente (sem passar pelo lms_lite_api)**

```bash
curl -s -X POST https://n8n.ipexdesenvolvimento.cloud/webhook/otp-send \
  -H "Content-Type: application/json" \
  -d '{"phone": "556399374165", "code": "000001"}'
```

Expected: `{"sent": true}` e mensagem de teste chega no WhatsApp com código `000001`.

---

### Task 5: Configurar n8n_webhook_url nas settings e verificar OTP completo

**Files:**
- External: `PUT https://api-lms.ipexdesenvolvimento.cloud/settings`

- [ ] **Step 1: Salvar URL do webhook n8n nas settings**

```bash
curl -s -X PUT https://api-lms.ipexdesenvolvimento.cloud/settings \
  -H "X-Admin-Key: admin-tds-2026" \
  -H "Content-Type: application/json" \
  -d '{"n8n_webhook_url": "https://n8n.ipexdesenvolvimento.cloud/webhook/otp-send"}'
```

Expected: `{"status":"ok"}` ou todos os campos refletidos com `n8n_webhook_url` preenchido.

- [ ] **Step 2: Confirmar campo salvo**

```bash
curl -s https://api-lms.ipexdesenvolvimento.cloud/settings \
  -H "X-Admin-Key: admin-tds-2026" | python3 -c \
  "import sys,json; s=json.load(sys.stdin); print('n8n_webhook_url:', s.get('n8n_webhook_url','VAZIO'))"
```

Expected: `n8n_webhook_url: https://n8n.ipexdesenvolvimento.cloud/webhook/otp-send`

- [ ] **Step 3: Disparar OTP via lms_lite_api e confirmar mensagem WhatsApp**

```bash
curl -s -X POST https://api-lms.ipexdesenvolvimento.cloud/otp/send \
  -H "Content-Type: application/json" \
  -d '{"phone": "556399374165"}'
```

Expected: `{"sent": true}` e mensagem WhatsApp chega no número `+55 63 99374165` com código de 6 dígitos.

---

### Task 6: Criar aluno piloto e executar teste E2E completo

**Files:**
- External: endpoints da `lms_lite_api` em sequência

- [ ] **Step 1: Criar aluno piloto**

```bash
curl -s -X POST https://api-lms.ipexdesenvolvimento.cloud/student \
  -H "X-Admin-Key: admin-tds-2026" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "556399374165",
    "name": "Rafael Piloto",
    "course": "audiovisual-e-producao-de-conteudo-digital-2",
    "municipality": "Palmas"
  }'
```

Expected: JSON com `phone` e `name` do aluno criado (ou `409` se já existir — prosseguir normalmente).

- [ ] **Step 2: Disparar OTP**

```bash
curl -s -X POST https://api-lms.ipexdesenvolvimento.cloud/otp/send \
  -H "Content-Type: application/json" \
  -d '{"phone": "556399374165"}'
```

Expected: `{"sent": true}` e código chega no WhatsApp físico.

- [ ] **Step 3: Verificar OTP e obter token de sessão**

Substituir `XXXXXX` pelo código recebido no WhatsApp:

```bash
curl -s -X POST https://api-lms.ipexdesenvolvimento.cloud/otp/verify \
  -H "Content-Type: application/json" \
  -d '{"phone": "556399374165", "code": "XXXXXX"}'
```

Expected: `{"token": "<32-chars>", "student": {"name": "Rafael Piloto", "phone": "556399374165", ...}}`

Salvar o token: `TOKEN=<valor retornado>`

- [ ] **Step 4: Verificar sessão ativa**

```bash
curl -s https://api-lms.ipexdesenvolvimento.cloud/session/me \
  -H "Authorization: Bearer $TOKEN"
```

Expected: JSON com `phone`, `name`, `course` do aluno.

- [ ] **Step 5: Listar cursos e identificar o ID do curso do piloto**

```bash
curl -s https://api-lms.ipexdesenvolvimento.cloud/courses | python3 -c "
import sys, json
cs = json.load(sys.stdin)
for c in cs:
    print(c.get('id'), '-', c.get('title','?'))
"
```

Anotar o `id` do curso `audiovisual-e-producao-de-conteudo-digital-2` (ex: `audiovisual`).

- [ ] **Step 6: Registrar progresso em uma lição**

Substituir `COURSE_ID` pelo id encontrado no Step 5:

```bash
curl -s -X POST https://api-lms.ipexdesenvolvimento.cloud/update_progress \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"phone": "556399374165", "course_id": "COURSE_ID", "lesson_id": "lesson_1", "score": 100}'
```

Expected: `{"status": "ok"}` ou `{"updated": true}`.

- [ ] **Step 7: Emitir certificado**

```bash
curl -s -X POST https://api-lms.ipexdesenvolvimento.cloud/issue_cert \
  -H "X-Admin-Key: admin-tds-2026" \
  -H "Content-Type: application/json" \
  -d '{"phone": "556399374165", "course_id": "COURSE_ID"}'
```

Expected: `{"cert_hash": "<sha256>", "url": "/validate/<hash>"}` ou similar.

- [ ] **Step 8: Validar certificado publicamente**

```bash
# Substituir HASH pelo cert_hash retornado no Step 7
curl -s https://api-lms.ipexdesenvolvimento.cloud/validate_cert/HASH | python3 -m json.tool
```

Expected: JSON com `valid: true`, `student_name: "Rafael Piloto"`, `course`, `issued_at`.

Verificar também em: `https://ops.ipexdesenvolvimento.cloud/validate/HASH`

---

### Task 7: Criar script import_students_csv.py

**Files:**
- Create: `/root/projeto-tds/import_students_csv.py`

- [ ] **Step 1: Criar o script**

```python
#!/usr/bin/env python3
"""
Importa alunos TDS de planilha CSV para a lms_lite_api.

Formato CSV esperado (com cabeçalho):
  telefone,nome,municipio,curso_slug,nis

Uso:
  python3 import_students_csv.py alunos_sisec.csv
  python3 import_students_csv.py alunos_sisec.csv --dry-run
  python3 import_students_csv.py alunos_sisec.csv --api-url https://api-lms.ipexdesenvolvimento.cloud
"""
import csv
import sys
import time
import argparse
import requests
from pathlib import Path

API_URL = "https://api-lms.ipexdesenvolvimento.cloud"
ADMIN_KEY = "admin-tds-2026"
THROTTLE_SECONDS = 0.1  # 10 req/s


def import_students(csv_path: str, api_url: str, dry_run: bool) -> int:
    path = Path(csv_path)
    if not path.exists():
        print(f"[ERR] Arquivo não encontrado: {csv_path}")
        return 1

    errors = []
    ok = skip = err = 0

    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    prefix = "[DRY-RUN] " if dry_run else ""
    print(f"{prefix}Importando {len(rows)} alunos de {csv_path}...")

    for i, row in enumerate(rows, 1):
        phone = row.get("telefone", "").strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        name = row.get("nome", "").strip()
        municipality = row.get("municipio", "").strip()
        course = row.get("curso_slug", "").strip()
        nis = row.get("nis", "").strip()

        if not phone or not name:
            print(f"[SKIP] Linha {i}: telefone ou nome vazio — {row}")
            skip += 1
            continue

        if not phone.startswith("55"):
            phone = "55" + phone

        if dry_run:
            print(f"[DRY]  {i}/{len(rows)} {name} ({phone}) → {course or 'sem curso'}")
            ok += 1
            continue

        try:
            resp = requests.post(
                f"{api_url}/student",
                json={"phone": phone, "name": name, "municipality": municipality,
                      "course": course, "nis": nis},
                headers={"X-Admin-Key": ADMIN_KEY},
                timeout=15,
            )
            if resp.status_code in (200, 201):
                print(f"[OK]   {i}/{len(rows)} {name} ({phone})")
                ok += 1
            elif resp.status_code == 409:
                print(f"[SKIP] {i}/{len(rows)} {name} ({phone}) — já existe")
                skip += 1
            else:
                msg = resp.text[:120]
                print(f"[ERR]  {i}/{len(rows)} {name} ({phone}) — HTTP {resp.status_code}: {msg}")
                errors.append({**row, "_http_status": resp.status_code, "_error": msg})
                err += 1
        except Exception as e:
            print(f"[ERR]  {i}/{len(rows)} {name} ({phone}) — {e}")
            errors.append({**row, "_http_status": "exception", "_error": str(e)})
            err += 1

        time.sleep(THROTTLE_SECONDS)

    print(f"\n{'='*52}")
    print(f"Resultado: {ok} OK  |  {skip} SKIP  |  {err} ERRO  de {len(rows)} total")

    if errors:
        err_path = path.stem + "_errors.csv"
        fieldnames = list(errors[0].keys())
        with open(err_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(errors)
        print(f"Falhas salvas em: {err_path} — reprocesse com: python3 {sys.argv[0]} {err_path}")

    success_rate = ok / max(len(rows), 1)
    return 0 if success_rate >= 0.95 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importa alunos TDS de CSV para lms_lite_api")
    parser.add_argument("csv_file", help="Caminho para o arquivo CSV")
    parser.add_argument("--api-url", default=API_URL, help="URL base da API (padrão: produção)")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem enviar requisições")
    args = parser.parse_args()
    sys.exit(import_students(args.csv_file, args.api_url, args.dry_run))
```

Salvar em `/root/projeto-tds/import_students_csv.py`.

- [ ] **Step 2: Criar CSV de teste com 3 linhas**

Criar `/root/projeto-tds/test_import.csv`:

```
telefone,nome,municipio,curso_slug,nis
5563991111111,Maria Silva Teste,Palmas,agricultura-sustentavel,111111111111
5511988882222,João Souza Teste,Araguaína,audiovisual-e-producao-de-conteudo-digital-2,222222222222
5562977773333,Ana Lima Teste,Porto Nacional,associativismo-e-cooperativismo-4,333333333333
```

- [ ] **Step 3: Executar dry-run**

```bash
python3 /root/projeto-tds/import_students_csv.py /root/projeto-tds/test_import.csv --dry-run
```

Expected:
```
[DRY-RUN] Importando 3 alunos de test_import.csv...
[DRY]  1/3 Maria Silva Teste (5563991111111) → agricultura-sustentavel
[DRY]  2/3 João Souza Teste (5511988882222) → audiovisual-e-producao-de-conteudo-digital-2
[DRY]  3/3 Ana Lima Teste (5562977773333) → associativismo-e-cooperativismo-4
====================================================
Resultado: 3 OK  |  0 SKIP  |  0 ERRO  de 3 total
```

- [ ] **Step 4: Executar import real**

```bash
python3 /root/projeto-tds/import_students_csv.py /root/projeto-tds/test_import.csv
```

Expected: `3 OK  |  0 SKIP  |  0 ERRO`

- [ ] **Step 5: Confirmar alunos na API**

```bash
curl -s https://api-lms.ipexdesenvolvimento.cloud/students \
  -H "X-Admin-Key: admin-tds-2026" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Total: {len(d)} alunos')
for s in d[-4:]:
    print(' -', s.get('name','?'), '|', s.get('phone','?'))
"
```

Expected: lista com 4+ alunos incluindo os 3 de teste.

- [ ] **Step 6: Commit**

```bash
cd /root/projeto-tds
git add import_students_csv.py
git commit -m "feat: add import_students_csv.py — bulk SISEC import with throttle + error log"
```

---

## Self-Review

**Spec coverage:**
- Componente 1 (10 keys + URL fix) → Task 1 ✓
- Componente 2 (n8n OTP workflow) → Task 4 ✓
- Componente 3 (otp_send modification + n8n_webhook_url field) → Tasks 2 + 3 ✓
- Componente 4 (piloto E2E 8 etapas) → Tasks 5 + 6 ✓
- Componente 5 (CSV import script) → Task 7 ✓

**Placeholder scan:** Nenhum TBD/TODO. Todos os steps têm código ou comando completo com expected output.

**Type consistency:**
- `n8n_webhook_url` adicionado em Task 2 → lido com `settings.get("n8n_webhook_url", "")` em Task 3 ✓
- Rebuild do container em Task 3 antes de configurar a URL em Task 5 ✓
- CSV columns `telefone,nome,municipio,curso_slug,nis` → payload `POST /student` com os mesmos campos ✓
- Token obtido em Task 6 Step 3 → usado em Steps 4, 6 do mesmo Task ✓

**Ordem de dependências:** Task 1 → Task 2 → Task 3 (rebuild) → Task 4 → Task 5 → Task 6 → Task 7. Sem inversões. ✓
