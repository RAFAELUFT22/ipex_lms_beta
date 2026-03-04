# Troubleshooting — Kreativ Education

## 1. `bench build` falha com exit code 137 ou 134

**Causa**: OOM — vite precisa de ~2GB heap para compilar 3885 módulos.

**Solução**:
```bash
docker update --memory 4g --memory-swap 6g kreativ_frappe_backend
docker exec kreativ_frappe_backend bench build --app lms
```

---

## 2. `/lms` retorna 404

**Causa**: Frontend não foi compilado — assets JS não existem.

**Diagnóstico**:
```bash
docker exec kreativ_frappe_backend ls sites/assets/lms/frontend/
# Se não tiver index.html e assets/, precisa rebuild
```

**Solução**:
```bash
docker exec kreativ_frappe_backend bench build --app lms
```

---

## 3. CORS bloqueando requests da IA/N8N

**Solução**:
```bash
docker exec kreativ_frappe_backend bash -c \
  "bench --site SITE set-config allow_cors 1 && \
   bench --site SITE set-config cors_origin '*'"
```

---

## 4. API retorna "Method Not Allowed"

**Causa**: Função não está whitelisted ou endpoint incorreto.

**Verificação**:
```bash
# Endpoint correto para CRUD:
curl .../api/resource/LMS%20Course  # ✅
curl .../api/resource/LMS Course    # ❌ espaço sem encode
```

---

## 5. MariaDB não inicia

**Causa comum**: permissões do volume.

```bash
docker exec -u root kreativ_frappe_mariadb chown -R mysql:mysql /var/lib/mysql
docker restart kreativ_frappe_mariadb
```

---

## 6. "Site not found" ao acessar

**Causa**: site não é o default.

```bash
docker exec kreativ_frappe_backend bench use SITE_NAME
```

---

## 7. Scheduler não roda jobs

```bash
docker exec kreativ_frappe_backend bench --site SITE enable-scheduler
docker restart kreativ_frappe_scheduler
```

---

## 8. Aluno não consegue logar

**Verificar** se o User existe e tem role "LMS Student":
```bash
curl ".../api/resource/User/email@example.com" -H "Authorization: token KEY:SECRET"
```

---

## Logs Úteis

```bash
# Backend logs
docker logs kreativ_frappe_backend --tail 50

# Worker errors
docker logs kreativ_frappe_queue_short --tail 50

# MariaDB slow queries
docker exec kreativ_frappe_mariadb mysqladmin processlist -p

# Frappe error log
docker exec kreativ_frappe_backend cat sites/SITE/logs/frappe.log | tail -30
```
