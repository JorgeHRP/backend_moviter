"""
Script de seed — importa o CSV de máquinas para o Supabase.
Uso: python scripts/seed_machines.py
"""
import csv
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from app.db.supabase import get_supabase

CSV_PATH = os.path.join(os.path.dirname(__file__), "../data/rocim_machines.csv")


def parse_row(row: dict) -> dict:
    def clean(v):
        if v in (None, "NULL", "null", ""):
            return None
        if isinstance(v, str):
            v = v.encode("latin-1", errors="replace").decode("utf-8", errors="replace")
        return v

    return {
        "id":           int(row["id"]),
        "chassis":      clean(row["chassis"]),
        "num_maquina":  clean(row["num_maquina"]),
        "designacao":   clean(row["designacao"]),
        "cod_cliente":  clean(row["cod_cliente"]),
        "nome_cliente": clean(row["nome_cliente"]),
        "localidade":   clean(row["localidade"]),
        "marca":        clean(row["marca"]),
        "familia":      clean(row["familia"]),
        "cod_marca":    clean(row["cod_marca"]),
        "cod_modelo":   clean(row["cod_modelo"]),
        "modelo":       clean(row["modelo"]),
        "email":        clean(row["email"]),
        "telefone1":    clean(row["telefone1"]),
        "synced_at":    clean(row["synced_at"]),
        "raw_json":     clean(row["raw_json"]),
    }


def main():
    db = get_supabase()
    rows = []

    with open(CSV_PATH, encoding="latin-1") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            try:
                rows.append(parse_row(row))
            except Exception as e:
                print(f"Erro na linha {row.get('id')}: {e}")

    print(f"A importar {len(rows)} máquinas...")

    # Upsert em lotes de 50
    batch_size = 50
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        resp = db.table("machines").upsert(batch).execute()
        print(f"  Lote {i // batch_size + 1}: {len(batch)} registos")

    print("[OK] Seed concluido.")


if __name__ == "__main__":
    main()
