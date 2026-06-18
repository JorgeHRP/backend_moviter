from app.db.supabase import get_supabase
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_provider_for_brand(brand: str) -> str | None:
    """Consulta a tabela brands e devolve o provider para a marca."""
    db = get_supabase()
    resp = (
        db.table("brands")
        .select("provider")
        .eq("brand_name", brand.upper().strip())
        .limit(1)
        .execute()
    )
    if resp.data:
        return resp.data[0]["provider"]
    return None


async def get_machine_by_chassis(chassis: str) -> dict | None:
    db = get_supabase()
    resp = (
        db.table("machines")
        .select("*")
        .eq("chassis", chassis)
        .single()
        .execute()
    )
    return resp.data


async def get_machine_by_num(num_maquina: str) -> dict | None:
    db = get_supabase()
    resp = (
        db.table("machines")
        .select("*")
        .eq("num_maquina", num_maquina)
        .single()
        .execute()
    )
    return resp.data


async def get_all_machines() -> list[dict]:
    db = get_supabase()
    resp = db.table("machines").select("*").execute()
    return resp.data or []
