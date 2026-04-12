#!/usr/bin/env python3
"""
Importa alunos TDS de planilha CSV para a lms_lite_api.

Formato CSV esperado (com cabeçalho):
  telefone,nome,municipio,curso_slug,nis

Uso:
  python3 import_students_csv.py alunos_sisec.csv
  python3 import_students_csv.py alunos_sisec.csv --dry-run
  python3 import_students_csv.py alunos_sisec.csv --api-url https://api-lms.ipexdesenvolvimento.cloud
"""
import csv
import sys
import time
import argparse
import requests
from pathlib import Path

API_URL = "https://api-lms.ipexdesenvolvimento.cloud"
ADMIN_KEY = "admin-tds-2026"
THROTTLE_SECONDS = 0.1  # 10 req/s


def import_students(csv_path: str, api_url: str, dry_run: bool) -> int:
    path = Path(csv_path)
    if not path.exists():
        print(f"[ERR] Arquivo não encontrado: {csv_path}")
        return 1

    errors = []
    ok = skip = err = 0

    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    prefix = "[DRY-RUN] " if dry_run else ""
    print(f"{prefix}Importando {len(rows)} alunos de {csv_path}...")

    for i, row in enumerate(rows, 1):
        phone = row.get("telefone", "").strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        name = row.get("nome", "").strip()
        municipality = row.get("municipio", "").strip()
        course = row.get("curso_slug", "").strip()
        nis = row.get("nis", "").strip()

        if not phone or not name:
            print(f"[SKIP] Linha {i}: telefone ou nome vazio — {row}")
            skip += 1
            continue

        if not phone.startswith("55"):
            phone = "55" + phone

        if dry_run:
            print(f"[DRY]  {i}/{len(rows)} {name} ({phone}) → {course or 'sem curso'}")
            ok += 1
            continue

        try:
            resp = requests.post(
                f"{api_url}/student",
                json={"whatsapp": phone, "name": name, "municipality": municipality,
                      "course": course, "nis": nis},
                headers={"X-Admin-Key": ADMIN_KEY},
                timeout=15,
            )
            if resp.status_code in (200, 201):
                print(f"[OK]   {i}/{len(rows)} {name} ({phone})")
                ok += 1
            elif resp.status_code == 409:
                print(f"[SKIP] {i}/{len(rows)} {name} ({phone}) — já existe")
                skip += 1
            else:
                msg = resp.text[:120]
                print(f"[ERR]  {i}/{len(rows)} {name} ({phone}) — HTTP {resp.status_code}: {msg}")
                errors.append({**row, "_http_status": resp.status_code, "_error": msg})
                err += 1
        except Exception as e:
            print(f"[ERR]  {i}/{len(rows)} {name} ({phone}) — {e}")
            errors.append({**row, "_http_status": "exception", "_error": str(e)})
            err += 1

        time.sleep(THROTTLE_SECONDS)

    print(f"\n{'='*52}")
    print(f"Resultado: {ok} OK  |  {skip} SKIP  |  {err} ERRO  de {len(rows)} total")

    if errors:
        err_path = path.stem + "_errors.csv"
        fieldnames = list(errors[0].keys())
        with open(err_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(errors)
        print(f"Falhas salvas em: {err_path} — reprocesse com: python3 {sys.argv[0]} {err_path}")

    success_rate = ok / max(len(rows), 1)
    return 0 if success_rate >= 0.95 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importa alunos TDS de CSV para lms_lite_api")
    parser.add_argument("csv_file", help="Caminho para o arquivo CSV")
    parser.add_argument("--api-url", default=API_URL, help="URL base da API (padrão: produção)")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem enviar requisições")
    args = parser.parse_args()
    sys.exit(import_students(args.csv_file, args.api_url, args.dry_run))
