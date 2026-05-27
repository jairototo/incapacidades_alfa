"""
Tests para el endpoint de descarga pública de documentos.

Verifica que usuarios SIN AUTENTICACIÓN puedan descargar documentos públicos
asociados a incapacidades.
"""
import pytest
from uuid import uuid4, UUID
from datetime import date, datetime
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.models.incapacidad import Incapacidad
from apps.backend.app.models.documento import Documento
from apps.backend.app.models.empresa import Empresa
from apps.backend.app.models.empleado import Empleado
from apps.backend.app.models.afiliado import Afiliado
from apps.backend.app.models.usuario import Usuario
from apps.backend.app.utils.enums import (
    TipoIncapacidad,
    EstadoIncapacidad,
    TipoDocumentoArchivo,
    Prioridad,
    EstadoEmpleado,
    EstadoAfiliado,
    EstadoEmpresa,
    TipoDocumento,
    Genero,
    RolUsuario,
    EstadoUsuario
)


@pytest.fixture
async def test_empresa_descarga(db_session: AsyncSession) -> Empresa:
    """Fixture para empresa de prueba."""
    empresa = Empresa(
        nit="900123456",
        razon_social="Empresa Test Descarga SA",
        direccion="Calle 123 #45-67",
        ciudad="Bogotá",
        telefono="3001234567",
        email_contacto="[email protected]",
        estado=EstadoEmpresa.ACTIVA
    )
    db_session.add(empresa)
    await db_session.commit()
    await db_session.refresh(empresa)
    return empresa


@pytest.fixture
async def test_empleado_descarga(
    db_session: AsyncSession,
    test_empresa_descarga: Empresa
) -> Empleado:
    """Fixture para empleado de prueba."""
    empleado = Empleado(
        empresa_id=test_empresa_descarga.id,
        tipo_documento=TipoDocumento.CC,
        numero_documento="1234567890",
        nombres="Juan Carlos",
        apellidos="Pérez García",
        fecha_nacimiento=date(1990, 5, 15),
        fecha_ingreso=date(2020, 1, 15),
        genero=Genero.M,
        email="[email protected]",
        telefono="3109876543",
        cargo="Operario",
        salario_base=Decimal("2500000.00"),
        estado=EstadoEmpleado.ACTIVO
    )
    db_session.add(empleado)
    await db_session.commit()
    await db_session.refresh(empleado)
    return empleado


@pytest.fixture
async def test_usuario_descarga(db_session: AsyncSession) -> Usuario:
    """Fixture para usuario de prueba."""
    usuario = Usuario(
        username="test_descarga",
        email="[email protected]",
        password_hash="$2b$12$test",
        nombre_completo="Usuario Test Descarga",
        rol=RolUsuario.ADMIN,
        estado=EstadoUsuario.ACTIVO
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    return usuario


@pytest.fixture
async def test_incapacidad_descarga(
    db_session: AsyncSession,
    test_empresa_descarga: Empresa,
    test_empleado_descarga: Empleado,
    test_usuario_descarga: Usuario
) -> Incapacidad:
    """Fixture para incapacidad de prueba."""
    incapacidad = Incapacidad(
        numero="INC-DESCARGA-001",
        empleado_id=test_empleado_descarga.id,
        empresa_id=test_empresa_descarga.id,
        tipo=TipoIncapacidad.ARL,
        fecha_inicio=date(2026, 1, 15),
        fecha_fin=date(2026, 1, 20),
        dias_totales=6,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Lumbago no especificado",
        valor_dia=Decimal("150000.00"),
        valor_total=Decimal("900000.00"),
        estado=EstadoIncapacidad.RADICADA,
        fecha_radicacion=datetime.utcnow(),
        radicado_por_id=test_usuario_descarga.id,
        prioridad=Prioridad.NORMAL,
        eps="EPS Test"
    )
    db_session.add(incapacidad)
    await db_session.commit()
    await db_session.refresh(incapacidad)
    return incapacidad


@pytest.fixture
async def test_documento_publico(
    db_session: AsyncSession,
    test_incapacidad_descarga: Incapacidad,
    test_usuario_descarga: Usuario
) -> Documento:
    """Fixture para documento público (INCAPACIDAD_MEDICA)."""
    documento = Documento(
        incapacidad_id=test_incapacidad_descarga.id,
        tipo_documento=TipoDocumentoArchivo.INCAPACIDAD_MEDICA,
        nombre_original="incapacidad_medica.pdf",
        nombre_archivo="incapacidad_medica_123.pdf",
        ruta_storage="documentos/incapacidad_medica_123.pdf",
        bucket="documentos",
        mime_type="application/pdf",
        tamanio_bytes=45000,
        hash_md5="abc123def456",
        hash_sha256="sha256hash123",
        uploaded_by_id=test_usuario_descarga.id,
        validado=True
    )
    db_session.add(documento)
    await db_session.commit()
    await db_session.refresh(documento)
    return documento


@pytest.fixture
async def test_documento_cedula(
    db_session: AsyncSession,
    test_incapacidad_descarga: Incapacidad,
    test_usuario_descarga: Usuario
) -> Documento:
    """Fixture para documento público (CEDULA)."""
    documento = Documento(
        incapacidad_id=test_incapacidad_descarga.id,
        tipo_documento=TipoDocumentoArchivo.CEDULA,
        nombre_original="cedula.pdf",
        nombre_archivo="cedula_123.pdf",
        ruta_storage="documentos/cedula_123.pdf",
        bucket="documentos",
        mime_type="application/pdf",
        tamanio_bytes=12000,
        hash_md5="cedula123",
        hash_sha256="sha256cedula",
        uploaded_by_id=test_usuario_descarga.id,
        validado=True
    )
    db_session.add(documento)
    await db_session.commit()
    await db_session.refresh(documento)
    return documento


@pytest.fixture
async def test_documento_no_publico(
    db_session: AsyncSession,
    test_incapacidad_descarga: Incapacidad,
    test_usuario_descarga: Usuario
) -> Documento:
    """Fixture para documento NO público (SOPORTE_PAGO)."""
    documento = Documento(
        incapacidad_id=test_incapacidad_descarga.id,
        tipo_documento=TipoDocumentoArchivo.SOPORTE_PAGO,
        nombre_original="soporte_pago.pdf",
        nombre_archivo="soporte_pago_123.pdf",
        ruta_storage="documentos/soporte_pago_123.pdf",
        bucket="documentos",
        mime_type="application/pdf",
        tamanio_bytes=25000,
        hash_md5="soporte123",
        hash_sha256="sha256soporte",
        uploaded_by_id=test_usuario_descarga.id,
        validado=True
    )
    db_session.add(documento)
    await db_session.commit()
    await db_session.refresh(documento)
    return documento


# ========== TESTS ==========

@pytest.mark.asyncio
async def test_descarga_documento_publico_exitosa(
    client: AsyncClient,
    db_session: AsyncSession,
    test_incapacidad_descarga: Incapacidad,
    test_documento_publico: Documento
):
    """
    Test 1: Happy path - Descarga exitosa de documento público.
    
    Verifica que se puede descargar un documento INCAPACIDAD_MEDICA
    sin autenticación y que la respuesta contiene una URL válida.
    """
    response = await client.get(
        f"/api/v1/incapacidades/{test_incapacidad_descarga.numero}/documentos/{test_documento_publico.id}/download"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validar estructura de respuesta
    assert "url" in data
    assert "expires_in" in data
    assert "nombre_archivo" in data
    assert "tipo_documento" in data
    
    # Validar valores
    assert data["expires_in"] == 900  # 15 minutos
    assert data["nombre_archivo"] == "incapacidad_medica_123.pdf"
    assert data["tipo_documento"] == TipoDocumentoArchivo.INCAPACIDAD_MEDICA.value
    
    # Validar que la URL contiene elementos esperados
    assert "documentos/incapacidad_medica_123.pdf" in data["url"]


@pytest.mark.asyncio
async def test_descarga_documento_cedula_exitosa(
    client: AsyncClient,
    db_session: AsyncSession,
    test_incapacidad_descarga: Incapacidad,
    test_documento_cedula: Documento
):
    """
    Test 2: Descarga exitosa de documento público tipo CEDULA.
    
    Verifica que los documentos de tipo CEDULA también son descargables.
    """
    response = await client.get(
        f"/api/v1/incapacidades/{test_incapacidad_descarga.numero}/documentos/{test_documento_cedula.id}/download"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["expires_in"] == 900
    assert data["nombre_archivo"] == "cedula_123.pdf"
    assert data["tipo_documento"] == TipoDocumentoArchivo.CEDULA.value
    assert "url" in data


@pytest.mark.asyncio
async def test_descarga_documento_publico_incapacidad_no_existe(
    client: AsyncClient,
    db_session: AsyncSession,
    test_documento_publico: Documento
):
    """
    Test 3: Error 404 cuando la incapacidad no existe.
    
    Verifica que retorna 404 si el número de radicación es inválido.
    """
    numero_invalido = "INC-NOEXISTE-999"
    
    response = await client.get(
        f"/api/v1/incapacidades/{numero_invalido}/documentos/{test_documento_publico.id}/download"
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert numero_invalido in data["detail"]


@pytest.mark.asyncio
async def test_descarga_documento_publico_documento_no_existe(
    client: AsyncClient,
    db_session: AsyncSession,
    test_incapacidad_descarga: Incapacidad
):
    """
    Test 4: Error 404 cuando el documento no existe.
    
    Verifica que retorna 404 si el ID del documento es inválido.
    """
    documento_id_invalido = uuid4()
    
    response = await client.get(
        f"/api/v1/incapacidades/{test_incapacidad_descarga.numero}/documentos/{documento_id_invalido}/download"
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert str(documento_id_invalido) in data["detail"]


@pytest.mark.asyncio
async def test_descarga_documento_publico_documento_no_pertenece(
    client: AsyncClient,
    db_session: AsyncSession,
    test_incapacidad_descarga: Incapacidad,
    test_usuario_descarga: Usuario
):
    """
    Test 5: Error 403 cuando el documento no pertenece a la incapacidad.
    
    Verifica que no se puede descargar un documento de otra incapacidad.
    """
    # Crear otra incapacidad
    otra_incapacidad = Incapacidad(
        numero="INC-OTRA-001",
        empleado_id=test_incapacidad_descarga.empleado_id,
        empresa_id=test_incapacidad_descarga.empresa_id,
        tipo=TipoIncapacidad.ARL,
        fecha_inicio=date(2026, 1, 21),
        fecha_fin=date(2026, 1, 25),
        dias_totales=5,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Test",
        valor_dia=Decimal("100000.00"),
        valor_total=Decimal("500000.00"),
        estado=EstadoIncapacidad.RADICADA,
        fecha_radicacion=datetime.utcnow(),
        radicado_por_id=test_usuario_descarga.id,
        prioridad=Prioridad.NORMAL,
        eps="EPS Test"
    )
    db_session.add(otra_incapacidad)
    
    # Crear documento que pertenece a otra_incapacidad
    otro_documento = Documento(
        incapacidad_id=otra_incapacidad.id,
        tipo_documento=TipoDocumentoArchivo.INCAPACIDAD_MEDICA,
        nombre_original="otro_doc.pdf",
        nombre_archivo="otro_doc_123.pdf",
        ruta_storage="documentos/otro_doc_123.pdf",
        bucket="documentos",
        mime_type="application/pdf",
        tamanio_bytes=30000,
        hash_md5="otro123",
        hash_sha256="sha256otro",
        uploaded_by_id=test_usuario_descarga.id,
        validado=True
    )
    db_session.add(otro_documento)
    await db_session.commit()
    await db_session.refresh(otra_incapacidad)
    await db_session.refresh(otro_documento)
    
    # Intentar descargar otro_documento usando el número de test_incapacidad_descarga
    response = await client.get(
        f"/api/v1/incapacidades/{test_incapacidad_descarga.numero}/documentos/{otro_documento.id}/download"
    )
    
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "no pertenece" in data["detail"].lower()


@pytest.mark.asyncio
async def test_descarga_documento_no_publico(
    client: AsyncClient,
    db_session: AsyncSession,
    test_incapacidad_descarga: Incapacidad,
    test_documento_no_publico: Documento
):
    """
    Test 6: Error 403 cuando el documento no es público.
    
    Verifica que documentos tipo SOPORTE_PAGO no son descargables sin auth.
    """
    response = await client.get(
        f"/api/v1/incapacidades/{test_incapacidad_descarga.numero}/documentos/{test_documento_no_publico.id}/download"
    )
    
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "no es público" in data["detail"].lower()


@pytest.mark.asyncio
async def test_presigned_url_valida(
    client: AsyncClient,
    db_session: AsyncSession,
    test_incapacidad_descarga: Incapacidad,
    test_documento_publico: Documento
):
    """
    Test 7: Verificar formato y expiración de URL pre-firmada.
    
    Valida que la URL generada tenga el formato correcto y expire en 15 minutos.
    """
    response = await client.get(
        f"/api/v1/incapacidades/{test_incapacidad_descarga.numero}/documentos/{test_documento_publico.id}/download"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validar que la URL contiene la ruta del storage
    assert test_documento_publico.ruta_storage in data["url"]
    
    # Validar expiración
    assert data["expires_in"] == 900
    
    # Validar que la URL es válida (comienza con http)
    assert data["url"].startswith("http")
    
    # Validar que contiene el bucket correcto
    assert "documentos" in data["url"].lower()


@pytest.mark.asyncio
async def test_descarga_multiples_documentos_publicos(
    client: AsyncClient,
    db_session: AsyncSession,
    test_incapacidad_descarga: Incapacidad,
    test_documento_publico: Documento,
    test_documento_cedula: Documento
):
    """
    Test 8: Descarga de múltiples documentos públicos de la misma incapacidad.
    
    Verifica que se pueden generar URLs para varios documentos.
    """
    # Descargar primer documento
    response1 = await client.get(
        f"/api/v1/incapacidades/{test_incapacidad_descarga.numero}/documentos/{test_documento_publico.id}/download"
    )
    
    assert response1.status_code == 200
    data1 = response1.json()
    
    # Descargar segundo documento
    response2 = await client.get(
        f"/api/v1/incapacidades/{test_incapacidad_descarga.numero}/documentos/{test_documento_cedula.id}/download"
    )
    
    assert response2.status_code == 200
    data2 = response2.json()
    
    # Validar que son URLs diferentes
    assert data1["url"] != data2["url"]
    assert data1["nombre_archivo"] != data2["nombre_archivo"]
    assert data1["tipo_documento"] != data2["tipo_documento"]
