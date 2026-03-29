#!/bin/bash
# =============================================================================
# install_theme.sh — Instala o kreativ_theme na instância Frappe em execução
# Uso: bash scripts/install_theme.sh
# =============================================================================

SITE="lms.ipexdesenvolvimento.cloud"
CONTAINER="kreativ-frappe-backend"
APP_SRC="/root/projeto-tds/kreativ_theme"

echo "============================================================"
echo "  🎨 Instalando kreativ_theme (Custom App Oficial Frappe)"
echo "============================================================"

# 1. Copiar o app para dentro do container
echo ""
echo "  [1/4] Copiando app para o container..."
docker exec "$CONTAINER" rm -rf /home/frappe/frappe-bench/apps/kreativ_theme
docker cp "$APP_SRC/." "$CONTAINER":/home/frappe/frappe-bench/apps/kreativ_theme
if [ $? -eq 0 ]; then
    echo "  ✅ App copiado"
else
    echo "  ❌ Erro ao copiar. Verifique o caminho."
    exit 1
fi

# 2. Instalar o app no ambiente Python
echo ""
echo "  [2/4] Instalando app no ambiente Python do bench..."
docker exec "$CONTAINER" bash -c "
    /home/frappe/frappe-bench/env/bin/pip install -e /home/frappe/frappe-bench/apps/kreativ_theme --quiet
"
if [ $? -eq 0 ]; then
    echo "  ✅ App instalado no Python env"
else
    echo "  ❌ Falha na instalação pip"
    exit 1
fi

# 3. Copiar os assets CSS para o diretório de assets do site (volume compartilhado)
echo ""
echo "  [3/4] Publicando assets CSS no volume frappe_assets_data..."
docker exec "$CONTAINER" bash -c "
    mkdir -p /home/frappe/frappe-bench/sites/assets/kreativ_theme/css
    cp /home/frappe/frappe-bench/apps/kreativ_theme/kreativ_theme/public/css/lms_theme.css \
       /home/frappe/frappe-bench/sites/assets/kreativ_theme/css/lms_theme.css
    cp /home/frappe/frappe-bench/apps/kreativ_theme/kreativ_theme/public/css/desk_theme.css \
       /home/frappe/frappe-bench/sites/assets/kreativ_theme/css/desk_theme.css
    echo 'Assets copiados:'
    ls -la /home/frappe/frappe-bench/sites/assets/kreativ_theme/css/
"

# 4. Instalar o app no site Frappe e limpar cache
echo ""
echo "  [4/4] Instalando app no site Frappe e limpando cache..."
docker exec "$CONTAINER" bash -c "
    cd /home/frappe/frappe-bench && \
    bench --site $SITE install-app kreativ_theme 2>&1 | tail -5 && \
    bench --site $SITE clear-website-cache && \
    bench --site $SITE clear-cache
"
if [ $? -eq 0 ]; then
    echo "  ✅ App instalado no site!"
else
    echo "  ⚠️  O app pode já estar instalado ou houve aviso. Verificando..."
    docker exec "$CONTAINER" bash -c "bench --site $SITE list-apps" 2>/dev/null
fi

echo ""
echo "============================================================"
echo "  🚀 KREATIV THEME INSTALADO!"
echo ""
echo "  Portal: https://lms.ipexdesenvolvimento.cloud/lms"
echo "  Desk:   https://lms.ipexdesenvolvimento.cloud/app"
echo ""
echo "  → Faça um hard refresh (Ctrl+F5 / Cmd+Shift+R)"
echo "  → O arquivo CSS está em /assets/kreativ_theme/css/lms_theme.css"
echo "============================================================"
