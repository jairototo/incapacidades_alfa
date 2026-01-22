"""
Tests para consulta pública de incapacidades (sin autenticación).
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime

from app.models.incapacidad import Incapacidad
from app.models.documento import Documento
from app.models.historial_estado import HistorialEstado
from app.utils.enums import (
    TipoIncapacidad,
    EstadoIncapacidad,
    TipoDocumentoAdjunto,
    Prioridad
)
from decimal import Decimal


@pytest.mark.asyncio
class TestConsultaPublica:
    """Tests para endpoint de consulta pública."""

    async def test_consulta_por_numero_exitosa(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_incapacidad,
        test_empleado
    ):
        """Debe retornar incapacidad al buscar por número válido."""
        response = await client.get(
            "/api/v1/incapacidades/consultar",
            params={"numero": test_incapacidad.numero}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar campos básicos
        assert data["numero"] == test_incapacidad.numero
        assert data["estado"] == "RADICADA"
        assert data["tipo"] == "ARL"
        assert data["dias_totales"] == 10
        
        # Verificar nombre completo sanitizado
        assert data["nombre_completo"] == f"{test_empleado.nombres} {test_empleado.apellidos}"
        assert data["tipo_documento"] == "CC"
        
        # Verificar que tiene estructuras requeridas
        assert "historial_estados" in data
        assert "documentos" in data
        
        # Verificar fechas
        assert "created_at" in data
        assert "updated_at" in data

    async def test_consulta_por_numero_case_insensitive(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_incapacidad
    ):
        """Debe buscar número en minúsculas/mayúsculas."""
        # Buscar con minúsculas
        response = await client.get(
            "/api/v1/incapacidades/consultar",
            params={"numero": test_incapacidad.numero.lower()}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["numero"] == test_incapacidad.numero

    async def test_consulta_por_documento_empleado_exitosa(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_incapacidad,
        test_empleado
    ):
        """Debe retornar incapacidad al buscar por documento de empleado."""
        response = await client.get(
            "/api/v1/incapacidades/consultar",
            params={
                "documento": test_empleado.numero_documento,
                "tipo_documento": test_empleado.tipo_documento.value
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["numero"] == test_incapacidad.numero
        assert data["tipo_documento"] == "CC"

    async def test_consulta_por_documento_afiliado_exitosa(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_afiliado
    ):
        """Debe retornar incapacidad al buscar por documento de afiliado."""
        # Crear incapacidad de tipo SALUD
        incapacidad_salud = Incapacidad(
            numero="INC-SAL-TEST-001",
            afiliado_id=test_afiliado.id,
            tipo=TipoIncapacidad.SALUD,
            fecha_inicio=date(2026, 1, 5),
            fecha_fin=date(2026, 1, 15),
            dias_totales=11,
            diagnostico_cie10="J06.9",
            descripcion_diagnostico="Infección aguda de las vías respiratorias superiores",
            estado=EstadoIncapacidad.RADICADA,
            fecha_radicacion=datetime.utcnow(),
            prioridad=Prioridad.NORMAL,
        )
        
        db_session.add(incapacidad_salud)
        await db_session.commit()
        await db_session.refresh(incapacidad_salud)
        
        response = await client.get(
            "/api/v1/incapacidades/consultar",
            params={
                "documento": test_afiliado.numero_documento,
                "tipo_documento": test_afiliado.tipo_documento
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["numero"] == incapacidad_salud.numero
        assert data["tipo"] == "SALUD"
        assert data["nombre_completo"] == f"{test_afiliado.nombres} {test_afiliado.apellidos}"

    async def test_consulta_sin_parametros(self, client: AsyncClient):
        """Debe retornar error 400 si no se envían parámetros."""
        response = await client.get("/api/v1/incapacidades/consultar")
        
        assert response.status_code == 400
        assert "parametros" in response.json()["detail"].lower() or "proporcionar" in response.json()["detail"].lower()

    async def test_consulta_solo_documento_sin_tipo(self, client: AsyncClient):
        """Debe retornar error 400 si se envía documento sin tipo."""
        response = await client.get(
            "/api/v1/incapacidades/consultar",
            params={"documento": "1234567890"}
        )
        
        assert response.status_code == 400

    async def test_consulta_numero_inexistente(self, client: AsyncClient):
        """Debe retornar 404 si no existe el número."""
        response = await client.get(
            "/api/v1/incapacidades/consultar",
            params={"numero": "INC-999999-999999"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "no se encontró" in data["detail"].lower()

    async def test_consulta_documento_inexistente(self, client: AsyncClient):
        """Debe retornar 404 si no existe el documento."""
        response = await client.get(
            "/api/v1/incapacidades/consultar",
            params={
                "documento": "9999999999",
                "tipo_documento": "CC"
            }
        )
        
        assert response.status_code == 404

    async def test_datos_sensibles_sanitizados(
        self,
        client: AsyncClient,
        test_incapacidad
    ):
        """Debe sanitizar datos sensibles en la respuesta."""
        response = await client.get(
            "/api/v1/incapacidades/consultar",
            params={"numero": test_incapacidad.numero}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # No debe incluir datos sensibles
        assert "valor_total" not in data
        assert "valor_dia" not in data
        assert "salario_base" not in data
        assert "cuenta_bancaria" not in data
        assert "radicado_por_id" not in data
        assert "auditado_por_id" not in data
        assert "aprobado_por_id" not in data

    async def test_historial_estados_ordenado(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_incapacidad,
        test_usuario
    ):
        """El historial debe venir ordenado cronológicamente."""
        # Crear varios cambios de estado
        historial_1 = HistorialEstado(
            entity_type="incapacidad",
            entity_id=test_incapacidad.id,
            estado_anterior=EstadoIncapacidad.RADICADA,
            estado_nuevo=EstadoIncapacidad.EN_AUDITORIA,
            observacion="Iniciando auditoría",
            cambiado_por_id=test_usuario.id
        )
        
        db_session.add(historial_1)
        await db_session.commit()
        
        # Esperar un poco para tener timestamps diferentes
        import asyncio
        await asyncio.sleep(0.1)
        
        historial_2 = HistorialEstado(
            entity_type="incapacidad",
            entity_id=test_incapacidad.id,
            estado_anterior=EstadoIncapacidad.EN_AUDITORIA,
            estado_nuevo=EstadoIncapacidad.OBSERVADA,
            observacion="Falta documentación",
            cambiado_por_id=test_usuario.id
        )
        
        db_session.add(historial_2)
        await db_session.commit()
        
        response = await client.get(
            "/api/v1/incapacidades/consultar",
            params={"numero": test_incapacidad.numero}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        historial = data["historial_estados"]
        assert len(historial) >= 2
        
        # Verificar orden cronológico
        fechas = [h["fecha_cambio"] for h in historial]
        # Comparar que cada fecha es menor o igual que la siguiente
        for i in range(len(fechas) - 1):
            assert fechas[i] <= fechas[i + 1], "El historial debe estar ordenado cronológicamente"

    async def test_documentos_solo_publicos(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_incapacidad,
        test_usuario
    ):
        """Solo debe retornar documentos públicos."""
        # Crear documento público
        doc_publico = Documento(
            incapacidad_id=test_incapacidad.id,
            tipo_documento=TipoDocumentoAdjunto.INCAPACIDAD_MEDICA,
            nombre_archivo="cert-medico.pdf",
            nombre_original="certificado.pdf",
            ruta_storage="docs/cert.pdf",
            bucket="incapacidades",
            mime_type="application/pdf",
            tamanio_bytes=250000,
            uploaded_by_id=test_usuario.id
        )
        
        # Crear documento "privado" (interno)
        doc_privado = Documento(
            incapacidad_id=test_incapacidad.id,
            tipo_documento=TipoDocumentoAdjunto.SOPORTE_PAGO,
            nombre_archivo="pago-interno.pdf",
            nombre_original="pago.pdf",
            ruta_storage="docs/pago.pdf",
            bucket="incapacidades",
            mime_type="application/pdf",
            tamanio_bytes=150000,
            uploaded_by_id=test_usuario.id
        )
        
        db_session.add(doc_publico)
        db_session.add(doc_privado)
        await db_session.commit()
        
        response = await client.get(
            "/api/v1/incapacidades/consultar",
            params={"numero": test_incapacidad.numero}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        tipos_permitidos = ["INCAPACIDAD_MEDICA", "CEDULA", "HISTORIA_CLINICA"]
        for doc in data["documentos"]:
            assert doc["tipo_documento"] in tipos_permitidos, f"Tipo {doc['tipo_documento']} no es público"
        
        # Verificar que SOPORTE_PAGO no aparece
        tipos_docs = [doc["tipo_documento"] for doc in data["documentos"]]
        assert "SOPORTE_PAGO" not in tipos_docs

    async def test_observaciones_solo_si_observada(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_incapacidad,
        test_usuario
    ):
        """Observaciones solo aparecen si está OBSERVADA."""
        # Caso 1: RADICADA - no debe tener observaciones
        response_radicada = await client.get(
            "/api/v1/incapacidades/consultar",
            params={"numero": test_incapacidad.numero}
        )
        assert response_radicada.status_code == 200
        data_radicada = response_radicada.json()
        assert data_radicada["observaciones_publicas"] is None
        
        # Cambiar a OBSERVADA
        test_incapacidad.estado = EstadoIncapacidad.OBSERVADA
        await db_session.commit()
        
        # Crear historial con observaciones
        historial_obs = HistorialEstado(
            entity_type="incapacidad",
            entity_id=test_incapacidad.id,
            estado_anterior=EstadoIncapacidad.RADICADA,
            estado_nuevo=EstadoIncapacidad.OBSERVADA,
            observacion="Falta adjuntar historia clínica completa",
            cambiado_por_id=test_usuario.id
        )
        
        db_session.add(historial_obs)
        await db_session.commit()
        
        # Caso 2: OBSERVADA - debe tener observaciones
        response_observada = await client.get(
            "/api/v1/incapacidades/consultar",
            params={"numero": test_incapacidad.numero}
        )
        assert response_observada.status_code == 200
        data_observada = response_observada.json()
        assert data_observada["observaciones_publicas"] is not None
        assert "historia clínica" in data_observada["observaciones_publicas"].lower()

    async def test_respuesta_incluye_diagnostico_basico(
        self,
        client: AsyncClient,
        test_incapacidad
    ):
        """Debe incluir información médica básica (código CIE-10 y descripción)."""
        response = await client.get(
            "/api/v1/incapacidades/consultar",
            params={"numero": test_incapacidad.numero}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Debe incluir datos médicos básicos
        assert data["diagnostico_cie10"] == test_incapacidad.diagnostico_cie10
        assert data["descripcion_diagnostico"] == test_incapacidad.descripcion_diagnostico
        
        # Puede incluir EPS si está disponible
        if test_incapacidad.eps:
            assert "eps" in data

    async def test_formato_documentos_correcto(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_incapacidad,
        test_documento
    ):
        """Los documentos deben tener el formato correcto."""
        response = await client.get(
            "/api/v1/incapacidades/consultar",
            params={"numero": test_incapacidad.numero}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["documentos"]:
            doc = data["documentos"][0]
            
            # Verificar campos requeridos
            assert "id" in doc
            assert "nombre_archivo" in doc
            assert "tipo_documento" in doc
            assert "tamanio_kb" in doc
            assert "fecha_upload" in doc
            
            # Verificar tipos de datos
            assert isinstance(doc["tamanio_kb"], int)
            assert doc["tamanio_kb"] > 0

    async def test_response_tiene_todas_claves_requeridas(
        self,
        client: AsyncClient,
        test_incapacidad
    ):
        """El response debe tener todas las claves requeridas del schema."""
        response = await client.get(
            "/api/v1/incapacidades/consultar",
            params={"numero": test_incapacidad.numero}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Claves requeridas según el schema
        claves_requeridas = [
            "numero",
            "estado",
            "tipo",
            "fecha_inicio",
            "fecha_fin",
            "dias_totales",
            "nombre_completo",
            "tipo_documento",
            "historial_estados",
            "documentos",
            "created_at",
            "updated_at"
        ]
        
        for clave in claves_requeridas:
            assert clave in data, f"Falta la clave requerida: {clave}"

    async def test_numero_con_espacios_se_limpia(
        self,
        client: AsyncClient,
        test_incapacidad
    ):
        """El número con espacios al inicio/final debe funcionar."""
        response = await client.get(
            "/api/v1/incapacidades/consultar",
            params={"numero": f"  {test_incapacidad.numero}  "}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["numero"] == test_incapacidad.numero
