#!/bin/bash
# Injeta o arquivo de tradução no container Frappe LMS

CONTAINER_NAME="kreativ-frappe-backend"
TRANSLATION_DIR="/home/frappe/frappe-bench/apps/lms/lms/translations"
SOURCE_FILE="pt-BR.csv"

if [ ! -f "$SOURCE_FILE" ]; then
    echo "❌ Arquivo $SOURCE_FILE não encontrado!"
    exit 1
fi

echo "🚀 Injetando tradução no container $CONTAINER_NAME..."
docker exec -u root "$CONTAINER_NAME" mkdir -p "$TRANSLATION_DIR"
docker cp "$SOURCE_FILE" "$CONTAINER_NAME:$TRANSLATION_DIR/pt-BR.csv"
docker exec -u root "$CONTAINER_NAME" chown frappe:frappe "$TRANSLATION_DIR/pt-BR.csv"

echo "🧹 Limpando cache e reiniciando bench..."
docker exec "$CONTAINER_NAME" bench --site lms.ipexdesenvolvimento.cloud clear-cache
# Nota: O restart pode demorar alguns segundos
docker exec "$CONTAINER_NAME" bench restart

echo "✅ Tradução aplicada com sucesso!"
