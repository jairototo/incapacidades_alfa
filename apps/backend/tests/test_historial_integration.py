"""
Tests de integración para el flujo completo con historial automático.
"""
import pytest
from datetime import date

from apps.backend.app.services.incapacidad_service import incapacidad_service
from apps.backend.app.services.siniestro_service import siniestro_service
from apps.backend.app.services.historial_estado_service import historial_estado_service
from apps.backend.app.schemas.incapacidad import IncapacidadCreate
from apps.backend.app.schemas.siniestro import SiniestroCreate
from apps.backend.app.utils.enums import TipoIncapacidad, TipoSiniestro, GravedadSiniestro


@pytest.mark.asyncio
class TestHistorialIntegration:
    """Tests de integración para verificar creación automática de historial."""
    
    async def test_incapacidad_workflow_creates_history(
        self, db_session, test_empleado, test_empresa, test_afiliado
    ):
        """Test que el workflow de incapacidad crea historial automáticamente."""
        # Crear incapacidad
        incapacidad_data = IncapacidadCreate(
            afiliado_id=test_afiliado.id,
            tipo=TipoIncapacidad.SALUD,
            fecha_inicio=date(2026, 1, 10),
            fecha_fin=date(2026, 1, 15),
            dias_incapacidad=5,
            diagnostico="Prueba de historial",
            numero_certificado="CERT-HIST-001"
        )
        
        incapacidad = await incapacidad_service.create_incapacidad(
            db=db_session,
            incapacidad_data=incapacidad_data
        )
        
        # Radicar (RADICADA → EN_AUDITORIA)
        incapacidad = await incapacidad_service.radicar_incapacidad(
            db=db_session,
            incapacidad_id=incapacidad.id
        )
        
        # Verificar que se creó historial
        historial = await historial_estado_service.get_incapacidad_history(
            db=db_session,
            incapacidad_id=incapacidad.id
        )
        
        assert len(historial) == 1
        assert historial[0].entity_type == "incapacidad"
        assert historial[0].estado_anterior == "RADICADA"
        assert historial[0].estado_nuevo == "EN_AUDITORIA"
        assert "radicada" in historial[0].observacion.lower()
        
        # Aprobar (EN_AUDITORIA → APROBADA)
        incapacidad = await incapacidad_service.aprobar_incapacidad(
            db=db_session,
            incapacidad_id=incapacidad.id
        )
        
        # Verificar que ahora hay 2 registros
        historial = await historial_estado_service.get_incapacidad_history(
            db=db_session,
            incapacidad_id=incapacidad.id
        )
        
        assert len(historial) == 2
        assert historial[0].estado_nuevo == "APROBADA"
        assert historial[1].estado_nuevo == "EN_AUDITORIA"
    
    async def test_siniestro_workflow_creates_history(
        self, db_session, test_empleado, test_empresa
    ):
        """Test que el workflow de siniestro crea historial automáticamente."""
        # Crear siniestro
        siniestro_data = SiniestroCreate(
            empresa_id=test_empresa.id,
            empleado_id=test_empleado.id,
            tipo_siniestro=TipoSiniestro.ACCIDENTE_TRABAJO,
            fecha_siniestro=date(2026, 1, 9),
            descripcion="Prueba historial siniestro",
            lugar_ocurrencia="Oficina",
            gravedad=GravedadSiniestro.LEVE
        )
        
        siniestro = await siniestro_service.create_siniestro(
            db=db_session,
            siniestro_data=siniestro_data
        )
        
        # Reportar (REPORTADO → EN_INVESTIGACION)
        siniestro = await siniestro_service.reportar_siniestro(
            db=db_session,
            siniestro_id=siniestro.id
        )
        
        # Verificar historial
        historial = await historial_estado_service.get_siniestro_history(
            db=db_session,
            siniestro_id=siniestro.id
        )
        
        assert len(historial) == 1
        assert historial[0].entity_type == "siniestro"
        assert historial[0].estado_anterior == "REPORTADO"
        assert historial[0].estado_nuevo == "EN_INVESTIGACION"
        
        # Cerrar (EN_INVESTIGACION → CERRADO)
        siniestro = await siniestro_service.cerrar_siniestro(
            db=db_session,
            siniestro_id=siniestro.id,
            observaciones="Investigación completada"
        )
        
        # Verificar que ahora hay 2 registros
        historial = await historial_estado_service.get_siniestro_history(
            db=db_session,
            siniestro_id=siniestro.id
        )
        
        assert len(historial) == 2
        assert historial[0].estado_nuevo == "CERRADO"
        assert "completada" in historial[0].observacion.lower()
    
    async def test_incapacidad_historial_endpoint(
        self, client, db_session, test_empleado, test_afiliado
    ):
        """Test endpoint /incapacidades/{id}/historial."""
        # Crear y radicar incapacidad
        incapacidad_data = {
            "afiliado_id": str(test_afiliado.id),
            "tipo": "SALUD",
            "fecha_inicio": "2026-01-10",
            "fecha_fin": "2026-01-13",
            "dias_incapacidad": 3,
            "diagnostico": "Test endpoint historial",
            "numero_certificado": "CERT-EP-001"
        }
        
        response = await client.post("/api/v1/incapacidades/", json=incapacidad_data)
        assert response.status_code == 201
        incapacidad = response.json()
        incapacidad_id = incapacidad["id"]
        
        # Radicar
        response = await client.post(f"/api/v1/incapacidades/{incapacidad_id}/radicar")
        assert response.status_code == 200
        
        # Obtener historial
        response = await client.get(f"/api/v1/incapacidades/{incapacidad_id}/historial")
        assert response.status_code == 200
        
        historial = response.json()
        assert len(historial) >= 1
        # La respuesta es una lista directa de registros de historial
        assert historial[0]["entity_type"] == "incapacidad"
        assert historial[0]["entity_id"] == incapacidad_id
    
    async def test_siniestro_historial_endpoint(
        self, client, db_session, test_empleado, test_empresa
    ):
        """Test endpoint /siniestros/{id}/historial."""
        # Crear siniestro
        siniestro_data = {
            "empresa_id": str(test_empresa.id),
            "empleado_id": str(test_empleado.id),
            "tipo_siniestro": "ACCIDENTE_TRABAJO",
            "fecha_siniestro": "2026-01-09",
            "descripcion": "Test endpoint",
            "lugar_ocurrencia": "Oficina",
            "gravedad": "LEVE"
        }
        
        response = await client.post("/api/v1/siniestros/", json=siniestro_data)
        assert response.status_code == 201
        siniestro = response.json()
        siniestro_id = siniestro["id"]
        
        # Reportar
        response = await client.post(f"/api/v1/siniestros/{siniestro_id}/reportar")
        assert response.status_code == 200
        
        # Obtener historial
        response = await client.get(f"/api/v1/siniestros/{siniestro_id}/historial")
        assert response.status_code == 200
        
        historial = response.json()
        assert len(historial) >= 1
        assert historial[0]["entity_type"] == "siniestro"
    
    async def test_multiple_entities_in_historial_list(
        self, client, db_session, test_empleado, test_empresa, test_afiliado
    ):
        """Test que el listado general muestra historial de múltiples entidades."""
        # Crear incapacidad
        inc_data = {
            "afiliado_id": str(test_afiliado.id),
            "tipo": "SALUD",
            "fecha_inicio": "2026-01-10",
            "fecha_fin": "2026-01-13",
            "dias_incapacidad": 3,
            "diagnostico": "Test multi",
            "numero_certificado": "CERT-MULTI-001"
        }
        response = await client.post("/api/v1/incapacidades/", json=inc_data)
        inc_id = response.json()["id"]
        
        # Radicar incapacidad
        await client.post(f"/api/v1/incapacidades/{inc_id}/radicar")
        
        # Crear siniestro
        sin_data = {
            "empresa_id": str(test_empresa.id),
            "empleado_id": str(test_empleado.id),
            "tipo_siniestro": "ACCIDENTE_TRABAJO",
            "fecha_siniestro": "2026-01-09",
            "descripcion": "Test multi",
            "lugar_ocurrencia": "Oficina",
            "gravedad": "LEVE"
        }
        response = await client.post("/api/v1/siniestros/", json=sin_data)
        sin_id = response.json()["id"]
        
        # Reportar siniestro
        await client.post(f"/api/v1/siniestros/{sin_id}/reportar")
        
        # Listar todo el historial
        response = await client.get("/api/v1/historial/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) >= 2
        
        # Verificar que hay ambos tipos de entidades
        entity_types = {item["entity_type"] for item in data["items"]}
        assert "incapacidad" in entity_types
        assert "siniestro" in entity_types
