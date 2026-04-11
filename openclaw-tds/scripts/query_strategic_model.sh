#!/usr/bin/env bash
# query_strategic_model.sh - Query strategic models on OpenRouter (e.g. Claude 3.5 Sonnet)
# Usage: ./query_strategic_model.sh "Your prompt here" [model_id]

set -euo pipefail

PROMPT="${1:-}"
MODEL="${2:-anthropic/claude-3.7-sonnet}" # Default strategic model

if [[ -z "$PROMPT" ]]; then
    echo "Usage: $0 \"Your prompt here\" [model_id]"
    exit 1
fi

SETTINGS_FILE="/root/projeto-tds/settings.json"

# Extract API Key from settings.json
if [[ -f "$SETTINGS_FILE" ]]; then
    OPENROUTER_KEY=$(jq -r '.openrouter_key' "$SETTINGS_FILE")
else
    echo "[-] settings.json not found."
    exit 1
fi

if [[ -z "$OPENROUTER_KEY" || "$OPENROUTER_KEY" == "null" ]]; then
    echo "[-] OpenRouter Key is missing in settings.json."
    exit 1
fi

# Inject TDS context (Same as OpenClaw context to maintain alignment)
SYSTEM_CONTEXT="Você é o Cérebro Estratégico Antigravity para o projeto TDS (Territórios de Desenvolvimento Social).
Sua missão: Resolver problemas complexos de arquitetura, implantação e testes.
Regra de Ouro: Todas as operações críticas devem ser via Dokploy Panel/API. 
Evite sugestões de acesso root direto ou comandos docker manuais no host.
Tecnologias: Frappe LMS, Supabase, Chatwoot, Evolution API, n8n.
Idioma: Português (pt-BR)."

# Prepare JSON via jq for safety
JSON_PAYLOAD=$(jq -n \
    --arg model "$MODEL" \
    --arg role "system" \
    --arg content "$SYSTEM_CONTEXT" \
    --arg user_role "user" \
    --arg user_content "Pergunta: $PROMPT" \
    '{
        model: $model,
        messages: [
            {role: $role, content: $content},
            {role: $user_role, content: $user_content}
        ]
    }')

echo "[*] Consulting Strategic Model: $MODEL..."

RESPONSE=$(curl -s "https://openrouter.ai/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENROUTER_KEY" \
  -d "$JSON_PAYLOAD")

# Check for errors in response
ERROR=$(echo "$RESPONSE" | jq -r '.error.message // empty')
if [[ -n "$ERROR" ]]; then
    echo "[-] OpenRouter Error: $ERROR"
    exit 1
fi

echo "$RESPONSE" | jq -r '.choices[0].message.content'
