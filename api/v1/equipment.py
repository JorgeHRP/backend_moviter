from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional

from models.equipment import EquipmentModel, MachineInput
from services import orchestrator
from core.security import get_current_client
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/equipment", tags=["Equipment"])


@router.post("/telemetry", response_model=EquipmentModel)
async def get_telemetry(
    machine: MachineInput,
    x_jd_token: Optional[str] = Header(None, description="Access token John Deere (se aplicável)"),
    _: dict = Depends(get_current_client),
):
    """
    Recebe os dados da máquina e devolve telemetria completa.
    O provider é determinado automaticamente pela marca via tabela brands.
    """
    try:
        return await orchestrator.get_equipment(machine.model_dump(), jd_access_token=x_jd_token)
    except Exception as e:
        logger.error(f"Erro ao buscar telemetria para {machine.chassis}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
