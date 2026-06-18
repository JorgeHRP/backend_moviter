"""
Cria a tabela brands no Supabase e faz seed das marcas iniciais.
Uso: python scripts/create_brands_table.py
"""
import os
import sys
import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

HEADERS = {
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "apikey": SERVICE_ROLE_KEY,
    "Content-Type": "application/json",
}

PG_META_ENDPOINTS = [
    f"{SUPABASE_URL}/pg/query",
    f"{SUPABASE_URL}/meta/query",
]

SQL = """
CREATE TABLE IF NOT EXISTS brands (
    id          SERIAL PRIMARY KEY,
    brand_name  TEXT UNIQUE NOT NULL,
    provider    TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
"""

# Marcas iniciais — adiciona mais diretamente no Supabase Studio
INITIAL_BRANDS = [
    {"brand_name": "HITACHI",      "provider": "hitachi"},
    {"brand_name": "HAMM",         "provider": "trackunit"},
    {"brand_name": "VOGELE",       "provider": "trackunit"},
    {"brand_name": "WIRTGEN",      "provider": "trackunit"},
    {"brand_name": "GEHL",         "provider": "trackunit"},
    {"brand_name": "JOHN DEERE",   "provider": "johndeere"},
    {"brand_name": "JOHN DEERE F", "provider": "johndeere"},
]


def run_sql(sql: str) -> bool:
    for endpoint in PG_META_ENDPOINTS:
        try:
            resp = httpx.post(
                endpoint,
                json={"query": sql},
                headers=HEADERS,
                timeout=30,
                follow_redirects=True,
            )
            if resp.status_code in (200, 201):
                print(f"[OK] via {endpoint}")
                return True
            print(f"  [{resp.status_code}] {endpoint}: {resp.text[:200]}")
        except httpx.RequestError as exc:
            print(f"  Erro a ligar a {endpoint}: {exc}")
    return False


def seed_brands():
    resp = httpx.post(
        f"{SUPABASE_URL}/rest/v1/brands",
        json=INITIAL_BRANDS,
        headers={
            **HEADERS,
            "Prefer": "resolution=ignore-duplicates,return=minimal",
        },
        timeout=30,
    )
    if resp.status_code not in (200, 201):
        print(f"  [AVISO] Seed retornou {resp.status_code}: {resp.text[:200]}")
    else:
        print(f"  {len(INITIAL_BRANDS)} marcas inseridas (duplicadas ignoradas).")


def main():
    if not SUPABASE_URL:
        sys.exit("[ERRO] SUPABASE_URL não definida no .env")
    if not SERVICE_ROLE_KEY:
        sys.exit("[ERRO] SUPABASE_SERVICE_ROLE_KEY não definida no .env")

    print(f"A criar tabela brands em {SUPABASE_URL} ...")
    if not run_sql(SQL):
        print("\n[ERRO] Não foi possível criar a tabela via API.")
        print("  -> Abre o Supabase Studio e corre este SQL manualmente:")
        print(SQL)
        sys.exit(1)

    print("A inserir marcas iniciais...")
    seed_brands()
    print("\n[OK] Tabela brands pronta.")


if __name__ == "__main__":
    main()
