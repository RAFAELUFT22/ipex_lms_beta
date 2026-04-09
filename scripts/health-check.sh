#!/usr/bin/env bash
# =============================================================================
# health-check.sh — Validar que todos os serviços Frappe LMS estão operacionais
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

set -a
# shellcheck disable=SC1091
source "$PROJECT_DIR/.env" 2>/dev/null || true
set +a

SITE="${FRAPPE_SITE_NAME:-lms.extensionista.site}"
URL="${FRAPPE_LMS_URL:-https://$SITE}"
PASS=0
FAIL=0

check() {
  local name="$1"
  local result="$2"
  if [ "$result" = "OK" ]; then
    echo "  ✅ $name"
    PASS=$((PASS + 1))
  else
    echo "  ❌ $name — $result"
    FAIL=$((FAIL + 1))
  fi
}

echo ""
echo "============================================="
echo " Territórios de Desenvolvimento Social e Inclusão Produtiva — Health Check"
echo " URL: $URL"
echo "============================================="
echo ""

# 1. Containers rodando
echo "📦 Containers:"
for svc in kreativ_frappe_backend kreativ_frappe_frontend kreativ_frappe_mariadb \
           kreativ_frappe_socketio kreativ_frappe_scheduler \
           kreativ_frappe_queue_short kreativ_frappe_queue_long \
           kreativ_frappe_redis_queue kreativ_frappe_redis_socketio; do
  STATUS=$(docker inspect -f '{{.State.Status}}' "$svc" 2>/dev/null || echo "not_found")
  if [ "$STATUS" = "running" ]; then
    check "$svc" "OK"
  else
    check "$svc" "Status: $STATUS"
  fi
done

echo ""
echo "🌐 HTTP Endpoints:"

# 2. Homepage
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL" --max-time 10 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
  check "Homepage ($URL)" "OK"
else
  check "Homepage ($URL)" "HTTP $HTTP_CODE"
fi

# 3. /lms route
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/lms" --max-time 10 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
  check "/lms Portal" "OK"
else
  check "/lms Portal" "HTTP $HTTP_CODE"
fi

# 4. API ping
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/api/method/ping" --max-time 10 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
  check "API /api/method/ping" "OK"
else
  check "API /api/method/ping" "HTTP $HTTP_CODE"
fi

# 5. Apps instaladas
echo ""
echo "📱 Apps instaladas:"
docker exec kreativ_frappe_backend bench --site all list-apps 2>/dev/null || echo "  ❌ Não foi possível listar"

# 6. Resultados
echo ""
echo "============================================="
echo " Resultado: $PASS OK, $FAIL falhas"
if [ $FAIL -eq 0 ]; then
  echo " 🎉 Todos os testes passaram!"
else
  echo " ⚠️  Verifique os serviços com falha acima"
fi
echo "============================================="
