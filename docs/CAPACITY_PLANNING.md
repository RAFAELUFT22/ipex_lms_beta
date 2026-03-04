# Capacity Planning — Kreativ Education

## Requisitos de RAM por Serviço

| Serviço | RAM Mínima | RAM Configurada | Notas |
|---------|-----------|-----------------|-------|
| `frappe_backend` | 2 GB | **4 GB** | ⚠️ Precisa de 4GB para `bench build` (vite compila 3885 módulos) |
| `frappe_mariadb` | 256 MB | 512 MB | InnoDB buffer pool = 256MB |
| `frappe_frontend` | 128 MB | 512 MB | Nginx servindo assets estáticos |
| `frappe_queue_short` | 128 MB | 256 MB | Worker para jobs rápidos |
| `frappe_queue_long` | 128 MB | 256 MB | Worker para jobs longos |
| `frappe_scheduler` | 64 MB | 128 MB | Cron interno |
| `frappe_socketio` | 64 MB | 128 MB | WebSocket real-time |
| `frappe_redis_queue` | 32 MB | 64 MB | Filas de trabalho |
| `frappe_redis_socketio` | 32 MB | 64 MB | Pub/sub WebSocket |
| **TOTAL** | **~2.8 GB** | **~5.9 GB** | |

## Recomendação por Escala

| Escala | Alunos | VPS | RAM | vCPU | SSD |
|--------|--------|-----|-----|------|-----|
| **Piloto** | até 100 | Mínima | 8 GB | 2 | 50 GB |
| **Produção** | 100-500 | Média | 16 GB | 4 | 80 GB |
| **Escala** | 500+ | Grande | 32 GB | 8 | 160 GB |

## ⚠️ Nota Crítica sobre OOM

O `bench build --app lms` executa `vite build` que compila **3885 módulos Vue**. Este processo usa até **2GB de heap JavaScript** além da memória base do container.

Se o container backend tiver menos de 4GB:
- **Exit code 137** → OOM kill pelo kernel
- **Exit code 134** → JS heap out of memory

**Solução permanente**: configurar `memory: 4G` no docker-compose.

**Solução temporária** (se RAM limitada):
```bash
docker update --memory 4g kreativ_frappe_backend
bench build --app lms
docker update --memory 2g kreativ_frappe_backend  # restaurar
```
