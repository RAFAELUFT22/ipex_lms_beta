#!/usr/bin/env bash
# =============================================================================
# setup.sh — Inicialização completa do Frappe LMS para Kreativ Educação
#
# REQUISITOS:
#   - Docker Engine 24+ com Compose V2
#   - Mínimo 8GB RAM (4GB para o container backend)
#   - .env preenchido (copie de .env.example)
#
# USO:
#   bash scripts/setup.sh
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker/docker-compose.yml"

# ---------------------------------------------------------------------------
# Cores para output
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${BLUE}⏳${NC} $1"; }
ok()   { echo -e "${GREEN}✅${NC} $1"; }
warn() { echo -e "${YELLOW}⚠️${NC}  $1"; }
fail() { echo -e "${RED}❌${NC} $1"; exit 1; }

# ---------------------------------------------------------------------------
# ETAPA 0 — Validar requisitos
# ---------------------------------------------------------------------------
echo ""
echo "============================================="
echo " Kreativ Education — Frappe LMS Setup"
echo "============================================="
echo ""

# Checar .env
if [ ! -f "$PROJECT_DIR/.env" ]; then
  fail "Arquivo .env não encontrado!\n   Copie: cp .env.example .env\n   Edite com suas senhas antes de continuar."
fi

# Carregar .env
set -a
# shellcheck disable=SC1091
source "$PROJECT_DIR/.env"
set +a

SITE_NAME="${FRAPPE_SITE_NAME:-lms.extensionista.site}"
ADMIN_PASS="${FRAPPE_ADMIN_PASSWORD:?'FRAPPE_ADMIN_PASSWORD não definido no .env'}"
DB_ROOT_PASS="${MARIADB_ROOT_PASSWORD:?'MARIADB_ROOT_PASSWORD não definido no .env'}"

# Checar Docker
if ! command -v docker &> /dev/null; then
  fail "Docker não instalado. Instale em https://docs.docker.com/get-docker/"
fi

DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "0")
log "Docker version: $DOCKER_VERSION"

# Checar RAM disponível
TOTAL_RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM_MB" -lt 6000 ]; then
  warn "RAM total: ${TOTAL_RAM_MB}MB — recomendado mínimo 8GB"
  warn "O build do frontend pode falhar por OOM com pouca memória."
  read -rp "   Continuar mesmo assim? (y/N) " -n 1
  echo ""
  [[ $REPLY =~ ^[Yy]$ ]] || exit 1
else
  ok "RAM disponível: ${TOTAL_RAM_MB}MB"
fi

# ---------------------------------------------------------------------------
# ETAPA 1 — Build da imagem Docker
# ---------------------------------------------------------------------------
log "[1/6] Construindo imagem Docker kreativ_frappe_lms..."
docker build -t kreativ_frappe_lms:latest "$PROJECT_DIR/docker/"
ok "Imagem construída!"
echo ""

# ---------------------------------------------------------------------------
# ETAPA 2 — Subir infra base (MariaDB + Redis)
# ---------------------------------------------------------------------------
log "[2/6] Subindo MariaDB e Redis..."
docker compose -f "$COMPOSE_FILE" \
  up -d frappe_mariadb frappe_redis_queue frappe_redis_socketio

log "Aguardando MariaDB ficar saudável (até 90s)..."
TIMEOUT=90
COUNT=0
until docker exec kreativ_frappe_mariadb healthcheck.sh --connect --innodb_initialized 2>/dev/null; do
  sleep 3
  COUNT=$((COUNT + 3))
  if [ $COUNT -ge $TIMEOUT ]; then
    fail "MariaDB não iniciou em ${TIMEOUT}s.\n   Verifique: docker logs kreativ_frappe_mariadb"
  fi
  echo "   Aguardando... (${COUNT}s/${TIMEOUT}s)"
done
ok "MariaDB pronto!"
echo ""

# ---------------------------------------------------------------------------
# ETAPA 3 — Subir backend + configurador
# ---------------------------------------------------------------------------
log "[3/6] Subindo backend e configurador..."
docker compose -f "$COMPOSE_FILE" up -d frappe_configurator frappe_backend
sleep 10

# Corrigir permissões
docker exec -u root kreativ_frappe_backend \
  chown -R frappe:frappe /home/frappe/frappe-bench/sites 2>/dev/null || true
ok "Backend iniciado!"
echo ""

# ---------------------------------------------------------------------------
# ETAPA 4 — Criar site e instalar LMS
# ---------------------------------------------------------------------------
log "[4/6] Criando site Frappe: $SITE_NAME"
log "   (Este processo leva 2-5 minutos na primeira execução)"

docker exec -w /home/frappe/frappe-bench/sites kreativ_frappe_backend bash -c \
  "ls -1 ../apps > apps.txt && bench new-site \
    --force \
    --db-host kreativ_frappe_mariadb \
    --db-root-password '$DB_ROOT_PASS' \
    --admin-password '$ADMIN_PASS' \
    --no-mariadb-socket \
    '$SITE_NAME'" || {
      warn "Site pode já existir. Continuando..."
    }

log "Instalando app LMS..."
docker exec -w /home/frappe/frappe-bench/sites kreativ_frappe_backend bash -c \
  "bench --site '$SITE_NAME' install-app lms" || {
      warn "App LMS pode já estar instalado. Continuando..."
    }

ok "Site + LMS instalados!"
echo ""

# ---------------------------------------------------------------------------
# ETAPA 5 — Build do frontend
# ---------------------------------------------------------------------------
log "[5/6] Compilando frontend LMS (vite build — pode levar 1-2 min)..."

# O backend precisa de pelo menos 4GB para o build
CURRENT_MEM=$(docker inspect kreativ_frappe_backend --format '{{.HostConfig.Memory}}' 2>/dev/null || echo "0")
if [ "$CURRENT_MEM" -lt 4000000000 ]; then
  log "   Aumentando memória do container temporariamente para 4GB..."
  docker update --memory 4g --memory-swap 6g kreativ_frappe_backend 2>/dev/null || true
fi

docker exec kreativ_frappe_backend bench build --app lms || {
  fail "Build do frontend falhou!\n   Possível OOM — veja docs/TROUBLESHOOTING.md"
}

ok "Frontend compilado!"
echo ""

# ---------------------------------------------------------------------------
# ETAPA 6 — Configurar e subir todos os serviços
# ---------------------------------------------------------------------------
log "[6/6] Configurando CORS, scheduler e subindo stack completo..."

docker exec -w /home/frappe/frappe-bench kreativ_frappe_backend bash -c \
  "bench --site $SITE_NAME set-config allow_cors 1 && \
   bench --site $SITE_NAME set-config cors_origin '*' && \
   bench --site $SITE_NAME enable-scheduler && \
   bench --site $SITE_NAME set-maintenance-mode off"

docker compose -f "$COMPOSE_FILE" up -d
ok "Todos os serviços ativos!"

# ---------------------------------------------------------------------------
# RESULTADO FINAL
# ---------------------------------------------------------------------------
echo ""
echo "============================================="
echo -e " ${GREEN}✅ Setup Frappe LMS CONCLUÍDO!${NC}"
echo "============================================="
echo ""
echo " 🌐 Portal:  https://$SITE_NAME"
echo " 👤 Admin:   Administrator"
echo " 🔑 Senha:   (definida no .env)"
echo ""
echo " 📋 PRÓXIMOS PASSOS:"
echo ""
echo "   1. Acesse https://$SITE_NAME e faça login"
echo ""
echo "   2. Gere API Key para integração N8N:"
echo "      → Menu Superior > Usuário > API Access > Gerar Chaves"
echo "      → Copie API Key + API Secret para o .env"
echo ""
echo "   3. Crie cursos (via UI ou API):"
echo "      → Veja docs/COURSE_CREATION_API.md"
echo ""
echo "   4. Teste o LMS:"
echo "      bash scripts/health-check.sh"
echo ""
echo "============================================="
