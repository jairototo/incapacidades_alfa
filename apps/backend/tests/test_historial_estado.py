"""
Tests para el módulo de HistorialEstado.
"""
import pytest
from uuid import uuid4
from datetime import datetime

from app.models.historial_estado import HistorialEstado
from app.services.historial_estado_service import historial_estado_service


@pytest.mark.asyncio
class TestHistorialEstadoService:
    """Tests para HistorialEstadoService."""
    
    async def test_create_historial_entry(self, db_session, test_empleado):
        """Test crear entrada de historial."""
        entity_id = uuid4()
        
        historial = await historial_estado_service.create_historial_entry(
            db=db_session,
            entity_type="incapacidad",
            entity_id=entity_id,
            estado_anterior=None,
            estado_nuevo="RADICADA",
            observacion="Incapacidad creada",
            cambiado_por_id=None
        )
        
        assert historial.entity_type == "incapacidad"
        assert historial.entity_id == entity_id
        assert historial.estado_anterior is None
        assert historial.estado_nuevo == "RADICADA"
        assert historial.observacion == "Incapacidad creada"
    
    async def test_get_entity_history(self, db_session):
        """Test obtener historial de una entidad."""
        entity_id = uuid4()
        
        # Crear varios cambios de estado
        await historial_estado_service.create_historial_entry(
            db=db_session,
            entity_type="incapacidad",
            entity_id=entity_id,
            estado_anterior=None,
            estado_nuevo="RADICADA"
        )
        
        await historial_estado_service.create_historial_entry(
            db=db_session,
            entity_type="incapacidad",
            entity_id=entity_id,
            estado_anterior="RADICADA",
            estado_nuevo="EN_AUDITORIA"
        )
        
        await historial_estado_service.create_historial_entry(
            db=db_session,
            entity_type="incapacidad",
            entity_id=entity_id,
            estado_anterior="EN_AUDITORIA",
            estado_nuevo="APROBADA"
        )
        
        # Obtener historial
        historial = await historial_estado_service.get_entity_history(
            db=db_session,
            entity_type="incapacidad",
            entity_id=entity_id
        )
        
        assert len(historial) == 3
        # Debe estar ordenado por fecha (más reciente primero)
        assert historial[0].estado_nuevo == "APROBADA"
        assert historial[1].estado_nuevo == "EN_AUDITORIA"
        assert historial[2].estado_nuevo == "RADICADA"
    
    async def test_get_incapacidad_history(self, db_session):
        """Test shortcut para historial de incapacidad."""
        incapacidad_id = uuid4()
        
        await historial_estado_service.create_historial_entry(
            db=db_session,
            entity_type="incapacidad",
            entity_id=incapacidad_id,
            estado_anterior=None,
            estado_nuevo="RADICADA"
        )
        
        historial = await historial_estado_service.get_incapacidad_history(
            db=db_session,
            incapacidad_id=incapacidad_id
        )
        
        assert len(historial) == 1
        assert historial[0].entity_type == "incapacidad"

    async def test_get_incapacidad_history_includes_cambiado_por_nombre(self, db_session, test_usuario):
        """El historial debe incluir el nombre del usuario responsable del cambio (no solo el id)."""
        incapacidad_id = uuid4()

        await historial_estado_service.create_historial_entry(
            db=db_session,
            entity_type="incapacidad",
            entity_id=incapacidad_id,
            estado_anterior="RADICADA",
            estado_nuevo="EN_AUDITORIA",
            cambiado_por_id=test_usuario.id,
        )

        historial = await historial_estado_service.get_incapacidad_history(
            db=db_session,
            incapacidad_id=incapacidad_id,
        )

        assert len(historial) == 1
        assert historial[0].cambiado_por_id == test_usuario.id
        assert historial[0].cambiado_por_nombre == test_usuario.nombre_completo

    async def test_get_incapacidad_history_cambiado_por_nombre_none_when_system_generated(self, db_session):
        """Una transición automática (sin usuario) no debe tener nombre — no un error."""
        incapacidad_id = uuid4()

        await historial_estado_service.create_historial_entry(
            db=db_session,
            entity_type="incapacidad",
            entity_id=incapacidad_id,
            estado_anterior=None,
            estado_nuevo="RADICADA",
            cambiado_por_id=None,
        )

        historial = await historial_estado_service.get_incapacidad_history(
            db=db_session,
            incapacidad_id=incapacidad_id,
        )

        assert len(historial) == 1
        assert historial[0].cambiado_por_nombre is None

    async def test_get_siniestro_history(self, db_session):
        """Test shortcut para historial de siniestro."""
        siniestro_id = uuid4()
        
        await historial_estado_service.create_historial_entry(
            db=db_session,
            entity_type="siniestro",
            entity_id=siniestro_id,
            estado_anterior="REPORTADO",
            estado_nuevo="EN_INVESTIGACION"
        )
        
        historial = await historial_estado_service.get_siniestro_history(
            db=db_session,
            siniestro_id=siniestro_id
        )
        
        assert len(historial) == 1
        assert historial[0].entity_type == "siniestro"
    
    async def test_get_recent_changes(self, db_session):
        """Test obtener cambios recientes."""
        # Crear varios cambios en diferentes entidades
        for i in range(5):
            await historial_estado_service.create_historial_entry(
                db=db_session,
                entity_type="incapacidad",
                entity_id=uuid4(),
                estado_anterior=None,
                estado_nuevo="RADICADA"
            )
        
        recent = await historial_estado_service.get_recent_changes(
            db=db_session,
            limit=3
        )
        
        assert len(recent) == 3
    
    async def test_search_historial(self, db_session):
        """Test búsqueda con filtros."""
        entity_id = uuid4()
        
        await historial_estado_service.create_historial_entry(
            db=db_session,
            entity_type="incapacidad",
            entity_id=entity_id,
            estado_anterior=None,
            estado_nuevo="RADICADA"
        )
        
        await historial_estado_service.create_historial_entry(
            db=db_session,
            entity_type="siniestro",
            entity_id=uuid4(),
            estado_anterior="REPORTADO",
            estado_nuevo="EN_INVESTIGACION"
        )
        
        # Buscar solo incapacidades
        resultados = await historial_estado_service.search_historial(
            db=db_session,
            entity_type="incapacidad"
        )
        
        assert len(resultados) == 1
        assert resultados[0].entity_type == "incapacidad"
    
    async def test_count_entity_changes(self, db_session):
        """Test contar cambios de una entidad."""
        entity_id = uuid4()
        
        for i in range(3):
            await historial_estado_service.create_historial_entry(
                db=db_session,
                entity_type="incapacidad",
                entity_id=entity_id,
                estado_anterior=None,
                estado_nuevo=f"ESTADO_{i}"
            )
        
        count = await historial_estado_service.count_entity_changes(
            db=db_session,
            entity_type="incapacidad",
            entity_id=entity_id
        )
        
        assert count == 3
    
    async def test_get_first_and_current_state(self, db_session):
        """Test obtener primer y último estado."""
        entity_id = uuid4()
        
        # Crear historial
        await historial_estado_service.create_historial_entry(
            db=db_session,
            entity_type="incapacidad",
            entity_id=entity_id,
            estado_anterior=None,
            estado_nuevo="RADICADA"
        )
        
        await historial_estado_service.create_historial_entry(
            db=db_session,
            entity_type="incapacidad",
            entity_id=entity_id,
            estado_anterior="RADICADA",
            estado_nuevo="APROBADA"
        )
        
        # Obtener primer estado
        first = await historial_estado_service.get_first_state(
            db=db_session,
            entity_type="incapacidad",
            entity_id=entity_id
        )
        
        assert first.estado_nuevo == "RADICADA"
        
        # Obtener estado actual
        current = await historial_estado_service.get_current_state(
            db=db_session,
            entity_type="incapacidad",
            entity_id=entity_id
        )
        
        assert current.estado_nuevo == "APROBADA"


@pytest.mark.asyncio
class TestHistorialEstadoAPI:
    """Tests para los endpoints de HistorialEstado."""
    
    async def test_list_historial(self, client, db_session):
        """Test listar historial."""
        # Crear algunos registros
        entity_id = uuid4()
        await historial_estado_service.create_historial_entry(
            db=db_session,
            entity_type="incapacidad",
            entity_id=entity_id,
            estado_anterior=None,
            estado_nuevo="RADICADA"
        )
        
        response = await client.get("/api/v1/historial/")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    async def test_get_recent_changes_endpoint(self, client, db_session):
        """Test endpoint de cambios recientes."""
        # Crear registros
        for _ in range(3):
            await historial_estado_service.create_historial_entry(
                db=db_session,
                entity_type="incapacidad",
                entity_id=uuid4(),
                estado_anterior=None,
                estado_nuevo="RADICADA"
            )
        
        response = await client.get("/api/v1/historial/recent?limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2
    
    async def test_get_entity_history_endpoint(self, client, db_session):
        """Test endpoint de historial de entidad específica."""
        entity_id = uuid4()
        
        await historial_estado_service.create_historial_entry(
            db=db_session,
            entity_type="incapacidad",
            entity_id=entity_id,
            estado_anterior=None,
            estado_nuevo="RADICADA"
        )
        
        response = await client.get(f"/api/v1/historial/incapacidad/{entity_id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["entity_type"] == "incapacidad"

    async def test_get_entity_history_endpoint_includes_cambiado_por_nombre(self, client, db_session, test_usuario):
        """La respuesta HTTP del historial debe traer el nombre del responsable, no solo su id."""
        entity_id = uuid4()

        await historial_estado_service.create_historial_entry(
            db=db_session,
            entity_type="incapacidad",
            entity_id=entity_id,
            estado_anterior="RADICADA",
            estado_nuevo="EN_AUDITORIA",
            cambiado_por_id=test_usuario.id,
        )

        response = await client.get(f"/api/v1/historial/incapacidad/{entity_id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["cambiado_por_id"] == str(test_usuario.id)
        assert data[0]["cambiado_por_nombre"] == test_usuario.nombre_completo

    async def test_count_endpoint(self, client, db_session):
        """Test endpoint de contador."""
        entity_id = uuid4()
        
        await historial_estado_service.create_historial_entry(
            db=db_session,
            entity_type="siniestro",
            entity_id=entity_id,
            estado_anterior=None,
            estado_nuevo="REPORTADO"
        )
        
        response = await client.get(f"/api/v1/historial/siniestro/{entity_id}/count")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["entity_type"] == "siniestro"
