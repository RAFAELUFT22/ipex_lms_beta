#!/usr/bin/env bash
# query_openclaw.sh - Query the Qwen2.5-Coder model on the remote Ollama instance.
# Usage: ./query_openclaw.sh "Your prompt here"

set -euo pipefail

PROMPT="$1"
OLLAMA_URL="http://46.202.150.132:11434"
MODEL="qwen2.5-coder:7b"

# Inject TDS context
SYSTEM_CONTEXT="Você é o especialista Antigravity para o projeto Territórios de Desenvolvimento Social e Inclusão Produtiva. 
Regra: Tudo via Dokploy Panel/API. Evitar hardcoded root.
Frappe LMS version: latest.
Language: pt-BR."

# Escape quotes for JSON
ESCAPED_PROMPT=$(echo "$PROMPT" | sed 's/"/\\"/g')
ESCAPED_CONTEXT=$(echo "$SYSTEM_CONTEXT" | sed 's/"/\\"/g' | awk '{printf "%s\\n", $0}' | tr -d '\r')

DATA=$(cat <<EOF
{
  "model": "$MODEL",
  "prompt": "$ESCAPED_CONTEXT\n\nPergunta: $ESCAPED_PROMPT",
  "stream": false
}
EOF
)

RESPONSE=$(curl -s "$OLLAMA_URL/api/generate" -d "$DATA" | jq -r '.response')

echo "$RESPONSE"
