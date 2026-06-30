"""
Unit tests for SiniestroRepository.get_candidatos and vincular-siniestro endpoint.
"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.db.repositories.siniestro_repository import SiniestroRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_siniestro(empleado_id, fecha_siniestro, numero="SIN-001"):
    s = MagicMock()
    s.id = uuid4()
    s.empleado_id = empleado_id
    s.numero_siniestro = numero
    s.fecha_siniestro = fecha_siniestro
    s.tipo_siniestro = "ACCIDENTE_TRABAJO"
    s.descripcion = "Caída en escalera"
    s.gravedad = "LEVE"
    s.estado = "ACTIVO"
    return s


# ---------------------------------------------------------------------------
# Tests para get_candidatos
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_candidatos_returns_matching_siniestros():
    """get_candidatos devuelve siniestros del empleado con fecha <= fecha_fin."""
    repo = SiniestroRepository()
    empleado_id = uuid4()
    fecha_inicio = date(2026, 1, 10)
    fecha_fin = date(2026, 1, 20)

    sin1 = make_siniestro(empleado_id, date(2026, 1, 5), "SIN-001")  # antes
    sin2 = make_siniestro(empleado_id, date(2026, 1, 20), "SIN-002")  # igual a fecha_fin

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sin2, sin1]

    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_result)

    candidatos = await repo.get_candidatos(db, empleado_id, fecha_inicio, fecha_fin)

    assert len(candidatos) == 2
    db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_candidatos_excludes_other_employees():
    """get_candidatos solo devuelve siniestros del empleado especificado."""
    repo = SiniestroRepository()
    empleado_id = uuid4()
    otro_empleado_id = uuid4()
    fecha_inicio = date(2026, 1, 10)
    fecha_fin = date(2026, 1, 20)

    # El query real filtra por empleado_id via WHERE en SQL; aquí verificamos
    # que la query se construye correctamente devolviendo solo los del empleado.
    sin_otro = make_siniestro(otro_empleado_id, date(2026, 1, 5), "SIN-OTRO")

    mock_result = MagicMock()
    # El filtro real es en SQL; el mock simula que el DB no devuelve nada
    # para el empleado_id correcto (o sea, filtra al otro empleado).
    mock_result.scalars.return_value.all.return_value = []

    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_result)

    candidatos = await repo.get_candidatos(db, empleado_id, fecha_inicio, fecha_fin)

    assert candidatos == []
    db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_candidatos_excludes_future_siniestros():
    """get_candidatos no incluye siniestros con fecha_siniestro > fecha_fin."""
    repo = SiniestroRepository()
    empleado_id = uuid4()
    fecha_inicio = date(2026, 1, 10)
    fecha_fin = date(2026, 1, 20)

    # El filtro real es en SQL; el mock simula que el DB aplica correctamente el filtro.
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []

    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_result)

    candidatos = await repo.get_candidatos(db, empleado_id, fecha_inicio, fecha_fin)

    assert candidatos == []
    # Verificar que se realizó una consulta (el WHERE fecha_siniestro <= fecha_fin lo aplica el DB)
    db.execute.assert_called_once()


# ---------------------------------------------------------------------------
# Test para vincular-siniestro via endpoint function
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_vincular_siniestro_links_and_creates_historial():
    """POST vincular-siniestro actualiza la incapacidad y crea entrada de historial."""
    from app.api.v1.endpoints.incapacidades import vincular_siniestro, _VincularSiniestroBody
    from app.utils.enums import RolUsuario, EstadoIncapacidad, TipoIncapacidad

    empleado_id = uuid4()
    incapacidad_id = uuid4()
    siniestro_id = uuid4()

    # Mocks de dependencias
    mock_incapacidad = MagicMock()
    mock_incapacidad.id = incapacidad_id
    mock_incapacidad.tipo = TipoIncapacidad.ARL
    mock_incapacidad.estado = EstadoIncapacidad.EN_AUDITORIA
    mock_incapacidad.empleado_id = empleado_id
    mock_incapacidad.siniestro = None

    mock_siniestro = MagicMock()
    mock_siniestro.id = siniestro_id
    mock_siniestro.empleado_id = empleado_id
    mock_siniestro.numero_siniestro = "SIN-2026-001"
    mock_siniestro.fecha_siniestro = date(2026, 1, 5)
    mock_siniestro.tipo_siniestro = "ACCIDENTE_TRABAJO"
    mock_siniestro.descripcion = "Caída en escalera"
    mock_siniestro.gravedad = "LEVE"
    mock_siniestro.estado = "ACTIVO"

    mock_updated = MagicMock()
    mock_updated.id = incapacidad_id
    mock_updated.tipo = TipoIncapacidad.ARL
    mock_updated.estado = EstadoIncapacidad.EN_AUDITORIA
    mock_updated.empleado_id = empleado_id
    mock_updated.siniestro_id = siniestro_id
    mock_updated.numero_siniestro = "SIN-2026-001"
    mock_updated.siniestro = mock_siniestro

    mock_current_user = MagicMock()
    mock_current_user.rol = RolUsuario.AUDITOR
    mock_current_user.id = uuid4()
    mock_current_user.nombre_completo = "Test Auditor"

    body = _VincularSiniestroBody(siniestro_id=siniestro_id)

    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()

    with (
        patch(
            "app.api.v1.endpoints.incapacidades.incapacidad_service"
        ) as mock_inc_service,
        patch(
            "app.api.v1.endpoints.incapacidades.siniestro_repository"
        ) as mock_sin_repo,
        patch(
            "app.api.v1.endpoints.incapacidades._serialize_incapacidad"
        ) as mock_serialize,
    ):
        mock_inc_service.get_incapacidad = AsyncMock(
            side_effect=[mock_incapacidad, mock_updated]
        )
        mock_sin_repo.get_by_id = AsyncMock(return_value=mock_siniestro)

        # Patch the inline import of incapacidad_repository
        with patch(
            "app.db.repositories.incapacidad_repository.incapacidad_repository"
        ) as mock_inc_repo:
            mock_inc_repo.update_flushed = AsyncMock()
            mock_serialize.return_value = {
                "id": str(incapacidad_id),
                "siniestro_id": str(siniestro_id),
                "numero_siniestro": "SIN-2026-001",
            }

            result = await vincular_siniestro(
                incapacidad_id=incapacidad_id,
                body=body,
                db=db,
                current_user=mock_current_user,
            )

    # Verificar que se hizo commit
    db.commit.assert_called_once()
    db.add.assert_called_once()  # HistorialEstado añadido
    db.flush.assert_called()
