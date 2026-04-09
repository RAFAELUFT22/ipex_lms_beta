# Coding Conventions — Territórios de Desenvolvimento Social e Inclusão Produtiva

## Python
- Python 3.11+
- Use `requests` para chamadas HTTP ao Frappe
- Auth header: `"Authorization": f"token {KEY}:{SECRET}"`
- Use `python-dotenv` para carregar `.env`
- Docstrings em português

## Bash
- `set -euo pipefail` no topo
- Output colorido com `echo -e`
- Logging: ✅ ok, ❌ fail, ⏳ progress, ⚠️ warning

## API Frappe
- URL encode DocTypes com espaço: `LMS Course` → `LMS%20Course`
- Filtros: `[["campo","operador","valor"]]` como JSON string
- Child tables: arrays dentro do JSON pai
- Sempre enviar `Content-Type: application/json`

## Docker
- Containers prefixados com `kreativ_frappe_`
- Rede interna: `kreativ_education_net`
- Usar `deploy.resources.limits.memory` para todos os serviços

## Git
- Commits em inglês, prefixados: `feat:`, `fix:`, `docs:`, `chore:`
- Branch principal: `main`
- Nunca commitar `.env`, chaves, ou senhas
