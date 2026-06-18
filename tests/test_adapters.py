"""
Testes unitários — adapters e lógica de mapeamento.
Uso: pytest tests/
"""
import pytest
from datetime import datetime, timezone
from adapters.equipment_adapter import (
    from_hitachi,
    from_trackunit,
    from_db_only,
    _time_ago,
)
from models.equipment import EquipmentStatus


# ─── Fixtures ─────────────────────────────────────────────────────────────────

MACHINE_DB = {
    "id": 1,
    "num_maquina": "MAC0002946",
    "chassis": "HCMDEU50C00110086",
    "designacao": "Escavadora de rastos ZX95USB-7 HITACHI",
    "cod_cliente": "101096",
    "nome_cliente": "VITOR ALMEIDA & FILHOS, S.A",
    "localidade": "BUSTOS",
    "marca": "HITACHI",
    "familia": "Escavadora de rastos",
    "cod_marca": "B032",
    "cod_modelo": "M01416",
    "modelo": None,
    "email": "vitorsantos@iol.pt",
    "telefone1": "937568618",
}

HITACHI_SNAPSHOT = {
    "EquipmentHeader": {
        "OEM": "Hitachi",
        "Model": "ZX95USB-7",
        "SerialNumber": "HCMDEU50C00110086",
    },
    "Location": {
        "Latitude": 40.0042,
        "Longitude": -8.7393,
        "Timestamp": "2026-05-27T10:00:00Z",
    },
    "CumulativeOperatingHours": {"Hour": 320.0, "Timestamp": "2026-05-27T10:00:00Z"},
    "FuelRemaining": {"Percent": 72.0, "FuelTankCapacity": 200.0},
    "DEFRemaining": {"Percent": 45.0},
    "AverageFuelConsumption": {"FuelConsumed": 12.4},
    "FuelUsedLast24": {"FuelConsumed": 11.8},
}

HITACHI_FAULTS = [
    {
        "FaultCode": "107",
        "FaultDescription": "Pressão Ar Admissão - Voltagem Alta",
        "Severity": "HIGH",
        "Source": "ECU Engine",
        "Timestamp": "2026-05-27T08:00:00Z",
    }
]


# ─── Testes _time_ago ──────────────────────────────────────────────────────────

def test_time_ago_now():
    dt = datetime.now(timezone.utc)
    assert _time_ago(dt) == "Agora mesmo"


def test_time_ago_minutes():
    from datetime import timedelta
    dt = datetime.now(timezone.utc) - timedelta(minutes=30)
    result = _time_ago(dt)
    assert "min" in result


def test_time_ago_hours():
    from datetime import timedelta
    dt = datetime.now(timezone.utc) - timedelta(hours=2)
    result = _time_ago(dt)
    assert "h" in result


# ─── Testes from_hitachi ───────────────────────────────────────────────────────

def test_from_hitachi_basic_fields():
    eq = from_hitachi(MACHINE_DB, HITACHI_SNAPSHOT, HITACHI_FAULTS)
    assert eq.id == "MAC0002946"
    assert eq.brand == "Hitachi"
    assert eq.model == "ZX95USB-7"
    assert eq.serialNumber == "HCMDEU50C00110086"
    assert eq.hours == 320.0
    assert eq.fuelLevel == 72.0
    assert eq.defLevel == 45.0
    assert eq.latitude == 40.0042
    assert eq.longitude == -8.7393
    assert eq.tankCapacityLiters == 200.0
    assert eq.hasTelemetry is True


def test_from_hitachi_status_with_alert():
    eq = from_hitachi(MACHINE_DB, HITACHI_SNAPSHOT, HITACHI_FAULTS)
    assert eq.status == EquipmentStatus.telemetry_with_alert
    assert eq.activeAlert is not None
    assert "107" in eq.activeAlert.title


def test_from_hitachi_error_codes():
    eq = from_hitachi(MACHINE_DB, HITACHI_SNAPSHOT, HITACHI_FAULTS)
    assert len(eq.errorCodes) == 1
    assert eq.errorCodes[0].spn == "107"
    assert eq.errorCodes[0].sourceAddress == "ECU Engine"


def test_from_hitachi_no_faults():
    eq = from_hitachi(MACHINE_DB, HITACHI_SNAPSHOT, [])
    assert eq.status == EquipmentStatus.telemetry_no_alert
    assert eq.activeAlert is None
    assert eq.errorCodes == []


def test_from_hitachi_empty_snapshot():
    eq = from_hitachi(MACHINE_DB, {}, [])
    assert eq.status == EquipmentStatus.no_telemetry
    assert eq.hours == 0.0


# ─── Testes from_db_only ──────────────────────────────────────────────────────

def test_from_db_only():
    eq = from_db_only(MACHINE_DB)
    assert eq.status == EquipmentStatus.no_telemetry
    assert eq.hasTelemetry is False
    assert eq.id == "MAC0002946"
    assert eq.brand == "HITACHI"
    assert eq.errorCodes == []
    assert eq.activeAlert is None


# ─── Testes from_trackunit ────────────────────────────────────────────────────

def test_from_trackunit_geojson_coords():
    """Verifica que longitude e latitude são correctamente invertidos do GeoJSON."""
    asset = {
        "id": "abc-123",
        "brand": "HAMM",
        "model": "H 14i",
        "serialNumber": "WGH0H267CHAA00460",
    }
    location_feature = {
        "geometry": {
            "type": "Point",
            "coordinates": [-8.5, 39.7, 100.0],  # [lon, lat, alt]
        },
        "properties": {"timestamp": "2026-05-27T09:00:00Z"},
    }
    eq = from_trackunit(MACHINE_DB, asset, {}, location_feature, [], [])
    assert eq.longitude == -8.5   # coordinates[0] → longitude
    assert eq.latitude == 39.7    # coordinates[1] → latitude
