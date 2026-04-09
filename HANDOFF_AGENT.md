# Handoff — Páginas Institucionais TDS · 2026-04-09

Este documento é um handoff para um agente continuar a execução do plano de implementação das páginas institucionais do LMS TDS em produção.

---

## Contexto do projeto

**Frappe LMS** em produção: `https://lms.ipexdesenvolvimento.cloud`  
**Projeto TDS** — Território de Desenvolvimento Social e Inclusão Produtiva, NERUDS/UFT/FAPTO/MDS  
**Diretório de trabalho:** `/root/projeto-tds`  
**Plano completo:** `/root/projeto-tds/docs/superpowers/plans/2026-04-09-tds-paginas-institucionais.md`  
**Design spec:** `/root/projeto-tds/docs/superpowers/specs/2026-04-09-tds-paginas-institucionais-design.md`

---

## Credenciais necessárias

| Serviço | Credencial |
|---------|-----------|
| Frappe API | `Authorization: token 056681de29fce7a:7c78dcba6e3c5d1` |
| Frappe URL | `https://lms.ipexdesenvolvimento.cloud` |
| Chatwoot widget token | `HwBawyqmiKTAbNzF8yAnzHCD` |
| Chatwoot base URL | `https://chat.ipexdesenvolvimento.cloud` |
| AnythingLLM API key | `W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0` |
| AnythingLLM URL | `https://rag.ipexdesenvolvimento.cloud` |
| N8N workflow ID | `XYcnRlPZSlfGXOWb` |
| N8N URL | `https://n8n.ipexdesenvolvimento.cloud` |
| MariaDB (via bench) | `docker exec kreativ-backend bench --site lms.ipexdesenvolvimento.cloud mariadb` |

---

## O que já foi feito (NÃO refazer)

### ✅ Task 1: LMS Cleanup
- Curso demo `a-guide-to-frappe-learning` despublicado
- Versões antigas de 7 cursos TDS despublicadas (sem sufixo ou com sufixo mais baixo)
- 7 cursos keeper confirmados publicados com capítulos:
  - `agricultura-sustent-vel-sistemas-agroflorestais-2`
  - `audiovisual-e-produ-o-de-conte-do-digital-2`
  - `finan-as-e-empreendedorismo-2`
  - `ia-no-meu-bolso-intelig-ncia-artificial-para-o-dia-a-dia-2`
  - `sim-servi-o-de-inspe-o-municipal-para-pequenos-produtores-2`
  - `associativismo-e-cooperativismo-4`
  - `educa-o-financeira-para-a-melhor-idade`

### ✅ Task 2: Batches vinculados aos cursos
Todos os 6 batches foram vinculados via Frappe API (campo `courses`):
- `turma-tds-agricultura-sustent-vel-2026` → `agricultura-sustent-vel-sistemas-agroflorestais-2`
- `turma-tds-associativismo-e-cooperativismo-2026` → `associativismo-e-cooperativismo-4`
- `turma-tds-audiovisual-e-conte-do-digital-2026` → `audiovisual-e-produ-o-de-conte-do-digital-2`
- `turma-tds-finan-as-e-empreendedorismo-2026` → `finan-as-e-empreendedorismo-2` + `educa-o-financeira-para-a-melhor-idade`
- `turma-tds-ia-no-meu-bolso-2026` → `ia-no-meu-bolso-intelig-ncia-artificial-para-o-dia-a-dia-2`
- `turma-tds-sim-e-inspe-o-alimentar-2026` → `sim-servi-o-de-inspe-o-municipal-para-pequenos-produtores-2`

### ✅ Task 3: Fix `<think>` strip no N8N
- Dois Code nodes adicionados no workflow `XYcnRlPZSlfGXOWb`:
  - "Strip Think Tags" → antes de "Responder no Chatwoot"
  - "Strip Think Tags Fallback" → antes de "Responder no Chatwoot Fallback"
- Workflow está **ativo**
- Código dos nodes:
  ```javascript
  const raw = $input.first().json.textResponse || '';
  const clean = raw.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
  return [{ json: { ...($input.first().json), textResponse: clean } }];
  ```

### 🔄 Task 4: Healthchecks dos containers (EM ANDAMENTO)
- `docker/docker-compose.yml` atualizado com healthchecks corretos (wget)
- N8N: `wget -q --spider http://localhost:5678/healthz || exit 1`
- Chatwoot: `wget -q --spider http://localhost:3000/ || exit 1` (Chatwoot usa porta 3000)
- Containers foram recriados manualmente:
  - `kreativ-n8n`: novo container com healthcheck correto (status: `health: starting`)
  - `kreativ-chatwoot`: novo container com healthcheck correto (status: `health: starting`)
- **Aguardar 2-3 minutos e verificar se ficam `(healthy)`**

---

## O que ainda precisa ser feito

### ⏳ Task 4 — Verificar healthchecks (continuar daqui)

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E "n8n|chatwoot"
```
Esperado: `(healthy)` para kreativ-n8n e kreativ-chatwoot.

Se ainda `(unhealthy)`, executar o diagnóstico:
```bash
docker inspect kreativ-chatwoot --format '{{json .State.Health.Log}}' | python3 -m json.tool | tail -20
docker inspect kreativ-n8n --format '{{json .State.Health.Log}}' | python3 -m json.tool | tail -20
```

---

### ⏳ Task 5 — Criar 5 Web Pages institucionais no Frappe LMS

**Esta é a tarefa principal — criar as páginas HTML via Frappe REST API.**

O HTML completo de todas as páginas está no plano em:
`/root/projeto-tds/docs/superpowers/plans/2026-04-09-tds-paginas-institucionais.md`

Leia o plano e escreva o script `/tmp/create_pages.py` com o HTML completo, então execute.

**Resumo das páginas a criar:**

| Rota | Título |
|------|--------|
| `tds-home` | TDS — Inclusão Produtiva no Tocantins |
| `sobre` | Sobre o Programa TDS |
| `guia-aluno` | Guia do Aluno |
| `guia-tutor` | Guia do Tutor |
| `guia-gestor` | Guia do Gestor |

**Todas as páginas devem incluir o Chatwoot widget script:**
```html
<script>
(function(d,t){
  var BASE_URL="https://chat.ipexdesenvolvimento.cloud";
  var g=d.createElement(t),s=d.getElementsByTagName(t)[0];
  g.src=BASE_URL+"/packs/js/sdk.js";
  g.defer=true; g.async=true;
  s.parentNode.insertBefore(g,s);
  g.onload=function(){
    window.chatwootSDK.run({
      websiteToken: 'HwBawyqmiKTAbNzF8yAnzHCD',
      baseUrl: BASE_URL
    })
  }
})(document,"script");
</script>
```

**Verificar se a página já existe antes de criar:**
```bash
curl -s "https://lms.ipexdesenvolvimento.cloud/api/resource/Web%20Page?filters=[[\"route\",\"=\",\"tds-home\"]]&fields=[\"name\",\"route\",\"published\"]" \
  -H "Authorization: token 056681de29fce7a:7c78dcba6e3c5d1" | python3 -m json.tool
```

**Criar uma página via API:**
```bash
curl -s -X POST "https://lms.ipexdesenvolvimento.cloud/api/resource/Web%20Page" \
  -H "Authorization: token 056681de29fce7a:7c78dcba6e3c5d1" \
  -H "Content-Type: application/json" \
  -d '{"doctype":"Web Page","title":"...","route":"tds-home","published":1,"content_type":"HTML","main_section_html":"HTML_AQUI"}'
```

**Se a página já existir, usar PUT para atualizar:**
```bash
curl -s -X PUT "https://lms.ipexdesenvolvimento.cloud/api/resource/Web%20Page/NOME_DA_PAGINA" \
  -H "Authorization: token 056681de29fce7a:7c78dcba6e3c5d1" \
  -H "Content-Type: application/json" \
  -d '{"main_section_html":"HTML_ATUALIZADO"}'
```

**Verificação de cada página:**
```bash
curl -s -o /dev/null -w "%{http_code}" "https://lms.ipexdesenvolvimento.cloud/tds-home"
```
Esperado: 200

---

### ⏳ Task 6 — Configurar home page para tds-home

Após criar as páginas, configurar a home page do Frappe:
```bash
curl -s -X PUT "https://lms.ipexdesenvolvimento.cloud/api/resource/Website%20Settings/Website%20Settings" \
  -H "Authorization: token 056681de29fce7a:7c78dcba6e3c5d1" \
  -H "Content-Type: application/json" \
  -d '{"home_page": "tds-home"}'
```

Verificar: `curl -s -o /dev/null -w "%{http_code}" "https://lms.ipexdesenvolvimento.cloud/"` → deve redirecionar para tds-home.

---

### ⏳ Task 7 — Verificação end-to-end

```bash
# Verificar todas as páginas
for route in tds-home sobre guia-aluno guia-tutor guia-gestor; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://lms.ipexdesenvolvimento.cloud/$route")
  echo "$route: $CODE"
done

# Verificar healthchecks
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E "n8n|chatwoot"

# Verificar 7 cursos keeper publicados
docker exec kreativ-backend bench --site lms.ipexdesenvolvimento.cloud mariadb --execute \
  "SELECT name, published FROM \`tabLMS Course\` WHERE name IN ('agricultura-sustent-vel-sistemas-agroflorestais-2','associativismo-e-cooperativismo-4','audiovisual-e-produ-o-de-conte-do-digital-2','educa-o-financeira-para-a-melhor-idade','finan-as-e-empreendedorismo-2','ia-no-meu-bolso-intelig-ncia-artificial-para-o-dia-a-dia-2','sim-servi-o-de-inspe-o-municipal-para-pequenos-produtores-2');"

# Verificar N8N workflow ativo
N8N_KEY=$(cat /root/kreativ-setup/.env.real 2>/dev/null | grep N8N_API_KEY | cut -d= -f2-)
curl -s "https://n8n.ipexdesenvolvimento.cloud/api/v1/workflows/XYcnRlPZSlfGXOWb" \
  -H "X-N8N-API-KEY: $N8N_KEY" | python3 -c "import sys,json; d=json.load(sys.stdin); print('active:', d.get('active'))"
```

---

## Notas técnicas importantes

1. **Frappe Web Page**: usa `content_type: "HTML"` e `main_section_html` para injetar HTML. O campo `route` define a URL pública.

2. **Chatwoot**: escuta na porta 3000 (não 3005). O container `kreativ-chatwoot` está na rede `kreativ_education_net` e `dokploy-network`.

3. **N8N**: o workflow foi atualizado via API. O strip de `<think>` é feito DENTRO do N8N antes de responder ao Chatwoot — a API RAG ainda retorna think tags, isso é normal.

4. **Container kreativ-n8n**: foi recriado. Se não estiver saudável, checar se o serviço N8N do Dokploy não criou um conflito. Container antigo `16ece849e794_kreativ-n8n` foi removido.

5. **Git hooks**: commits no `/root/projeto-tds` com mudanças em `docker/` trigam sync automático com Dokploy. Para outros arquivos, não triga.

6. **Frappe backend**: o container correto para bench é `kreativ-backend` (não `kreativ-frappe-backend`).
   ```bash
   docker exec kreativ-backend bench --site lms.ipexdesenvolvimento.cloud execute "frappe.db.get_value('Web Page', {'route': 'tds-home'}, 'name')"
   ```

---

## Próxima ação imediata

1. Verificar status dos containers (Task 4)
2. Ler o plano completo em `/root/projeto-tds/docs/superpowers/plans/2026-04-09-tds-paginas-institucionais.md` — Task 5 em diante (offset ~340 no arquivo)
3. Criar o script `/tmp/create_pages.py` com o HTML completo das 5 páginas
4. Executar o script e verificar as URLs
5. Configurar home page (Task 6)
6. Verificação final (Task 7)
