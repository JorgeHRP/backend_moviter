"""
Cria as tabelas no Supabase executando o SQL via pg-meta API.
Uso: python scripts/create_tables.py
"""
import os
import sys
import httpx
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

SQL_PATH = Path(__file__).parent / "create_tables.sql"

HEADERS = {
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "apikey": SERVICE_ROLE_KEY,
    "Content-Type": "application/json",
}

# Endpoints pg-meta expostos pelo Kong em instâncias self-hosted
PG_META_ENDPOINTS = [
    f"{SUPABASE_URL}/pg/query",
    f"{SUPABASE_URL}/meta/query",
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
                print(f"[OK] Tabelas criadas via {endpoint}")
                return True
            print(f"  [{resp.status_code}] {endpoint}: {resp.text[:200]}")
        except httpx.RequestError as exc:
            print(f"  Erro a ligar a {endpoint}: {exc}")
    return False


def main():
    if not SUPABASE_URL:
        sys.exit("[ERRO] SUPABASE_URL nao definida no .env")
    if not SERVICE_ROLE_KEY:
        sys.exit("[ERRO] SUPABASE_SERVICE_ROLE_KEY nao definida no .env")

    sql = SQL_PATH.read_text(encoding="utf-8")
    print(f"A executar SQL em {SUPABASE_URL} ...")

    if not run_sql(sql):
        print("\n[ERRO] Nenhum endpoint respondeu com sucesso.")
        print("   -> Abre o Supabase Studio em " + SUPABASE_URL)
        print("   -> Vai a SQL Editor e cola o conteudo de scripts/create_tables.sql")
        sys.exit(1)


if __name__ == "__main__":
    main()
