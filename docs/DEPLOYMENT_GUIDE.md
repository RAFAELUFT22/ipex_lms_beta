# Deployment Guide — Territórios de Desenvolvimento Social e Inclusão Produtiva

> Passo a passo para deploy do Frappe LMS em uma VPS nova.

---

## Pré-requisitos

| Requisito | Mínimo | Recomendado |
|-----------|--------|-------------|
| CPU | 2 vCPU | 4 vCPU |
| RAM | 8 GB | 16 GB |
| SSD | 50 GB | 80 GB |
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| Docker | 24.0+ | Latest |
| Docker Compose | V2 (plugin) | Latest |

---

## Etapa 1 — Preparar a VPS

```bash
# Atualizar pacotes
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Verificar
docker --version
docker compose version
```

---

## Etapa 2 — Clonar o repositório

```bash
git clone https://github.com/RAFAELUFT22/kreativ-education.git
cd kreativ-education
```

---

## Etapa 3 — Configurar variáveis

```bash
cp .env.example .env
nano .env  # Preencha todas as senhas
```

**Variáveis obrigatórias:**
- `MARIADB_ROOT_PASSWORD` — senha root do MariaDB
- `MARIADB_FRAPPE_PASSWORD` — senha do usuário frappe
- `FRAPPE_ADMIN_PASSWORD` — senha do Administrator

---

## Etapa 4 — Build e Setup

```bash
# Tornar scripts executáveis
chmod +x scripts/*.sh

# Executar setup completo (10-15 min na primeira vez)
bash scripts/setup.sh
```

O script irá:
1. ✅ Validar requisitos (RAM, Docker)
2. ✅ Construir a imagem Docker
3. ✅ Iniciar MariaDB + Redis
4. ✅ Criar site Frappe + instalar LMS
5. ✅ Compilar frontend (com proteção OOM)
6. ✅ Configurar CORS e subir todos os serviços

---

## Etapa 5 — Gerar API Keys

1. Acesse `https://lms.SEU-DOMINIO.com`
2. Login: `Administrator` / `{FRAPPE_ADMIN_PASSWORD}`
3. Menu Superior → **Settings** → **My Settings**
4. Seção **API Access** → **Generate Keys**
5. Copie `API Key` e `API Secret` para o `.env`

---

## Etapa 6 — Seed de cursos

```bash
source .env
python3 scripts/seed-courses.py --dir courses/tds
```

---

## Etapa 7 — Health check

```bash
bash scripts/health-check.sh
```

Todos os 9 serviços devem estar ✅.

---

## Etapa 8 — Configurar DNS

Aponte `lms.SEU-DOMINIO.com` (A record) para o IP da VPS.
O Traefik gerará certificados SSL automaticamente via Let's Encrypt.

---

## Manutenção

```bash
# Parar tudo
docker compose -f docker/docker-compose.yml down

# Atualizar Frappe/LMS
docker exec kreativ_frappe_backend bash -c \
  "cd apps/lms && git pull && cd ../.. && bench migrate"

# Rebuild frontend após atualização
docker exec kreativ_frappe_backend bench build --app lms

# Backup
docker exec kreativ_frappe_backend bench backup --with-files
```
