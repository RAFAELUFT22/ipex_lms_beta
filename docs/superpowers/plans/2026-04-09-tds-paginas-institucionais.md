# TDS — Páginas Institucionais, Guias e Limpeza do LMS — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar landing page institucional, 4 páginas de suporte, 3 guias de uso com chatbot Chatwoot integrado, e limpar o catálogo de cursos do Frappe LMS em produção.

**Architecture:** Frappe Web Pages (CMS nativo) para todas as páginas públicas, criadas via REST API. Chatbot embutido via Chatwoot SDK script. Limpeza do LMS via MariaDB direto no container. Fix N8N via API do N8N.

**Tech Stack:** Frappe LMS v2.45.2 · Chatwoot v4.11.0 · N8N v2.13.4 · AnythingLLM · Docker · MariaDB · curl

**Auth Frappe:** `Authorization: token 056681de29fce7a:7c78dcba6e3c5d1`  
**URL base:** `https://lms.ipexdesenvolvimento.cloud`  
**Chatwoot widget token:** `HwBawyqmiKTAbNzF8yAnzHCD`  
**Chatwoot base URL:** `https://chat.ipexdesenvolvimento.cloud`

---

## Task 1: Limpeza do catálogo — despublicar duplicatas e demo

**Files:** nenhum arquivo — operações diretas no MariaDB do container `kreativ-mariadb`

- [ ] **Step 1: Despublicar curso demo**

```bash
docker exec kreativ-backend bench --site lms.ipexdesenvolvimento.cloud mariadb --execute \
  "UPDATE \`tabLMS Course\` SET published=0 WHERE name='a-guide-to-frappe-learning';"
```

Verificar: `docker exec kreativ-backend bench --site lms.ipexdesenvolvimento.cloud mariadb --execute "SELECT name, published FROM \`tabLMS Course\` WHERE name='a-guide-to-frappe-learning';"`
Esperado: `published = 0`

- [ ] **Step 2: Despublicar versões antigas dos 7 cursos TDS (manter apenas os com conteúdo)**

```bash
docker exec kreativ-backend bench --site lms.ipexdesenvolvimento.cloud mariadb --execute "
UPDATE \`tabLMS Course\` SET published=0 WHERE name IN (
  'agricultura-sustent-vel-sistemas-agroflorestais',
  'audiovisual-e-produ-o-de-conte-do-digital',
  'finan-as-e-empreendedorismo',
  'ia-no-meu-bolso-intelig-ncia-artificial-para-o-dia-a-dia',
  'sim-servi-o-de-inspe-o-municipal-para-pequenos-produtores',
  'associativismo-e-cooperativismo-3',
  'associativismo-e-cooperativismo-2',
  'associativismo-e-cooperativismo'
);"
```

- [ ] **Step 3: Verificar catálogo — contar cursos publicados restantes**

```bash
docker exec kreativ-backend bench --site lms.ipexdesenvolvimento.cloud mariadb --execute \
  "SELECT COUNT(*) as publicados FROM \`tabLMS Course\` WHERE published=1;"
```

Esperado: número menor que 106 (era 106 antes da limpeza). Os 7 cursos keeper + 5 Trilhas + sub-cursos de eixo devem permanecer.

- [ ] **Step 4: Verificar os 7 cursos keeper estão publicados**

```bash
docker exec kreativ-backend bench --site lms.ipexdesenvolvimento.cloud mariadb --execute "
SELECT name, title, published,
  (SELECT COUNT(*) FROM \`tabCourse Chapter\` ch WHERE ch.course=c.name) as caps
FROM \`tabLMS Course\` c
WHERE name IN (
  'agricultura-sustent-vel-sistemas-agroflorestais-2',
  'audiovisual-e-produ-o-de-conte-do-digital-2',
  'finan-as-e-empreendedorismo-2',
  'ia-no-meu-bolso-intelig-ncia-artificial-para-o-dia-a-dia-2',
  'sim-servi-o-de-inspe-o-municipal-para-pequenos-produtores-2',
  'associativismo-e-cooperativismo-4',
  'educa-o-financeira-para-a-melhor-idade'
);"
```

Esperado: todos com `published=1` e `caps > 0`.

- [ ] **Step 5: Commit de estado**

```bash
cd /root/projeto-tds && git add -A && git commit -m "chore: despublicar cursos duplicados e demo do LMS

- Demo 'a-guide-to-frappe-learning' despublicado
- Versões antigas dos 7 cursos TDS despublicadas
- Mantidos apenas os cursos com conteúdo (sufixo -2 e -4)"
```

---

## Task 2: Vincular turmas (batches) aos cursos

**Files:** nenhum — operações via Frappe bench

- [ ] **Step 1: Verificar estrutura do doctype LMS Batch para campo de cursos**

```bash
docker exec kreativ-backend bench --site lms.ipexdesenvolvimento.cloud mariadb --execute \
  "SHOW TABLES LIKE 'tabLMS Batch%';"
```

Anotar quais child tables existem para LMS Batch.

- [ ] **Step 2: Verificar se há child table de cursos no Batch**

```bash
docker exec kreativ-backend bench --site lms.ipexdesenvolvimento.cloud mariadb --execute \
  "SELECT t.name FROM \`tabDocType\` t WHERE t.module='LMS' AND t.name LIKE '%Batch%';"
```

- [ ] **Step 3: Inspecionar campos do LMS Batch via API**

```bash
curl -s "https://lms.ipexdesenvolvimento.cloud/api/resource/LMS%20Batch/turma-tds-agricultura-sustent-vel-2026" \
  -H "Authorization: token 056681de29fce7a:7c78dcba6e3c5d1" \
  2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(list(d.get('data',d).keys()))"
```

- [ ] **Step 4: Vincular cada batch ao curso correspondente via API (ajustar campo conforme Step 3)**

Se o batch tiver campo `courses` (child table):
```bash
# Agricultura
curl -s -X PUT "https://lms.ipexdesenvolvimento.cloud/api/resource/LMS%20Batch/turma-tds-agricultura-sustent-vel-2026" \
  -H "Authorization: token 056681de29fce7a:7c78dcba6e3c5d1" \
  -H "Content-Type: application/json" \
  -d '{"courses": [{"course": "agricultura-sustent-vel-sistemas-agroflorestais-2"}]}'

# Associativismo
curl -s -X PUT "https://lms.ipexdesenvolvimento.cloud/api/resource/LMS%20Batch/turma-tds-associativismo-e-cooperativismo-2026" \
  -H "Authorization: token 056681de29fce7a:7c78dcba6e3c5d1" \
  -H "Content-Type: application/json" \
  -d '{"courses": [{"course": "associativismo-e-cooperativismo-4"}]}'

# Audiovisual
curl -s -X PUT "https://lms.ipexdesenvolvimento.cloud/api/resource/LMS%20Batch/turma-tds-audiovisual-e-conte-do-digital-2026" \
  -H "Authorization: token 056681de29fce7a:7c78dcba6e3c5d1" \
  -H "Content-Type: application/json" \
  -d '{"courses": [{"course": "audiovisual-e-produ-o-de-conte-do-digital-2"}]}'

# Finanças
curl -s -X PUT "https://lms.ipexdesenvolvimento.cloud/api/resource/LMS%20Batch/turma-tds-finan-as-e-empreendedorismo-2026" \
  -H "Authorization: token 056681de29fce7a:7c78dcba6e3c5d1" \
  -H "Content-Type: application/json" \
  -d '{"courses": [{"course": "finan-as-e-empreendedorismo-2"}, {"course": "educa-o-financeira-para-a-melhor-idade"}]}'

# IA
curl -s -X PUT "https://lms.ipexdesenvolvimento.cloud/api/resource/LMS%20Batch/turma-tds-ia-no-meu-bolso-2026" \
  -H "Authorization: token 056681de29fce7a:7c78dcba6e3c5d1" \
  -H "Content-Type: application/json" \
  -d '{"courses": [{"course": "ia-no-meu-bolso-intelig-ncia-artificial-para-o-dia-a-dia-2"}]}'

# SIM
curl -s -X PUT "https://lms.ipexdesenvolvimento.cloud/api/resource/LMS%20Batch/turma-tds-sim-e-inspe-o-alimentar-2026" \
  -H "Authorization: token 056681de29fce7a:7c78dcba6e3c5d1" \
  -H "Content-Type: application/json" \
  -d '{"courses": [{"course": "sim-servi-o-de-inspe-o-municipal-para-pequenos-produtores-2"}]}'
```

- [ ] **Step 5: Verificar vínculos**

```bash
curl -s "https://lms.ipexdesenvolvimento.cloud/api/resource/LMS%20Batch/turma-tds-agricultura-sustent-vel-2026" \
  -H "Authorization: token 056681de29fce7a:7c78dcba6e3c5d1" \
  2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin).get('data', {})
print('courses:', d.get('courses', 'campo não encontrado'))
"
```

---

## Task 3: Fix `<think>` strip no workflow N8N

**Files:** nenhum — modificação via N8N API  
**Workflow ID:** `XYcnRlPZSlfGXOWb`  
**N8N API Key:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9` (JWT — usar a chave completa do .env.real)

- [ ] **Step 1: Obter workflow atual via API**

```bash
N8N_KEY=$(cat /root/kreativ-setup/.env.real 2>/dev/null | grep N8N_API_KEY | cut -d= -f2-)
curl -s "https://n8n.ipexdesenvolvimento.cloud/api/v1/workflows/XYcnRlPZSlfGXOWb" \
  -H "X-N8N-API-KEY: $N8N_KEY" \
  2>/dev/null | python3 -m json.tool > /tmp/workflow_current.json && echo "Salvo em /tmp/workflow_current.json"
```

- [ ] **Step 2: Verificar nodes do workflow — listar nomes**

```bash
python3 -c "
import json
with open('/tmp/workflow_current.json') as f:
    w = json.load(f)
nodes = w.get('nodes', [])
for n in nodes:
    print(f'  {n[\"id\"]} | {n[\"name\"]} | {n[\"type\"]}')
"
```

- [ ] **Step 3: Identificar o node de resposta ao Chatwoot e o node Fallback**

Anotar os IDs dos nodes:
- "Responder no Chatwoot" (recebe a resposta boa do RAG)
- "Responder Fallback" (recebe a resposta do RAG fallback)

- [ ] **Step 4: Adicionar Code nodes de strip antes dos nodes de resposta**

```bash
python3 << 'PYEOF'
import json, copy

with open('/tmp/workflow_current.json') as f:
    w = json.load(f)

nodes = w['nodes']
connections = w['connections']

# Código de strip para os Code nodes
strip_code = """
const raw = $input.first().json.textResponse || '';
const clean = raw.replace(/<think>[\\s\\S]*?<\\/think>/gi, '').trim();
return [{ json: { ...($input.first().json), textResponse: clean } }];
"""

# Encontrar nodes de resposta
resposta_nodes = [n for n in nodes if 'Responder' in n['name']]
for rn in resposta_nodes:
    print(f"Node de resposta: {rn['name']} | id: {rn['id']}")

# Listar conexões que chegam a cada node de resposta
for rn in resposta_nodes:
    for src_name, src_conns in connections.items():
        for conn_list in src_conns.get('main', []):
            for conn in conn_list:
                if conn.get('node') == rn['name']:
                    print(f"  ← vem de: {src_name}")

print("\nWorkflow carregado. Use Step 5 para criar os Code nodes via UI do N8N.")
PYEOF
```

- [ ] **Step 5: Adicionar strip via Code node na UI do N8N (mais seguro que API para workflow complexo)**

Acesse `https://n8n.ipexdesenvolvimento.cloud`, abra o workflow "Kreativ TDS — Chatwoot RAG Flow" e:

1. Antes do node **"Responder no Chatwoot"**: inserir um node **Code** com o código:
```javascript
const raw = $input.first().json.textResponse || '';
const clean = raw.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
return [{ json: { ...($input.first().json), textResponse: clean } }];
```

2. Antes do node **"Responder Fallback"**: inserir o mesmo Code node.

3. Salvar e **Activate** o workflow.

- [ ] **Step 6: Testar strip via API**

```bash
curl -s --max-time 30 -X POST "https://rag.ipexdesenvolvimento.cloud/api/v1/workspace/tds/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
  -d '{"message": "O que é o TDS?", "mode": "chat"}' \
  2>/dev/null | python3 -c "
import sys, json, re
d = json.load(sys.stdin)
resp = d.get('textResponse','')
has_think = bool(re.search(r'<think>', resp))
print('Tem <think>:', has_think)
print('Resposta (primeiros 200 chars):', resp[:200])
"
```

Esperado: `Tem <think>: False`

---

## Task 4: Aplicar healthchecks corrigidos (recreate containers)

**Files:** já corrigido em `/etc/dokploy/compose/compose-parse-primary-array-kmj9v7/code/docker-compose.yml`

- [ ] **Step 1: Confirmar que as correções estão no arquivo**

```bash
grep -A 3 "wget.*spider" /etc/dokploy/compose/compose-parse-primary-array-kmj9v7/code/docker-compose.yml
```

Esperado: 2 ocorrências de `wget -q --spider` (uma para N8N, uma para Chatwoot).

- [ ] **Step 2: Recriar apenas os containers com healthcheck incorreto**

```bash
cd /etc/dokploy/compose/compose-parse-primary-array-kmj9v7/code && \
  docker compose up -d --no-deps --force-recreate chatwoot-app n8n
```

Aguardar 30 segundos para os containers iniciarem.

- [ ] **Step 3: Verificar status de saúde após recreate**

```bash
sleep 40 && docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E "chatwoot|n8n"
```

Esperado: `kreativ-chatwoot` e `kreativ-n8n` com `(healthy)` após ~2 minutos.

---

## Task 5: Criar Landing Page (/) no Frappe LMS

**Files:** nenhum — via Frappe REST API

- [ ] **Step 1: Verificar se já existe Web Page com route vazia ou "home"**

```bash
curl -s "https://lms.ipexdesenvolvimento.cloud/api/resource/Web%20Page?filters=[[%22route%22,%22=%22,%22home-tds%22]]&fields=[%22name%22,%22route%22,%22published%22]" \
  -H "Authorization: token 056681de29fce7a:7c78dcba6e3c5d1" \
  2>/dev/null | python3 -m json.tool | head -20
```

- [ ] **Step 2: Criar (ou atualizar) a Web Page da landing**

```bash
curl -s -X POST "https://lms.ipexdesenvolvimento.cloud/api/resource/Web%20Page" \
  -H "Authorization: token 056681de29fce7a:7c78dcba6e3c5d1" \
  -H "Content-Type: application/json" \
  -d @- << 'ENDJSON'
{
  "doctype": "Web Page",
  "title": "TDS — Inclusão Produtiva no Tocantins",
  "route": "tds-home",
  "published": 1,
  "content_type": "HTML",
  "meta_title": "TDS — Território de Desenvolvimento Social e Inclusão Produtiva",
  "meta_description": "Capacitação profissional gratuita para beneficiários do CadÚnico em 36 municípios do Tocantins. Presencial, online e mista — com instrutores qualificados da UFT.",
  "main_section_html": "PLACEHOLDER_LANDING"
}
ENDJSON
```

Nota: substituir `PLACEHOLDER_LANDING` pelo HTML completo gerado no Step 3.

- [ ] **Step 3: Construir HTML da landing page e criar via script Python**

Criar arquivo `/tmp/create_pages.py`:

```python
#!/usr/bin/env python3
import subprocess, json, re

FRAPPE_URL = "https://lms.ipexdesenvolvimento.cloud"
AUTH = "token 056681de29fce7a:7c78dcba6e3c5d1"
CHATWOOT_URL = "https://chat.ipexdesenvolvimento.cloud"
WIDGET_TOKEN = "HwBawyqmiKTAbNzF8yAnzHCD"

WIDGET_SCRIPT = f"""
<script>
(function(d,t){{
  var BASE_URL="{CHATWOOT_URL}";
  var g=d.createElement(t),s=d.getElementsByTagName(t)[0];
  g.src=BASE_URL+"/packs/js/sdk.js";
  g.defer=true; g.async=true;
  s.parentNode.insertBefore(g,s);
  g.onload=function(){{
    window.chatwootSDK.run({{
      websiteToken: '{WIDGET_TOKEN}',
      baseUrl: BASE_URL
    }})
  }}
}})(document,"script");
</script>
"""

def create_page(route, title, meta_desc, html_content):
    data = {{
        "doctype": "Web Page",
        "title": title,
        "route": route,
        "published": 1,
        "content_type": "HTML",
        "meta_title": title,
        "meta_description": meta_desc,
        "main_section_html": html_content + WIDGET_SCRIPT
    }}
    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        f"{{FRAPPE_URL}}/api/resource/Web%20Page",
        "-H", f"Authorization: {{AUTH}}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(data)
    ], capture_output=True, text=True)
    resp = json.loads(result.stdout)
    if "data" in resp:
        print(f"✅ Criado: /{{route}} ({{}}{{'title'}})")
    else:
        print(f"❌ Erro em /{{route}}: {{resp}}")
    return resp

# --- LANDING PAGE HTML ---
LANDING_HTML = """<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:'Segoe UI',system-ui,sans-serif;}}
.tds-nav{{background:#1a237e;color:white;padding:0.7rem 2rem;display:flex;align-items:center;justify-content:space-between;}}
.tds-brand{{font-weight:800;font-size:1.1rem;}}
.tds-brand .badge{{background:#ff6f00;font-size:0.6rem;font-weight:800;padding:0.1rem 0.4rem;border-radius:3px;margin-left:0.3rem;}}
.tds-nav-links{{display:flex;gap:1.5rem;font-size:0.85rem;}}
.tds-nav-links a{{color:rgba(255,255,255,0.85);text-decoration:none;}}
.tds-nav .cta{{background:#ff6f00;color:white;padding:0.4rem 1rem;border-radius:4px;font-size:0.82rem;font-weight:700;text-decoration:none;}}
.hero{{background:linear-gradient(135deg,#1a237e,#283593 60%,#1565c0);color:white;padding:3.5rem 2rem 3rem;display:grid;grid-template-columns:1.1fr 0.9fr;gap:2rem;align-items:center;}}
.hero h1{{font-size:1.9rem;font-weight:800;line-height:1.25;margin-bottom:0.8rem;}}
.hero h1 em{{color:#ffd54f;font-style:normal;}}
.hero p{{font-size:0.92rem;opacity:0.9;line-height:1.65;margin-bottom:1.4rem;}}
.hero-ctas{{display:flex;gap:0.8rem;flex-wrap:wrap;}}
.btn-p{{background:#ff6f00;color:white;padding:0.65rem 1.3rem;border-radius:6px;font-weight:700;font-size:0.88rem;text-decoration:none;display:inline-block;}}
.btn-g{{background:rgba(255,255,255,0.12);color:white;padding:0.65rem 1.3rem;border-radius:6px;font-weight:600;font-size:0.88rem;border:1px solid rgba(255,255,255,0.3);text-decoration:none;display:inline-block;}}
.stats{{display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;}}
.stat{{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.15);border-radius:8px;padding:0.9rem;text-align:center;}}
.stat .n{{font-size:2rem;font-weight:800;color:#ffd54f;line-height:1;}}
.stat .l{{font-size:0.7rem;opacity:0.85;margin-top:0.2rem;text-transform:uppercase;letter-spacing:0.05em;}}
.modalities{{background:#f5f7ff;border-top:3px solid #1a237e;padding:2rem 2rem;}}
.modalities h3{{text-align:center;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.1em;color:#5c6bc0;margin-bottom:1.2rem;font-weight:700;}}
.mod-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;max-width:800px;margin:0 auto;}}
.mod-card{{background:white;border-radius:8px;padding:1.2rem;text-align:center;border:1px solid #e8eaf6;}}
.mod-card .ico{{font-size:1.8rem;margin-bottom:0.5rem;}}
.mod-card h4{{font-size:0.88rem;font-weight:700;color:#1a237e;margin-bottom:0.3rem;}}
.mod-card p{{font-size:0.78rem;color:#555;line-height:1.5;}}
.team-strip{{background:#1a237e;color:white;padding:1rem 2rem;display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;}}
.team-strip .lbl{{font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;opacity:0.65;white-space:nowrap;}}
.team-tags{{display:flex;gap:0.5rem;flex-wrap:wrap;}}
.team-tag{{background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);border-radius:20px;padding:0.2rem 0.7rem;font-size:0.75rem;font-weight:600;}}
.sec{{padding:2.5rem 2rem;}}
.sec.bg{{background:#fafafa;}}
.sec-title{{text-align:center;margin-bottom:2rem;}}
.sec-title h2{{font-size:1.45rem;font-weight:700;color:#1a237e;}}
.sec-title p{{color:#555;font-size:0.88rem;margin-top:0.3rem;}}
.eixo{{margin-bottom:1.6rem;}}
.eixo-header{{display:flex;align-items:center;gap:0.7rem;margin-bottom:0.7rem;padding-bottom:0.4rem;border-bottom:2px solid #e8eaf6;}}
.eixo-num{{background:#1a237e;color:white;width:1.8rem;height:1.8rem;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.78rem;font-weight:800;flex-shrink:0;}}
.eixo-name{{font-size:0.9rem;font-weight:700;color:#283593;}}
.eixo-courses{{display:flex;gap:0.65rem;flex-wrap:wrap;}}
.cpill{{background:white;border:1px solid #c5cae9;border-radius:6px;padding:0.5rem 0.9rem;font-size:0.78rem;display:flex;align-items:center;gap:0.4rem;}}
.cpill .ico{{font-size:1rem;}}
.cpill .nm{{font-weight:600;color:#1a237e;display:block;font-size:0.77rem;}}
.cpill .inst{{font-size:0.67rem;color:#888;display:block;}}
.cpill .tag{{display:inline-block;background:#e8f5e9;color:#2e7d32;font-size:0.6rem;font-weight:700;padding:0.06rem 0.38rem;border-radius:10px;margin-top:0.1rem;}}
.see-all{{text-align:center;margin-top:1.4rem;}}
.btn-outline{{border:2px solid #1a237e;color:#1a237e;padding:0.55rem 1.5rem;border-radius:6px;font-weight:700;font-size:0.85rem;display:inline-block;text-decoration:none;}}
.steps{{display:grid;grid-template-columns:repeat(3,1fr);gap:1.2rem;text-align:center;}}
.step .num{{width:2.5rem;height:2.5rem;background:#1a237e;color:white;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;margin:0 auto 0.8rem;font-size:1rem;}}
.step h4{{font-size:0.9rem;font-weight:700;margin-bottom:0.3rem;}}
.step p{{font-size:0.8rem;color:#555;line-height:1.5;}}
.about-grid{{display:grid;grid-template-columns:1fr 1fr;gap:2rem;align-items:center;}}
.about-badge{{display:inline-block;background:#1a237e;color:white;font-size:0.7rem;padding:0.25rem 0.75rem;border-radius:20px;font-weight:600;margin-bottom:0.7rem;}}
.about h2{{font-size:1.35rem;color:#1a237e;font-weight:700;margin-bottom:0.7rem;}}
.about p{{font-size:0.86rem;color:#333;line-height:1.7;margin-bottom:0.5rem;}}
.mapa{{background:#c5cae9;border-radius:8px;height:160px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#5c6bc0;font-weight:600;font-size:0.85rem;gap:0.3rem;}}
.partners{{padding:1.8rem 2rem;border-top:1px solid #eee;text-align:center;}}
.partners h3{{font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;color:#999;margin-bottom:1rem;}}
.logos{{display:flex;justify-content:center;align-items:center;gap:2rem;flex-wrap:wrap;}}
.logo{{background:#f5f5f5;border:1px solid #ddd;border-radius:6px;padding:0.5rem 1.1rem;font-size:0.82rem;font-weight:700;color:#455;}}
.tds-footer{{background:#1a237e;color:white;padding:1.5rem 2rem;display:grid;grid-template-columns:2fr 1fr 1fr;gap:1.5rem;font-size:0.8rem;}}
.tds-footer h4{{font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;opacity:0.55;margin-bottom:0.5rem;}}
.tds-footer a{{color:rgba(255,255,255,0.75);display:block;margin-bottom:0.3rem;text-decoration:none;font-size:0.78rem;}}
.tds-footer .brand{{font-size:1rem;font-weight:800;margin-bottom:0.4rem;}}
.tds-footer .brand em{{color:#ffd54f;font-style:normal;}}
@media(max-width:700px){{
  .hero,.about-grid,.tds-footer{{grid-template-columns:1fr;}}
  .mod-grid,.steps{{grid-template-columns:1fr;}}
  .tds-nav-links{{display:none;}}
}}
</style>

<nav class="tds-nav">
  <div class="tds-brand">🌱 TDS <span class="badge">TOCANTINS</span></div>
  <div class="tds-nav-links">
    <a href="/sobre">Sobre</a>
    <a href="/courses">Cursos</a>
    <a href="/guia-aluno">Para Alunos</a>
    <a href="/guia-tutor">Para Tutores</a>
    <a href="/guia-gestor">Para Gestores</a>
  </div>
  <a href="/courses" class="cta">Acessar Plataforma</a>
</nav>

<div class="hero">
  <div>
    <h1>Capacitação profissional gratuita para <em>inclusão produtiva</em> no Tocantins</h1>
    <p>O programa TDS oferece trilhas formativas presenciais, online e mistas para beneficiários do CadÚnico em 36 municípios — com instrutores qualificados da UFT, tecnologia como suporte e certificação reconhecida.</p>
    <div class="hero-ctas">
      <a href="/guia-aluno" class="btn-p">📋 Como participar</a>
      <a href="/courses" class="btn-g">Ver cursos →</a>
    </div>
  </div>
  <div class="stats">
    <div class="stat"><div class="n">2.160</div><div class="l">Beneficiários CadÚnico</div></div>
    <div class="stat"><div class="n">36</div><div class="l">Municípios do Tocantins</div></div>
    <div class="stat"><div class="n">5</div><div class="l">Eixos formativos</div></div>
    <div class="stat"><div class="n">3</div><div class="l">Modalidades de ensino</div></div>
  </div>
</div>

<div class="modalities">
  <h3>Modalidades de capacitação</h3>
  <div class="mod-grid">
    <div class="mod-card"><div class="ico">🏫</div><h4>Presencial</h4><p>Encontros nos municípios com instrutores e equipe de campo. Metodologias participativas e práticas aplicadas ao território.</p></div>
    <div class="mod-card"><div class="ico">💻</div><h4>Online</h4><p>Conteúdos e trilhas via plataforma LMS e WhatsApp como canal de suporte, acompanhamento e comunicação.</p></div>
    <div class="mod-card"><div class="ico">🔄</div><h4>Mista</h4><p>Combinação de atividades presenciais e digitais, adaptada à conectividade e realidade de cada território.</p></div>
  </div>
</div>

<div class="team-strip">
  <span class="lbl">Corpo docente e de apoio</span>
  <div class="team-tags">
    <span class="team-tag">👨‍🏫 Professores UFT</span>
    <span class="team-tag">🎓 Pós-graduandos</span>
    <span class="team-tag">📚 Mestrandos</span>
    <span class="team-tag">🧑‍🎓 Graduandos</span>
    <span class="team-tag">🌱 Instrutores capacitados</span>
    <span class="team-tag">🤝 Estagiários TDS</span>
  </div>
</div>

<div class="sec bg">
  <div class="sec-title"><h2>Cursos por Eixo Temático</h2><p>5 eixos estruturantes do Projeto TDS — trilhas gratuitas com certificação</p></div>
  <div class="eixo">
    <div class="eixo-header"><div class="eixo-num">1</div><div class="eixo-name">Empreendedorismo Popular e Gestão de Negócios</div></div>
    <div class="eixo-courses">
      <div class="cpill"><span class="ico">💰</span><div><span class="nm">Finanças e Empreendedorismo</span><span class="inst">Gabriela</span><span class="tag">4 módulos</span></div></div>
      <div class="cpill"><span class="ico">👵</span><div><span class="nm">Educação Financeira — Melhor Idade</span><span class="inst">Gabriela</span><span class="tag">3 módulos</span></div></div>
      <div class="cpill"><span class="ico">🤖</span><div><span class="nm">IA no meu Bolso</span><span class="inst">Rafael</span><span class="tag">4 módulos</span></div></div>
      <div class="cpill"><span class="ico">🎬</span><div><span class="nm">Audiovisual e Conteúdo Digital</span><span class="inst">Pedro H.</span><span class="tag">4 módulos</span></div></div>
    </div>
  </div>
  <div class="eixo">
    <div class="eixo-header"><div class="eixo-num">2</div><div class="eixo-name">Formação Cooperativista Popular</div></div>
    <div class="eixo-courses">
      <div class="cpill"><span class="ico">🤝</span><div><span class="nm">Associativismo e Cooperativismo</span><span class="inst">Sofia</span><span class="tag">3 módulos</span></div></div>
    </div>
  </div>
  <div class="eixo">
    <div class="eixo-header"><div class="eixo-num">3</div><div class="eixo-name">Agricultura Familiar e Políticas Públicas Federais</div></div>
    <div class="eixo-courses">
      <div class="cpill"><span class="ico">🥩</span><div><span class="nm">SIM — Serviço de Inspeção Municipal</span><span class="inst">Sahaa</span><span class="tag">4 módulos</span></div></div>
    </div>
  </div>
  <div class="eixo">
    <div class="eixo-header"><div class="eixo-num">4</div><div class="eixo-name">Sistemas Produtivos Sustentáveis e Tecnologias Sociais</div></div>
    <div class="eixo-courses">
      <div class="cpill"><span class="ico">🌿</span><div><span class="nm">Agricultura Sustentável — SAFs</span><span class="inst">Valentine</span><span class="tag">4 módulos</span></div></div>
    </div>
  </div>
  <div class="eixo" style="opacity:0.55;">
    <div class="eixo-header"><div class="eixo-num" style="background:#9e9e9e;">5</div><div class="eixo-name" style="color:#888;">Inovação e Certificação Agroecológica <span style="font-weight:400;font-size:0.72rem;">(em desenvolvimento)</span></div></div>
    <div class="eixo-courses"><div class="cpill" style="border-style:dashed;"><span class="ico">🔬</span><div><span class="nm" style="color:#999;">Novos cursos em breve</span></div></div></div>
  </div>
  <div class="see-all"><a href="/courses" class="btn-outline">Acessar plataforma de cursos →</a></div>
</div>

<div class="sec">
  <div class="sec-title"><h2>Como funciona</h2></div>
  <div class="steps">
    <div class="step"><div class="num">1</div><h4>Identificação</h4><p>A equipe TDS identifica beneficiários do CadÚnico elegíveis nos 36 municípios atendidos pelo programa.</p></div>
    <div class="step"><div class="num">2</div><h4>Matrícula e trilha</h4><p>O beneficiário é matriculado na trilha mais adequada ao seu perfil, território e eixo temático.</p></div>
    <div class="step"><div class="num">3</div><h4>Capacitação e certificado</h4><p>Participa das atividades presenciais, online ou mistas e recebe certificado digital ao concluir.</p></div>
  </div>
</div>

<div class="sec bg">
  <div class="about-grid">
    <div class="about">
      <span class="about-badge">Bolsa nº 212/2026 — FAPTO/UFT · Programa Acredita/MDS</span>
      <h2>Sobre o Programa TDS</h2>
      <p>O <strong>Território de Desenvolvimento Social e Inclusão Produtiva (TDS)</strong> é coordenado pelo NERUDS/UFT com apoio da FAPTO e do Ministério do Desenvolvimento Social, no âmbito do Programa Acredita.</p>
      <p>Atende agricultores familiares, MEIs, trabalhadores informais, quilombolas e povos do campo nos territórios do Bico do Papagaio e municípios polo do Tocantins — com metodologias participativas e formação contextualizada ao território.</p>
      <a href="/sobre" style="color:#1a237e;font-size:0.85rem;font-weight:700;text-decoration:none;">Saiba mais sobre o programa →</a>
    </div>
    <div class="mapa">🗺️<span>36 municípios do Tocantins</span><span style="font-size:0.7rem;font-weight:400;color:#7986cb;">Bico do Papagaio · Jalapão · Dianópolis</span></div>
  </div>
</div>

<div class="partners">
  <h3>Realização e apoio</h3>
  <div class="logos">
    <div class="logo">🎓 NERUDS / UFT</div>
    <div class="logo">🏛️ FAPTO</div>
    <div class="logo">💻 Ipex Desenvolvimento</div>
    <div class="logo">🇧🇷 MDS · Programa Acredita</div>
  </div>
</div>

<footer class="tds-footer">
  <div>
    <div class="brand">🌱 TDS <em>Tocantins</em></div>
    <div style="opacity:0.55;font-size:0.73rem;line-height:1.7;">Inclusão Produtiva — NERUDS/UFT<br>Fomento: FAPTO — Bolsa nº 212/2026<br>Coord.: Juliana Aguiar de Melo</div>
  </div>
  <div>
    <h4>Acesso</h4>
    <a href="/courses">Plataforma LMS</a>
    <a href="/guia-aluno">Guia do Aluno</a>
    <a href="/guia-tutor">Guia do Tutor</a>
    <a href="/guia-gestor">Guia do Gestor</a>
  </div>
  <div>
    <h4>Institucional</h4>
    <a href="/sobre">Sobre o TDS</a>
    <a href="/sobre#municipios">36 Municípios</a>
    <a href="mailto:atendimento@ipexdesenvolvimento.cloud">Contato</a>
  </div>
</footer>"""

# --- SOBRE PAGE HTML ---
SOBRE_HTML = """<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:'Segoe UI',system-ui,sans-serif;}}
.pg-header{{background:#1a237e;color:white;padding:3rem 2rem;text-align:center;}}
.pg-header .breadcrumb{{font-size:0.78rem;opacity:0.65;margin-bottom:0.5rem;}}
.pg-header .breadcrumb a{{color:rgba(255,255,255,0.7);text-decoration:none;}}
.pg-header h1{{font-size:2rem;font-weight:800;}}
.pg-header p{{font-size:0.95rem;opacity:0.85;margin-top:0.5rem;max-width:600px;margin-left:auto;margin-right:auto;}}
.content{{max-width:860px;margin:0 auto;padding:2.5rem 2rem;}}
.card-sec{{background:#f5f7ff;border-left:4px solid #1a237e;border-radius:0 8px 8px 0;padding:1.5rem;margin-bottom:1.5rem;}}
.card-sec h2{{font-size:1.1rem;font-weight:700;color:#1a237e;margin-bottom:0.6rem;}}
.card-sec p{{font-size:0.88rem;color:#333;line-height:1.7;}}
.card-sec ul{{font-size:0.88rem;color:#333;line-height:1.9;padding-left:1.2rem;margin-top:0.3rem;}}
.eixos-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:1rem;margin-top:1rem;}}
.eixo-card{{background:white;border:1px solid #e8eaf6;border-radius:8px;padding:1rem;}}
.eixo-card .num{{background:#1a237e;color:white;width:1.6rem;height:1.6rem;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:0.72rem;font-weight:800;margin-bottom:0.4rem;}}
.eixo-card h3{{font-size:0.85rem;font-weight:700;color:#283593;margin-bottom:0.2rem;}}
.eixo-card p{{font-size:0.78rem;color:#555;}}
.team-section{{margin-top:1.5rem;}}
.team-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:0.8rem;margin-top:0.8rem;}}
.team-card{{background:white;border:1px solid #e0e0e0;border-radius:8px;padding:0.9rem;text-align:center;}}
.team-card .ico{{font-size:1.5rem;margin-bottom:0.3rem;}}
.team-card h4{{font-size:0.82rem;font-weight:700;color:#1a237e;}}
.team-card p{{font-size:0.73rem;color:#555;margin-top:0.2rem;}}
.back-link{{display:inline-block;margin-top:2rem;color:#1a237e;font-weight:700;text-decoration:none;font-size:0.88rem;}}
@media(max-width:600px){{.eixos-grid,.team-grid{{grid-template-columns:1fr;}}}}
</style>

<div class="pg-header">
  <div class="breadcrumb"><a href="/">Início</a> → Sobre o TDS</div>
  <h1>Sobre o Programa TDS</h1>
  <p>Território de Desenvolvimento Social e Inclusão Produtiva — NERUDS/UFT · FAPTO · MDS</p>
</div>

<div class="content">
  <div class="card-sec">
    <h2>🎯 O que é o TDS?</h2>
    <p>O <strong>Território de Desenvolvimento Social e Inclusão Produtiva (TDS)</strong> é um programa coordenado pelo Núcleo de Estudos Rurais e Desenvolvimento Sustentável da Universidade Federal do Tocantins (NERUDS/UFT), com fomento da Fundação de Apoio Científico e Tecnológico do Tocantins (FAPTO) e apoio do Ministério do Desenvolvimento Social (MDS) no âmbito do <strong>Programa Acredita</strong>.</p>
    <p style="margin-top:0.6rem;">Seu objetivo é promover a <strong>inclusão produtiva</strong> de famílias vulneráveis inscritas no CadÚnico, por meio de capacitação profissional contextualizada ao território, com metodologias participativas e acesso à tecnologia como ferramenta de apoio à formação.</p>
  </div>

  <div class="card-sec">
    <h2>🗺️ Público atendido e abrangência</h2>
    <p>O programa atende <strong>2.160 beneficiários</strong> do CadÚnico, com prioridade para pessoas em situação de pobreza ou extrema pobreza, entre 16 e 65 anos, nos seguintes perfis:</p>
    <ul>
      <li>Agricultores familiares e assentados da reforma agrária</li>
      <li>Microempreendedores Individuais (MEIs) e trabalhadores informais</li>
      <li>Comunidades quilombolas, indígenas e ribeirinhas</li>
      <li>Mulheres chefes de família em situação de vulnerabilidade</li>
    </ul>
    <p style="margin-top:0.6rem;"><strong>Abrangência territorial:</strong> 36 municípios do Tocantins nos territórios do Bico do Papagaio, Jalapão e Dianópolis.</p>
  </div>

  <div class="card-sec">
    <h2>📚 Modalidades de ensino</h2>
    <p>As capacitações são oferecidas em três modalidades, adaptadas à realidade de cada território e perfil de beneficiário:</p>
    <ul>
      <li><strong>🏫 Presencial:</strong> Encontros com instrutores e equipe de campo nos municípios atendidos, com metodologias participativas, oficinas práticas e atividades aplicadas.</li>
      <li><strong>💻 Online:</strong> Trilhas formativas via plataforma LMS com suporte por WhatsApp para comunicação, acompanhamento e dúvidas.</li>
      <li><strong>🔄 Mista (híbrida):</strong> Combinação de atividades presenciais e digitais, adaptada à conectividade e demanda de cada território.</li>
    </ul>
  </div>

  <div class="card-sec">
    <h2>🧩 Os 5 Eixos Formativos</h2>
    <p>O programa estrutura sua formação em 5 eixos temáticos que refletem as necessidades produtivas e sociais dos territórios atendidos:</p>
    <div class="eixos-grid">
      <div class="eixo-card"><div class="num">1</div><h3>Empreendedorismo Popular e Gestão de Negócios</h3><p>Finanças, planejamento, IA aplicada e conteúdo digital para MEIs e empreendedores locais.</p></div>
      <div class="eixo-card"><div class="num">2</div><h3>Formação Cooperativista Popular</h3><p>Princípios cooperativistas, associativismo e gestão coletiva para comunidades organizadas.</p></div>
      <div class="eixo-card"><div class="num">3</div><h3>Agricultura Familiar e Políticas Públicas</h3><p>Inspeção sanitária, acesso a políticas públicas e regularização para pequenos produtores.</p></div>
      <div class="eixo-card"><div class="num">4</div><h3>Sistemas Produtivos Sustentáveis</h3><p>Agroflorestas, práticas sustentáveis e tecnologias sociais para produção familiar.</p></div>
      <div class="eixo-card" style="grid-column:span 2;opacity:0.7;"><div class="num" style="background:#9e9e9e;">5</div><h3>Inovação e Certificação Agroecológica</h3><p>Certificação orgânica, rastreabilidade e inovação no campo. <em>Cursos em desenvolvimento.</em></p></div>
    </div>
  </div>

  <div class="card-sec team-section">
    <h2>👥 Equipe e corpo docente</h2>
    <p>O TDS conta com uma equipe multidisciplinar e qualificada da Universidade Federal do Tocantins:</p>
    <div class="team-grid">
      <div class="team-card"><div class="ico">👨‍🏫</div><h4>Professores UFT</h4><p>Docentes qualificados com expertise nas áreas de cada eixo temático</p></div>
      <div class="team-card"><div class="ico">🎓</div><h4>Pós-graduandos</h4><p>Especialistas e doutores aplicando pesquisa na formação territorial</p></div>
      <div class="team-card"><div class="ico">📚</div><h4>Mestrandos</h4><p>Pesquisadores em formação contribuindo com metodologias inovadoras</p></div>
      <div class="team-card"><div class="ico">🧑‍🎓</div><h4>Graduandos</h4><p>Estudantes da UFT atuando como monitores e facilitadores</p></div>
      <div class="team-card"><div class="ico">🌱</div><h4>Instrutores capacitados</h4><p>Profissionais formados especificamente para atuação no programa</p></div>
      <div class="team-card"><div class="ico">🤝</div><h4>Estagiários TDS</h4><p>Equipe de campo responsável pelo contato e acompanhamento dos beneficiários</p></div>
    </div>
  </div>

  <div class="card-sec">
    <h2>🏛️ Realização e apoio institucional</h2>
    <ul>
      <li><strong>Coordenação:</strong> NERUDS — Núcleo de Estudos Rurais e Desenvolvimento Sustentável / UFT</li>
      <li><strong>Coordenadora:</strong> Prof.ª Juliana Aguiar de Melo</li>
      <li><strong>Fomento:</strong> FAPTO — Fundação de Apoio Científico e Tecnológico do Tocantins (Bolsa nº 212/2026)</li>
      <li><strong>Apoio federal:</strong> MDS — Ministério do Desenvolvimento Social · Programa Acredita</li>
      <li><strong>Infraestrutura tecnológica:</strong> Ipex Desenvolvimento</li>
    </ul>
  </div>

  <a href="/" class="back-link">← Voltar para o início</a>
</div>"""

# --- GUIA ALUNO HTML ---
GUIA_ALUNO_HTML = """<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:'Segoe UI',system-ui,sans-serif;}}
.pg-header{{background:#2e7d32;color:white;padding:3rem 2rem;text-align:center;}}
.pg-header .breadcrumb{{font-size:0.78rem;opacity:0.65;margin-bottom:0.5rem;}}
.pg-header .breadcrumb a{{color:rgba(255,255,255,0.7);text-decoration:none;}}
.pg-header h1{{font-size:1.8rem;font-weight:800;}}
.pg-header p{{font-size:0.92rem;opacity:0.85;margin-top:0.5rem;max-width:580px;margin-left:auto;margin-right:auto;}}
.content{{max-width:800px;margin:0 auto;padding:2.5rem 2rem;}}
.qa{{background:#f9f9f9;border-radius:8px;padding:1.2rem 1.4rem;margin-bottom:1rem;border-left:4px solid #2e7d32;}}
.qa .q{{font-size:0.95rem;font-weight:700;color:#1b5e20;margin-bottom:0.5rem;}}
.qa .a{{font-size:0.88rem;color:#333;line-height:1.7;}}
.qa .a ul{{padding-left:1.2rem;margin-top:0.3rem;line-height:1.9;}}
.highlight{{background:#e8f5e9;border-radius:8px;padding:1.2rem 1.4rem;margin:1.5rem 0;text-align:center;}}
.highlight h3{{font-size:1rem;color:#1b5e20;font-weight:700;}}
.highlight p{{font-size:0.88rem;color:#2e7d32;margin-top:0.3rem;}}
.highlight .wpp{{font-size:1.5rem;font-weight:800;color:#1b5e20;margin-top:0.5rem;display:block;}}
.sec-title{{font-size:0.72rem;text-transform:uppercase;letter-spacing:0.1em;color:#2e7d32;font-weight:700;margin:2rem 0 0.8rem;}}
.back-link{{display:inline-block;margin-top:2rem;color:#1a237e;font-weight:700;text-decoration:none;font-size:0.88rem;}}
</style>

<div class="pg-header">
  <div class="breadcrumb"><a href="/">Início</a> → Guia do Aluno</div>
  <h1>📱 Guia do Aluno TDS</h1>
  <p>Tudo que você precisa saber para participar do programa de capacitação. Linguagem simples, para você.</p>
</div>

<div class="content">
  <div class="highlight">
    <h3>🌱 Quer participar do TDS?</h3>
    <p>Aguarde o contato da nossa equipe de estagiários pelo WhatsApp ou procure a prefeitura do seu município.</p>
    <p style="font-size:0.8rem;color:#555;margin-top:0.5rem;">O contato é feito pela equipe TDS — não pague nada para se inscrever. O programa é 100% gratuito.</p>
  </div>

  <div class="sec-title">Perguntas frequentes</div>

  <div class="qa">
    <div class="q">O que é o programa TDS?</div>
    <div class="a">O TDS (Território de Desenvolvimento Social e Inclusão Produtiva) é um programa da Universidade Federal do Tocantins (UFT) com apoio do governo federal. Ele oferece <strong>cursos gratuitos de capacitação profissional</strong> para pessoas cadastradas no CadÚnico em 36 municípios do Tocantins.</div>
  </div>

  <div class="qa">
    <div class="q">Quem pode participar?</div>
    <div class="a">Pode participar quem:
      <ul>
        <li>Está inscrito no <strong>CadÚnico</strong></li>
        <li>Tem entre 16 e 65 anos</li>
        <li>Mora em um dos 36 municípios atendidos pelo programa</li>
        <li>Está em situação de pobreza ou vulnerabilidade social</li>
      </ul>
      Tem prioridade: agricultores familiares, MEIs, trabalhadores informais, mulheres chefes de família, quilombolas e comunidades tradicionais.
    </div>
  </div>

  <div class="qa">
    <div class="q">Como funciona o curso? Preciso ir a algum lugar?</div>
    <div class="a">O TDS oferece 3 modalidades:
      <ul>
        <li><strong>Presencial:</strong> encontros com instrutores no seu município</li>
        <li><strong>Online:</strong> conteúdo disponível na plataforma e suporte pelo WhatsApp</li>
        <li><strong>Mista:</strong> combinação de presencial e online</li>
      </ul>
      A modalidade depende do seu município e do curso escolhido. Nossa equipe vai explicar como será no seu caso.
    </div>
  </div>

  <div class="qa">
    <div class="q">Preciso ter internet ou celular moderno?</div>
    <div class="a">Não é necessário um celular caro. Para a modalidade online, você precisa de acesso ao WhatsApp. Para cursos presenciais, não é necessário nenhum equipamento. Casos sem acesso à internet são atendidos prioritariamente na modalidade presencial.</div>
  </div>

  <div class="qa">
    <div class="q">O curso tem custo? Preciso pagar alguma coisa?</div>
    <div class="a"><strong>Não. O programa TDS é totalmente gratuito.</strong> Não pague nada para ninguém que diga ser do TDS. Em caso de dúvida, entre em contato com a coordenação pelo e-mail oficial.</div>
  </div>

  <div class="qa">
    <div class="q">Vou receber certificado?</div>
    <div class="a">Sim! Ao concluir o curso, você recebe um <strong>certificado digital</strong> emitido pela UFT. O certificado pode ser usado para comprovar a capacitação em processos de crédito, editais e oportunidades de emprego.</div>
  </div>

  <div class="qa">
    <div class="q">Quanto tempo dura o curso?</div>
    <div class="a">A duração varia por curso e modalidade. Em geral, cada trilha tem entre 3 e 4 módulos, com atividades semanais. Nossa equipe informa o cronograma completo no momento da matrícula.</div>
  </div>

  <div class="qa">
    <div class="q">Como me inscrevo?</div>
    <div class="a">A inscrição é feita pela equipe TDS. Você será contactado pelo WhatsApp pelos estagiários do programa, que verificarão seu CadÚnico e explicarão os próximos passos. Você também pode procurar a assistência social do seu município.</div>
  </div>

  <div class="highlight">
    <h3>❓ Dúvidas? Fale com o Tutor IA</h3>
    <p>Use o chat no canto da tela para tirar dúvidas sobre os cursos e o programa. O tutor virtual está disponível 24h. (Versão beta — em fase de testes)</p>
  </div>

  <a href="/" class="back-link">← Voltar para o início</a>
</div>"""

# --- GUIA TUTOR HTML ---
GUIA_TUTOR_HTML = """<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:'Segoe UI',system-ui,sans-serif;}}
.pg-header{{background:#1565c0;color:white;padding:3rem 2rem;text-align:center;}}
.pg-header .breadcrumb{{font-size:0.78rem;opacity:0.65;margin-bottom:0.5rem;}}
.pg-header .breadcrumb a{{color:rgba(255,255,255,0.7);text-decoration:none;}}
.pg-header h1{{font-size:1.8rem;font-weight:800;}}
.pg-header p{{font-size:0.92rem;opacity:0.85;margin-top:0.5rem;max-width:580px;margin-left:auto;margin-right:auto;}}
.content{{max-width:860px;margin:0 auto;padding:2.5rem 2rem;}}
.step-sec{{margin-bottom:2rem;}}
.step-sec .step-header{{display:flex;align-items:center;gap:0.8rem;margin-bottom:0.8rem;}}
.step-sec .num{{background:#1565c0;color:white;width:2rem;height:2rem;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:0.85rem;flex-shrink:0;}}
.step-sec h2{{font-size:1rem;font-weight:700;color:#0d47a1;}}
.step-sec .body{{background:#f3f8ff;border-radius:8px;padding:1.2rem 1.4rem;border-left:4px solid #1565c0;font-size:0.87rem;color:#333;line-height:1.7;}}
.step-sec .body ul,.step-sec .body ol{{padding-left:1.2rem;margin-top:0.4rem;line-height:1.9;}}
.step-sec .body code{{background:#e3f2fd;color:#0d47a1;padding:0.1rem 0.4rem;border-radius:3px;font-family:monospace;font-size:0.85em;}}
.step-sec .body strong{{color:#0d47a1;}}
.info-box{{background:#e1f5fe;border-radius:8px;padding:1rem 1.2rem;margin:1.5rem 0;font-size:0.85rem;color:#01579b;line-height:1.6;}}
.back-link{{display:inline-block;margin-top:2rem;color:#1a237e;font-weight:700;text-decoration:none;font-size:0.88rem;}}
</style>

<div class="pg-header">
  <div class="breadcrumb"><a href="/">Início</a> → Guia do Tutor</div>
  <h1>🎓 Guia do Tutor / Instrutor</h1>
  <p>Manual completo para instrutores e tutores do Projeto TDS — como usar a plataforma LMS e gerenciar suas turmas.</p>
</div>

<div class="content">
  <div class="info-box">
    💡 <strong>Sua conta de tutor foi criada pela equipe TDS.</strong> Verifique o e-mail com suas credenciais. Dúvidas técnicas: entre em contato com Rafael (<a href="mailto:rafael@ipexdesenvolvimento.cloud" style="color:#0d47a1;">rafael@ipexdesenvolvimento.cloud</a>)
  </div>

  <div class="step-sec">
    <div class="step-header"><div class="num">1</div><h2>Acessando a plataforma</h2></div>
    <div class="body">
      <ol>
        <li>Acesse <strong>lms.ipexdesenvolvimento.cloud</strong> pelo navegador</li>
        <li>Clique em <strong>"Login"</strong> no canto superior direito</li>
        <li>Use o e-mail fornecido pela equipe TDS (formato: <code>seunome@ipexdesenvolvimento.cloud</code>)</li>
        <li>Senha padrão: <code>TDSTutor@2024</code> — troque após o primeiro acesso</li>
        <li>Após login, você verá o painel com seus cursos em <strong>"Meus Cursos"</strong></li>
      </ol>
    </div>
  </div>

  <div class="step-sec">
    <div class="step-header"><div class="num">2</div><h2>Visão geral do seu curso</h2></div>
    <div class="body">
      Cada instrutor é responsável por um ou mais cursos. No seu curso você encontrará:
      <ul>
        <li><strong>Capítulos:</strong> seções temáticas do curso (ex.: "Módulo 1 — Introdução")</li>
        <li><strong>Aulas:</strong> conteúdos dentro de cada capítulo (texto, vídeo, quiz)</li>
        <li><strong>Turma (Batch):</strong> grupo de alunos matriculados no seu curso</li>
        <li><strong>Progresso:</strong> acompanhamento de quais alunos concluíram cada aula</li>
      </ul>
      Para acessar seu curso: Menu → <strong>Cursos</strong> → clique no nome do seu curso.
    </div>
  </div>

  <div class="step-sec">
    <div class="step-header"><div class="num">3</div><h2>Editando aulas e conteúdo</h2></div>
    <div class="body">
      <ol>
        <li>No seu curso, clique no capítulo que deseja editar</li>
        <li>Clique na aula específica ou em <strong>"Nova Aula"</strong> para adicionar conteúdo</li>
        <li>O editor suporta: texto rico, imagens, vídeos (YouTube/Vimeo), quizzes e anexos PDF</li>
        <li>Sempre clique em <strong>"Salvar"</strong> após editar</li>
        <li>Para publicar uma aula, marque como <strong>"Publicado"</strong> no formulário da aula</li>
      </ol>
      <strong>Atenção:</strong> aulas não publicadas ficam invisíveis para os alunos mas visíveis para você como rascunho.
    </div>
  </div>

  <div class="step-sec">
    <div class="step-header"><div class="num">4</div><h2>Gerenciando sua turma</h2></div>
    <div class="body">
      As turmas (Batches) são criadas pela coordenação do TDS. Como tutor, você pode:
      <ul>
        <li>Ver a lista de alunos matriculados na sua turma</li>
        <li>Verificar o status de cada aluno (matriculado, em progresso, concluído)</li>
        <li>Enviar comunicados para a turma (via Chatwoot/WhatsApp — coordenar com a equipe)</li>
      </ul>
      Para acessar: Menu → <strong>Turmas</strong> → selecione sua turma.
    </div>
  </div>

  <div class="step-sec">
    <div class="step-header"><div class="num">5</div><h2>Acompanhando progresso dos alunos</h2></div>
    <div class="body">
      No painel do seu curso, você pode ver:
      <ul>
        <li>Quantos alunos completaram cada aula</li>
        <li>Alunos que não acessaram nas últimas semanas (inativos)</li>
        <li>Resultados de quizzes e avaliações por aluno</li>
      </ul>
      Alunos com dificuldade de acesso devem ser reportados à coordenação para suporte ou mudança de modalidade.
    </div>
  </div>

  <div class="step-sec">
    <div class="step-header"><div class="num">6</div><h2>Avaliações e certificados</h2></div>
    <div class="body">
      O certificado é emitido automaticamente pela plataforma quando o aluno conclui todas as aulas obrigatórias. Como tutor:
      <ul>
        <li>Certifique-se de que todas as aulas do curso estão marcadas como obrigatórias se necessário</li>
        <li>Quizzes com nota mínima podem ser configurados — solicite à coordenação se precisar ajustar</li>
        <li>O certificado é digital, emitido pela UFT, e o aluno recebe por e-mail/plataforma</li>
      </ul>
    </div>
  </div>

  <div class="step-sec">
    <div class="step-header"><div class="num">7</div><h2>Suporte técnico</h2></div>
    <div class="body">
      Em caso de problemas técnicos na plataforma:
      <ul>
        <li>📧 E-mail: <strong>atendimento@ipexdesenvolvimento.cloud</strong></li>
        <li>🔧 Responsável técnico: Rafael Luciano (admin@neruds.org)</li>
        <li>💬 Use o chat desta página (Tutor IA) para dúvidas rápidas sobre o programa</li>
      </ul>
    </div>
  </div>

  <a href="/" class="back-link">← Voltar para o início</a>
</div>"""

# --- GUIA GESTOR HTML ---
GUIA_GESTOR_HTML = """<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:'Segoe UI',system-ui,sans-serif;}}
.pg-header{{background:#4a148c;color:white;padding:3rem 2rem;text-align:center;}}
.pg-header .breadcrumb{{font-size:0.78rem;opacity:0.65;margin-bottom:0.5rem;}}
.pg-header .breadcrumb a{{color:rgba(255,255,255,0.7);text-decoration:none;}}
.pg-header h1{{font-size:1.8rem;font-weight:800;}}
.pg-header p{{font-size:0.92rem;opacity:0.85;margin-top:0.5rem;max-width:580px;margin-left:auto;margin-right:auto;}}
.content{{max-width:860px;margin:0 auto;padding:2.5rem 2rem;}}
.sec-card{{background:#faf5ff;border-left:4px solid #7b1fa2;border-radius:0 8px 8px 0;padding:1.3rem 1.5rem;margin-bottom:1.5rem;}}
.sec-card h2{{font-size:1rem;font-weight:700;color:#4a148c;margin-bottom:0.7rem;}}
.sec-card p,.sec-card li{{font-size:0.87rem;color:#333;line-height:1.7;}}
.sec-card ul,.sec-card ol{{padding-left:1.2rem;margin-top:0.3rem;line-height:1.9;}}
.arch-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:0.8rem;margin-top:0.8rem;}}
.arch-card{{background:white;border:1px solid #e1bee7;border-radius:6px;padding:0.8rem;text-align:center;}}
.arch-card .ico{{font-size:1.4rem;margin-bottom:0.3rem;}}
.arch-card h4{{font-size:0.78rem;font-weight:700;color:#4a148c;margin-bottom:0.2rem;}}
.arch-card p{{font-size:0.72rem;color:#555;}}
.flow{{display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;margin-top:0.7rem;font-size:0.82rem;}}
.flow .step{{background:#e1bee7;border-radius:4px;padding:0.3rem 0.6rem;color:#4a148c;font-weight:600;}}
.flow .arrow{{color:#9c27b0;font-size:1rem;}}
.metric-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:0.8rem;margin-top:0.8rem;}}
.metric{{background:white;border:1px solid #e1bee7;border-radius:6px;padding:0.8rem;}}
.metric h4{{font-size:0.78rem;font-weight:700;color:#4a148c;margin-bottom:0.2rem;}}
.metric p{{font-size:0.75rem;color:#555;}}
.access-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:0.8rem;margin-top:0.8rem;}}
.access-card{{background:white;border:1px solid #e1bee7;border-radius:6px;padding:0.9rem;}}
.access-card h4{{font-size:0.82rem;font-weight:700;color:#4a148c;margin-bottom:0.3rem;}}
.access-card a{{color:#7b1fa2;font-size:0.8rem;font-weight:600;text-decoration:none;display:block;margin-top:0.2rem;}}
.back-link{{display:inline-block;margin-top:2rem;color:#1a237e;font-weight:700;text-decoration:none;font-size:0.88rem;}}
@media(max-width:600px){{.arch-grid,.metric-grid,.access-grid{{grid-template-columns:1fr;}}}}
</style>

<div class="pg-header">
  <div class="breadcrumb"><a href="/">Início</a> → Guia do Gestor</div>
  <h1>📊 Guia do Gestor</h1>
  <p>Visão executiva da plataforma TDS — arquitetura tecnológica, fluxos, métricas e acesso administrativo para equipes NERUDS/UFT/FAPTO/MDS.</p>
</div>

<div class="content">

  <div class="sec-card">
    <h2>🏛️ Visão geral do programa</h2>
    <p>O TDS opera por meio de uma infraestrutura tecnológica integrada que suporta as 3 modalidades de ensino (presencial, online e mista), o gerenciamento de beneficiários, o acompanhamento de progresso e a emissão de certificados.</p>
    <ul style="margin-top:0.5rem;">
      <li><strong>2.160 beneficiários</strong> em 36 municípios do Tocantins</li>
      <li><strong>7 cursos ativos</strong> organizados em 5 eixos temáticos</li>
      <li><strong>6 turmas</strong> abertas com vagas de 200 a 400 por turma</li>
      <li><strong>Equipe:</strong> professores UFT, pós-graduandos, mestrandos, graduandos e estagiários</li>
    </ul>
  </div>

  <div class="sec-card">
    <h2>🔧 Arquitetura tecnológica</h2>
    <p>A plataforma é composta por serviços integrados, hospedados em infraestrutura própria (<strong>ipexdesenvolvimento.cloud</strong>):</p>
    <div class="arch-grid">
      <div class="arch-card"><div class="ico">📚</div><h4>Frappe LMS</h4><p>Plataforma de cursos, matrículas e certificados</p></div>
      <div class="arch-card"><div class="ico">💬</div><h4>Chatwoot</h4><p>CRM de atendimento e comunicação multicanal</p></div>
      <div class="arch-card"><div class="ico">🤖</div><h4>N8N</h4><p>Automação de fluxos e integração entre sistemas</p></div>
      <div class="arch-card"><div class="ico">🧠</div><h4>AnythingLLM (RAG)</h4><p>Base de conhecimento do projeto com IA generativa</p></div>
      <div class="arch-card"><div class="ico">📱</div><h4>WhatsApp Cloud API</h4><p>Canal de comunicação com beneficiários</p></div>
      <div class="arch-card"><div class="ico">📧</div><h4>Poste.io (E-mail)</h4><p>Servidor de e-mail institucional</p></div>
    </div>
  </div>

  <div class="sec-card">
    <h2>🔄 Fluxo completo do beneficiário</h2>
    <div class="flow">
      <span class="step">CadÚnico verificado</span><span class="arrow">→</span>
      <span class="step">Contato estagiário (WhatsApp)</span><span class="arrow">→</span>
      <span class="step">Matrícula no LMS</span><span class="arrow">→</span>
      <span class="step">Capacitação (presencial/online/mista)</span><span class="arrow">→</span>
      <span class="step">Conclusão de módulos</span><span class="arrow">→</span>
      <span class="step">Certificado digital (UFT)</span>
    </div>
    <p style="margin-top:0.8rem;font-size:0.83rem;color:#555;">O Tutor IA (chatbot) está disponível em todas as páginas para tirar dúvidas dos beneficiários 24h via WhatsApp e web. Conversas são monitoradas pela equipe técnica e usadas para aprimorar o sistema.</p>
  </div>

  <div class="sec-card">
    <h2>📈 Métricas e relatórios disponíveis</h2>
    <p>Acesse o painel administrativo do LMS para relatórios em tempo real:</p>
    <div class="metric-grid">
      <div class="metric"><h4>Matrículas por curso</h4><p>Total de alunos por curso e turma, status de matrícula e progresso geral</p></div>
      <div class="metric"><h4>Progresso por aluno</h4><p>Aulas concluídas, quizzes realizados, tempo de acesso e última atividade</p></div>
      <div class="metric"><h4>Conversas Chatwoot</h4><p>Volume de atendimentos, tempo de resposta do bot e conversas escaladas para humanos</p></div>
      <div class="metric"><h4>Certificados emitidos</h4><p>Histórico de certificações por curso, período e município de origem</p></div>
    </div>
  </div>

  <div class="sec-card">
    <h2>🔐 Acesso aos sistemas</h2>
    <div class="access-grid">
      <div class="access-card"><h4>📚 LMS (Admin)</h4><a href="https://lms.ipexdesenvolvimento.cloud/app">lms.ipexdesenvolvimento.cloud/app</a><p style="font-size:0.75rem;color:#555;margin-top:0.3rem;">Conta Administrator — solicite acesso à coordenação</p></div>
      <div class="access-card"><h4>💬 Chatwoot</h4><a href="https://chat.ipexdesenvolvimento.cloud">chat.ipexdesenvolvimento.cloud</a><p style="font-size:0.75rem;color:#555;margin-top:0.3rem;">Painel de atendimentos e métricas de conversas</p></div>
      <div class="access-card"><h4>🤖 N8N (Automações)</h4><a href="https://n8n.ipexdesenvolvimento.cloud">n8n.ipexdesenvolvimento.cloud</a><p style="font-size:0.75rem;color:#555;margin-top:0.3rem;">Visualização dos fluxos de integração</p></div>
      <div class="access-card"><h4>🧠 RAG (AnythingLLM)</h4><a href="https://rag.ipexdesenvolvimento.cloud">rag.ipexdesenvolvimento.cloud</a><p style="font-size:0.75rem;color:#555;margin-top:0.3rem;">Base de conhecimento do projeto com IA</p></div>
    </div>
  </div>

  <div class="sec-card">
    <h2>👥 Equipe e responsabilidades</h2>
    <ul>
      <li><strong>Coordenação científica:</strong> Prof.ª Juliana Aguiar de Melo (NERUDS/UFT)</li>
      <li><strong>Gestão técnica da plataforma:</strong> Rafael Luciano — admin@neruds.org</li>
      <li><strong>Instrutores por curso:</strong> Valentine (Agricultura), Pedro H. (Audiovisual), Gabriela (Finanças/Melhor Idade), Rafael (IA), Sofia (Cooperativismo), Sahaa (SIM)</li>
      <li><strong>Estagiários de campo:</strong> responsáveis pelo contato direto e acompanhamento dos 2.160 beneficiários</li>
    </ul>
  </div>

  <div class="sec-card">
    <h2>🔒 Política de dados e privacidade</h2>
    <ul>
      <li>Dados dos beneficiários (CadÚnico) são tratados conforme a LGPD</li>
      <li>Conversas com o chatbot (Tutor IA) são monitoradas pela equipe técnica para fins de melhoria do sistema — os usuários são informados no banner beta do widget</li>
      <li>Dados de progresso e matrículas são armazenados em servidor próprio hospedado no Brasil</li>
      <li>Nenhum dado é compartilhado com terceiros fora do escopo do programa</li>
    </ul>
  </div>

  <div class="sec-card">
    <h2>📞 Contato técnico</h2>
    <ul>
      <li>📧 Suporte técnico: atendimento@ipexdesenvolvimento.cloud</li>
      <li>👤 Responsável: Rafael Luciano (admin@neruds.org)</li>
      <li>🏛️ NERUDS/UFT: neruds@uft.edu.br</li>
    </ul>
  </div>

  <a href="/" class="back-link">← Voltar para o início</a>
</div>"""

if __name__ == "__main__":
    print("=== Criando páginas institucionais TDS ===\n")
    create_page("tds-home", "TDS — Inclusão Produtiva no Tocantins",
        "Capacitação profissional gratuita para beneficiários do CadÚnico em 36 municípios do Tocantins.",
        LANDING_HTML)
    create_page("sobre", "Sobre o Programa TDS",
        "Conheça o Território de Desenvolvimento Social — NERUDS/UFT, FAPTO, Programa Acredita/MDS.",
        SOBRE_HTML)
    create_page("guia-aluno", "Guia do Aluno TDS",
        "Tudo sobre como participar do TDS — inscrição, modalidades, certificado e perguntas frequentes.",
        GUIA_ALUNO_HTML)
    create_page("guia-tutor", "Guia do Tutor TDS",
        "Manual completo para instrutores do TDS — acesso ao LMS, edição de conteúdo e gestão de turmas.",
        GUIA_TUTOR_HTML)
    create_page("guia-gestor", "Guia do Gestor TDS",
        "Visão executiva da plataforma TDS — arquitetura, fluxos, métricas e acesso para NERUDS/UFT/FAPTO/MDS.",
        GUIA_GESTOR_HTML)
    print("\n=== Concluído ===")
PYEOF

if __name__ == "__main__":
    create_page("tds-home", ...)
```

- [ ] **Step 4: Executar o script**

```bash
python3 /tmp/create_pages.py
```

Esperado: 5 linhas `✅ Criado:` no output.

- [ ] **Step 5: Verificar páginas no ar**

```bash
for route in tds-home sobre guia-aluno guia-tutor guia-gestor; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://lms.ipexdesenvolvimento.cloud/$route")
  echo "$route: $STATUS"
done
```

Esperado: todos retornando `200`.

---

## Task 6: Configurar home page do LMS para a nova landing

**Files:** Frappe Website Settings

- [ ] **Step 1: Atualizar home page nas configurações do Website**

```bash
curl -s -X PUT "https://lms.ipexdesenvolvimento.cloud/api/resource/Website%20Settings/Website%20Settings" \
  -H "Authorization: token 056681de29fce7a:7c78dcba6e3c5d1" \
  -H "Content-Type: application/json" \
  -d '{"home_page": "tds-home"}' \
  2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
hp = d.get('data', {}).get('home_page', d.get('home_page','?'))
print('home_page configurado para:', hp)
"
```

- [ ] **Step 2: Verificar redirect da raiz**

```bash
curl -sL -o /dev/null -w "%{http_code} %{url_effective}" https://lms.ipexdesenvolvimento.cloud/
```

Esperado: `200 https://lms.ipexdesenvolvimento.cloud/tds-home` (ou redirect seguido de 200).

- [ ] **Step 3: Commit**

```bash
cd /root/projeto-tds && git add docs/ && git commit -m "feat: spec e plano das páginas institucionais TDS

- Design doc: docs/superpowers/specs/2026-04-09-tds-paginas-institucionais-design.md
- Plano: docs/superpowers/plans/2026-04-09-tds-paginas-institucionais.md
- 5 páginas: landing, sobre, guia-aluno, guia-tutor, guia-gestor
- Widget Chatwoot beta integrado
- Cursos organizados pelos 5 eixos TDS"
```

---

## Task 7: Verificação final end-to-end

- [ ] **Step 1: Verificar todas as páginas respondem 200**

```bash
for url in \
  "https://lms.ipexdesenvolvimento.cloud/" \
  "https://lms.ipexdesenvolvimento.cloud/tds-home" \
  "https://lms.ipexdesenvolvimento.cloud/sobre" \
  "https://lms.ipexdesenvolvimento.cloud/guia-aluno" \
  "https://lms.ipexdesenvolvimento.cloud/guia-tutor" \
  "https://lms.ipexdesenvolvimento.cloud/guia-gestor"; do
  STATUS=$(curl -sL -o /dev/null -w "%{http_code}" "$url")
  echo "$STATUS $url"
done
```

Esperado: todos `200`.

- [ ] **Step 2: Verificar catálogo de cursos limpo**

```bash
docker exec kreativ-backend bench --site lms.ipexdesenvolvimento.cloud mariadb \
  --execute "SELECT COUNT(*) as publicados FROM \`tabLMS Course\` WHERE published=1;"
```

Esperado: número significativamente menor que 106.

- [ ] **Step 3: Verificar RAG responde sem think tags**

```bash
curl -s --max-time 30 -X POST "https://rag.ipexdesenvolvimento.cloud/api/v1/workspace/tds/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
  -d '{"message":"O que é o TDS?","mode":"chat"}' \
  2>/dev/null | python3 -c "
import sys,json,re
d=json.load(sys.stdin)
r=d.get('textResponse','')
print('think tags:', bool(re.search(r'<think>',r)))
print('resposta ok:', len(r)>10)
"
```

Esperado: `think tags: False`, `resposta ok: True`.

- [ ] **Step 4: Verificar healthchecks**

```bash
docker ps --format '{{.Names}}\t{{.Status}}' | grep -E "chatwoot|n8n"
```

Esperado: ambos com `(healthy)`.

- [ ] **Step 5: Commit final**

```bash
cd /root/projeto-tds && git add -A && git commit -m "feat: plataforma TDS completa — páginas institucionais + limpeza LMS

- Landing page /tds-home com 5 eixos, 3 modalidades, equipe UFT
- Páginas: /sobre, /guia-aluno, /guia-tutor, /guia-gestor
- Widget Chatwoot beta (inbox #7) em todas as páginas
- Catálogo limpo: duplicatas e demo despublicados
- Healthchecks corrigidos (wget ao invés de curl)
- RAG fix: workspace tds voltou a usar OpenRouter (sem override Ollama)
- <think> strip: configurado no N8N"
```
