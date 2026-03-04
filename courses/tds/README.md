# Cursos TDS — Kreativ Educação

Cursos reais do projeto TDS (Transformação Digital Solidária).

## Cursos Disponíveis

| # | Curso | Capítulos | Lições |
|---|-------|-----------|--------|
| 1 | Gestão Financeira para Empreendimentos | 2 | 5 |
| 2 | Boas Práticas na Manipulação de Alimentos | 2 | 4 |
| 3 | Organização da Produção para o Mercado | 2 | 3 |

## Uso

```bash
# Criar cursos via API
source .env
python3 scripts/seed-courses.py --dir courses/tds

# Dry-run (ver sem criar)
python3 scripts/seed-courses.py --dir courses/tds --dry-run
```

## Arquivos

- `tds-courses.json` — JSON com os 3 cursos completos e conteúdo das lições
