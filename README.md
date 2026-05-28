# Moviter Equipment API

Backend FastAPI para a app mobile Moviter — agrega telemetria de múltiplas APIs externas num schema normalizado.

---

## Arquitectura

```
app/
├── main.py                        # Entry point FastAPI
├── core/
│   ├── config.py                  # Settings via pydantic-settings + .env
│   ├── logging.py                 # Logger centralizado
│   └── exceptions.py              # Excepções personalizadas
├── api/v1/
│   ├── equipment.py               # GET /equipment, GET /equipment/{id}
│   ├── clients.py                 # GET /clients
│   └── auth_johndeere.py          # OAuth John Deere
├── services/
│   ├── hitachi.py                 # Hitachi AEMP 2.0 / ISO 15143-3
│   ├── trackunit.py               # Trackunit IRIS API
│   ├── johndeere.py               # John Deere Operations Center
│   ├── proemion.py                # Proemion SOAP (Wirtgen Group)
│   ├── machines_db.py             # Operações Supabase
│   └── orchestrator.py            # Orquestra BD + API externa
├── adapters/
│   └── equipment_adapter.py       # Normaliza todas as APIs → EquipmentModel
├── models/
│   └── equipment.py               # Schemas Pydantic
└── db/
    ├── supabase.py                # Cliente Supabase singleton
    └── cache.py                   # Cache Redis (opcional)

scripts/
├── create_tables.sql              # DDL para o Supabase
└── seed_machines.py               # Importa CSV de máquinas para o Supabase

tests/
└── test_adapters.py               # Testes unitários dos adapters
```

---

## Instalação

```bash
# 1. Clonar e entrar na pasta
git clone <repo>
cd moviter-api

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com as credenciais reais
```

---

## Base de dados (Supabase)

```bash
# 1. Criar tabela no Supabase SQL Editor
#    Copiar e executar o conteúdo de scripts/create_tables.sql

# 2. Copiar o CSV para data/
mkdir -p data
cp /caminho/para/rocim_machines.csv data/

# 3. Importar máquinas
python scripts/seed_machines.py
```

---

## Arranque

```bash
# Desenvolvimento
uvicorn app.main:app --reload --port 8000

# Produção
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Documentação interativa disponível em: http://localhost:8000/docs

---

## Endpoints principais

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/api/v1/clients` | Lista clientes |
| `GET` | `/api/v1/equipment?cod_cliente=101096` | Lista equipamentos de um cliente |
| `GET` | `/api/v1/equipment/{id}` | Detalhe completo de um equipamento |
| `GET` | `/api/v1/auth/johndeere/login?cod_cliente=...` | Inicia OAuth John Deere |
| `GET` | `/api/v1/auth/johndeere/callback` | Callback OAuth John Deere |
| `POST`| `/api/v1/auth/johndeere/token` | Injeta token JD manualmente (testes) |
| `GET` | `/health` | Health check |

---

## Providers de telemetria por marca

| Marca | Provider | Protocolo |
|-------|----------|-----------|
| HITACHI | Hitachi AEMP 2.0 | REST/JSON |
| HAMM | Trackunit IRIS | REST/JSON |
| VOGELE | Trackunit IRIS | REST/JSON |
| WIRTGEN | Trackunit IRIS | REST/JSON |
| GEHL | Trackunit IRIS | REST/JSON |
| JOHN DEERE | Operations Center | REST/JSON + OAuth 2.0 |
| FIORI, NPK, WARATAH | — | Sem telemetria |

---

## Testes

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

---

## Notas importantes

- **GeoJSON Trackunit**: coordenadas em `[longitude, latitude]` — ordem inversa ao convencional
- **DEF < 10%**: motor entra em modo derate — alerta crítico implementado no adapter
- **Proemion**: protocolo SOAP/XML — requer `zeep`; usado para HAMM/VOGELE/WIRTGEN via Wirtgen Group
- **John Deere OAuth**: tokens devem ser persistidos no Supabase em produção (actualmente em memória)
- **Cache**: Redis opcional — se `REDIS_URL` estiver vazio, funciona sem cache
- **Rate limit Trackunit**: 1 req/s no endpoint de localizações — respeitar em produção
