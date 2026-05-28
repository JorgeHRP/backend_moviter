"""
Setup completo da base de dados para demo/apresentacao.
Apaga tudo e recria do zero com dados fixos do CSV.

Uso: python scripts/setup_db.py
"""
import csv
import os
import sys
import httpx
import bcrypt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

URL = os.getenv("SUPABASE_URL", "").rstrip("/")
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
CSV_PATH = Path(__file__).parent.parent / "data" / "rocim_machines.csv"

HEADERS = {
    "Authorization": f"Bearer {KEY}",
    "apikey": KEY,
    "Content-Type": "application/json",
}


def sql(query: str, label: str = ""):
    resp = httpx.post(f"{URL}/pg/query", json={"query": query}, headers=HEADERS, timeout=30)
    if resp.status_code not in (200, 201):
        print(f"[ERRO] {label}: {resp.text[:300]}")
        sys.exit(1)
    if label:
        print(f"  [OK] {label}")


def rest_upsert(table: str, rows: list[dict], label: str = ""):
    h = {**HEADERS, "Prefer": "resolution=merge-duplicates"}
    resp = httpx.post(f"{URL}/rest/v1/{table}", json=rows, headers=h, timeout=30)
    if resp.status_code not in (200, 201):
        print(f"[ERRO] {label}: {resp.text[:300]}")
        sys.exit(1)
    if label:
        print(f"  [OK] {label} ({len(rows)} registos)")


# ── 1. Apagar tabelas existentes ──────────────────────────────────────────────

print("\n[1/4] A apagar tabelas existentes...")
sql("DROP TABLE IF EXISTS user_machines;",   "drop user_machines")
sql("DROP TABLE IF EXISTS refresh_tokens;",  "drop refresh_tokens")
sql("DROP TABLE IF EXISTS users;",           "drop users")
sql("DROP TABLE IF EXISTS machines;",        "drop machines")


# ── 2. Criar tabelas novas ────────────────────────────────────────────────────

print("\n[2/4] A criar tabelas...")

sql("""
CREATE TABLE machines (
    id          INTEGER PRIMARY KEY,
    num_maquina TEXT UNIQUE NOT NULL,
    chassis     TEXT,
    designacao  TEXT,
    cod_cliente TEXT NOT NULL,
    nome_cliente TEXT,
    localidade  TEXT,
    marca       TEXT,
    familia     TEXT,
    cod_marca   TEXT,
    cod_modelo  TEXT,
    modelo      TEXT,
    email       TEXT,
    telefone1   TEXT,
    created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_machines_cod_cliente ON machines(cod_cliente);
CREATE INDEX idx_machines_chassis     ON machines(chassis);
""", "tabela machines")

sql("""
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name        TEXT,
    cod_cliente TEXT UNIQUE NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);
""", "tabela users")

sql("""
CREATE TABLE user_machines (
    user_id     UUID NOT NULL,
    num_maquina TEXT NOT NULL,
    PRIMARY KEY (user_id, num_maquina)
);
CREATE INDEX idx_um_user_id     ON user_machines(user_id);
CREATE INDEX idx_um_num_maquina ON user_machines(num_maquina);
""", "tabela user_machines")


# ── 3. Seed machines ──────────────────────────────────────────────────────────

print("\n[3/4] A importar maquinas do CSV...")

def clean(v):
    if v in (None, "NULL", "null", ""):
        return None
    if isinstance(v, str):
        try:
            v = v.encode("latin-1").decode("utf-8")
        except Exception:
            pass
    return v

machines_rows = []
with open(CSV_PATH, encoding="latin-1") as f:
    for row in csv.DictReader(f, delimiter=";"):
        machines_rows.append({
            "id":           int(row["id"]),
            "num_maquina":  clean(row["num_maquina"]),
            "chassis":      clean(row["chassis"]),
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
        })

# Upsert em lotes de 50
for i in range(0, len(machines_rows), 50):
    batch = machines_rows[i:i+50]
    rest_upsert("machines", batch, f"machines lote {i//50+1}")


# ── 4. Seed users + user_machines ─────────────────────────────────────────────

print("\n[4/4] A criar utilizadores e mapeamentos...")

# Agrupa maquinas por cliente
from collections import defaultdict
machines_by_client: dict[str, list[str]] = defaultdict(list)
for m in machines_rows:
    machines_by_client[m["cod_cliente"]].append(m["num_maquina"])

# Clientes unicos (email, nome, cod_cliente)
clients_seen: dict[str, dict] = {}
for m in machines_rows:
    cod = m["cod_cliente"]
    if cod and cod not in clients_seen:
        clients_seen[cod] = {
            "nome":  m["nome_cliente"],
            "email": m["email"],
        }

# Inserir users um a um para obter o UUID gerado
for cod, info in clients_seen.items():
    email = info["email"] or f"{cod}@moviter.pt"
    name  = info["nome"] or cod
    pw_hash = bcrypt.hashpw(cod.encode(), bcrypt.gensalt()).decode()

    h = {**HEADERS, "Prefer": "return=representation"}
    resp = httpx.post(
        f"{URL}/rest/v1/users",
        json={"email": email, "password_hash": pw_hash, "name": name, "cod_cliente": cod},
        headers=h,
        timeout=15,
    )
    if resp.status_code not in (200, 201):
        print(f"[ERRO] user {cod}: {resp.text[:200]}")
        sys.exit(1)

    user_id = resp.json()[0]["id"]
    num_maquinas = machines_by_client[cod]

    um_rows = [{"user_id": user_id, "num_maquina": nm} for nm in num_maquinas]
    rest_upsert("user_machines", um_rows)

    print(f"  [OK] {email} (pw: {cod}) -> {len(num_maquinas)} maquinas")

print("\n[DONE] Base de dados pronta.")
print("\nLogins de demo:")
for cod, info in clients_seen.items():
    email = info["email"] or f"{cod}@moviter.pt"
    print(f"  email: {email:<35}  password: {cod}")
