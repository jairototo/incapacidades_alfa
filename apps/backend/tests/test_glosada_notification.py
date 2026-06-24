"""
Tests for Task 6.1: GLOSADA email + PDF notification.

Test plan:
1. Unit: _generar_pdf_glosa returns valid PDF bytes (no DB needed)
2. Unit: notificar_glosada stores Documento and skips email when SMTP unconfigured
3. Integration: reenviar endpoint returns 200 for GLOSADA incapacidad
4. Integration: reenviar endpoint returns 400 for non-GLOSADA incapacidad
5. Integration: auditar RECHAZAR triggers notificacion (document created in DB)
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.utils.enums import EstadoIncapacidad, TipoIncapacidad, Prioridad


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_incapacidad_arl(test_empresa):
    """Minimal mock Incapacidad ARL — no DB needed for unit tests."""
    inc = MagicMock()
    inc.id = uuid4()
    inc.numero = "INC-ARL-20260624-0001"
    inc.tipo = TipoIncapacidad.ARL
    inc.estado = EstadoIncapacidad.GLOSADA
    inc.fecha_inicio = date(2026, 6, 1)
    inc.fecha_fin = date(2026, 6, 10)
    inc.dias_totales = 10
    inc.diagnostico_cie10 = "M545"
    inc.descripcion_diagnostico = "Lumbago no especificado"
    inc.motivo_rechazo = "Documentación insuficiente"

    # Empresa
    empresa = MagicMock()
    empresa.razon_social = "Empresa Test SAS"
    empresa.email_contacto = "contacto@empresa.com"
    inc.empresa = empresa

    # Empleado
    empleado = MagicMock()
    empleado.nombres = "Juan Carlos"
    empleado.apellidos = "Pérez González"
    inc.empleado = empleado

    inc.afiliado = None
    return inc


@pytest.fixture
def mock_incapacidad_salud():
    """Minimal mock Incapacidad SALUD — no DB needed for unit tests."""
    inc = MagicMock()
    inc.id = uuid4()
    inc.numero = "INC-SAL-20260624-0001"
    inc.tipo = TipoIncapacidad.SALUD
    inc.estado = EstadoIncapacidad.GLOSADA
    inc.fecha_inicio = date(2026, 6, 1)
    inc.fecha_fin = date(2026, 6, 10)
    inc.dias_totales = 10
    inc.diagnostico_cie10 = "A048"
    inc.descripcion_diagnostico = "Enfermedad intestinal"
    inc.motivo_rechazo = "Período ya cubierto"

    # No empresa
    inc.empresa = None

    # Afiliado
    afiliado = MagicMock()
    afiliado.nombres = "María Fernanda"
    afiliado.apellidos = "López García"
    afiliado.email = "maria.lopez@test.com"
    inc.afiliado = afiliado
    inc.empleado = None

    return inc


@pytest.fixture
def mock_incapacidad_no_email():
    """Incapacidad sin email en empresa ni afiliado."""
    inc = MagicMock()
    inc.id = uuid4()
    inc.numero = "INC-ARL-NO-EMAIL-001"
    inc.tipo = TipoIncapacidad.ARL
    inc.estado = EstadoIncapacidad.GLOSADA
    inc.fecha_inicio = date(2026, 6, 1)
    inc.fecha_fin = date(2026, 6, 10)
    inc.dias_totales = 10
    inc.diagnostico_cie10 = "M545"

    empresa = MagicMock()
    empresa.razon_social = "Empresa Sin Email"
    empresa.email_contacto = None
    inc.empresa = empresa
    inc.afiliado = None
    inc.empleado = MagicMock()
    inc.empleado.nombres = "Test"
    inc.empleado.apellidos = "User"

    return inc


# ---------------------------------------------------------------------------
# 1. Unit: PDF generation
# ---------------------------------------------------------------------------


def test_generar_pdf_glosa_returns_valid_bytes(mock_incapacidad_arl):
    """PDF bytes must start with %PDF magic bytes and have meaningful size."""
    from app.services.glosada_notification_service import _generar_pdf_glosa

    pdf = _generar_pdf_glosa(mock_incapacidad_arl, "Documentación insuficiente")

    assert isinstance(pdf, bytes)
    assert len(pdf) > 100, "PDF debe tener contenido sustancial"
    assert pdf[:4] == b"%PDF", "PDF debe iniciar con magic bytes %PDF"


def test_generar_pdf_glosa_salud(mock_incapacidad_salud):
    """PDF también funciona para incapacidades SALUD (sin empresa)."""
    from app.services.glosada_notification_service import _generar_pdf_glosa

    pdf = _generar_pdf_glosa(mock_incapacidad_salud, "Período ya cubierto")

    assert isinstance(pdf, bytes)
    assert pdf[:4] == b"%PDF"


def test_generar_pdf_glosa_sin_empleado_ni_afiliado():
    """PDF funciona cuando no hay empleado ni afiliado (no debe lanzar excepción)."""
    from app.services.glosada_notification_service import _generar_pdf_glosa

    inc = MagicMock()
    inc.numero = "INC-TEST-NONE-001"
    inc.fecha_inicio = date(2026, 6, 1)
    inc.fecha_fin = date(2026, 6, 10)
    inc.dias_totales = 10
    inc.diagnostico_cie10 = "M545"
    inc.empresa = None
    inc.empleado = None
    inc.afiliado = None

    pdf = _generar_pdf_glosa(inc, "Motivo de prueba")
    assert isinstance(pdf, bytes)
    assert pdf[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# 2. Unit: _resolver_destinatario
# ---------------------------------------------------------------------------


def test_resolver_destinatario_usa_empresa(mock_incapacidad_arl):
    from app.services.glosada_notification_service import _resolver_destinatario

    dest = _resolver_destinatario(mock_incapacidad_arl)
    assert dest == "contacto@empresa.com"


def test_resolver_destinatario_usa_afiliado_cuando_no_hay_empresa(mock_incapacidad_salud):
    from app.services.glosada_notification_service import _resolver_destinatario

    dest = _resolver_destinatario(mock_incapacidad_salud)
    assert dest == "maria.lopez@test.com"


def test_resolver_destinatario_returns_none_sin_email(mock_incapacidad_no_email):
    from app.services.glosada_notification_service import _resolver_destinatario

    dest = _resolver_destinatario(mock_incapacidad_no_email)
    assert dest is None


# ---------------------------------------------------------------------------
# 3. Unit: notificar_glosada — guarda documento, omite email sin SMTP
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_notificar_glosada_guarda_documento_sin_smtp(mock_incapacidad_arl):
    """
    Cuando SMTP no está configurado, notificar_glosada debe:
    - generar el PDF
    - guardar el Documento (flush al DB)
    - NO lanzar excepción
    """
    from app.services import glosada_notification_service

    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    # Simulate no existing glosa document (first call = new insert path)
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=execute_result)

    with patch("app.services.glosada_notification_service.settings") as mock_settings:
        mock_settings.SMTP_USER = None
        mock_settings.SMTP_PASSWORD = None
        mock_settings.SMTP_TLS = True

        # No debe lanzar excepción
        await glosada_notification_service.notificar_glosada(
            db, mock_incapacidad_arl, "Documentación insuficiente"
        )

    # Verificar que se añadió un documento
    db.add.assert_called_once()
    db.flush.assert_called_once()

    # Verificar que el documento tiene los datos correctos
    documento_guardado = db.add.call_args[0][0]
    from app.models.documento import Documento
    assert isinstance(documento_guardado, Documento)
    assert documento_guardado.nombre_archivo == f"glosa_{mock_incapacidad_arl.numero}.pdf"
    assert documento_guardado.mime_type == "application/pdf"
    assert documento_guardado.tamanio_bytes > 0


@pytest.mark.asyncio
async def test_notificar_glosada_sin_email_disponible_no_falla(mock_incapacidad_no_email):
    """Cuando no hay email, debe guardar documento pero no intentar enviar email."""
    from app.services import glosada_notification_service

    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    # Simulate no existing glosa document
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=execute_result)

    with patch("app.services.glosada_notification_service.settings") as mock_settings:
        mock_settings.SMTP_USER = "user@example.com"
        mock_settings.SMTP_PASSWORD = "secret"
        mock_settings.SMTP_TLS = True

        # No debe lanzar excepción
        await glosada_notification_service.notificar_glosada(
            db, mock_incapacidad_no_email, "Motivo prueba"
        )

    # El documento SÍ se guarda aunque no haya email
    db.add.assert_called_once()


# ---------------------------------------------------------------------------
# 4. Integration: reenviar endpoint — 200 for GLOSADA
# ---------------------------------------------------------------------------


@pytest.fixture
async def incapacidad_glosada(db_session, test_empleado, test_empresa):
    """Incapacidad en estado GLOSADA con empresa que tiene email."""
    from app.models.incapacidad import Incapacidad

    inc = Incapacidad(
        numero="INC-ARL-GLOSADA-001",
        empleado_id=test_empleado.id,
        empresa_id=test_empresa.id,
        tipo=TipoIncapacidad.ARL,
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 10),
        dias_totales=10,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Lumbago no especificado",
        valor_dia=Decimal("100000.00"),
        valor_total=Decimal("1000000.00"),
        estado=EstadoIncapacidad.GLOSADA,
        fecha_radicacion=datetime.utcnow(),
        fecha_rechazo=datetime.utcnow(),
        motivo_rechazo="Documentación insuficiente para este período",
        prioridad=Prioridad.NORMAL,
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


@pytest.fixture
async def incapacidad_en_auditoria_for_reenviar(db_session, test_empleado, test_empresa):
    """Incapacidad en EN_AUDITORIA — no debe poder reenviar glosa."""
    from app.models.incapacidad import Incapacidad

    inc = Incapacidad(
        numero="INC-ARL-AUDITORIA-002",
        empleado_id=test_empleado.id,
        empresa_id=test_empresa.id,
        tipo=TipoIncapacidad.ARL,
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 10),
        dias_totales=10,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Lumbago",
        valor_dia=Decimal("100000.00"),
        valor_total=Decimal("1000000.00"),
        estado=EstadoIncapacidad.EN_AUDITORIA,
        fecha_radicacion=datetime.utcnow(),
        prioridad=Prioridad.NORMAL,
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


@pytest.mark.asyncio
async def test_reenviar_notificacion_glosada_200(
    client, incapacidad_glosada, admin_token_headers
):
    """POST /incapacidades/{id}/reenviar-notificacion-glosada devuelve 200."""
    with patch(
        "app.services.glosada_notification_service.notificar_glosada",
        new_callable=AsyncMock,
    ):
        response = await client.post(
            f"/api/v1/incapacidades/{incapacidad_glosada.id}/reenviar-notificacion-glosada",
            headers=admin_token_headers,
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "ok"
    assert body["numero"] == incapacidad_glosada.numero


@pytest.mark.asyncio
async def test_reenviar_notificacion_no_glosada_400(
    client, incapacidad_en_auditoria_for_reenviar, admin_token_headers
):
    """POST reenviar devuelve 400 cuando el estado no es GLOSADA."""
    response = await client.post(
        f"/api/v1/incapacidades/{incapacidad_en_auditoria_for_reenviar.id}/reenviar-notificacion-glosada",
        headers=admin_token_headers,
    )

    assert response.status_code == 400, response.text


# ---------------------------------------------------------------------------
# 5. Integration: auditar RECHAZAR → documento de glosa creado en DB
# ---------------------------------------------------------------------------


@pytest.fixture
async def incapacidad_arl_en_auditoria_con_siniestro(
    db_session, test_empleado, test_empresa
):
    """Incapacidad ARL en EN_AUDITORIA con siniestro asociado (requerido para GLOSADA)."""
    from app.models.incapacidad import Incapacidad
    from app.models.siniestro import Siniestro
    from app.utils.enums import TipoSiniestro, GravedadSiniestro, EstadoSiniestro

    siniestro = Siniestro(
        numero_siniestro="SIN-TEST-GLOSA-001",
        empleado_id=test_empleado.id,
        empresa_id=test_empresa.id,
        tipo_siniestro=TipoSiniestro.ACCIDENTE_TRABAJO,
        gravedad=GravedadSiniestro.LEVE,
        estado=EstadoSiniestro.REPORTADO,
        fecha_siniestro=date(2026, 5, 31),
        descripcion="Accidente de prueba para glosa",
    )
    db_session.add(siniestro)
    await db_session.flush()

    inc = Incapacidad(
        numero="INC-ARL-AUDIT-GLOSA-001",
        empleado_id=test_empleado.id,
        empresa_id=test_empresa.id,
        siniestro_id=siniestro.id,
        tipo=TipoIncapacidad.ARL,
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 10),
        dias_totales=10,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Lumbago no especificado",
        valor_dia=Decimal("100000.00"),
        valor_total=Decimal("1000000.00"),
        estado=EstadoIncapacidad.EN_AUDITORIA,
        fecha_radicacion=datetime.utcnow(),
        prioridad=Prioridad.NORMAL,
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


@pytest.mark.asyncio
async def test_auditar_rechazar_crea_documento_glosa(
    db_session, incapacidad_arl_en_auditoria_con_siniestro, test_usuario
):
    """
    Cuando auditar_incapacidad recibe accion=RECHAZAR, debe:
    1. Cambiar estado a GLOSADA
    2. Crear un Documento con nombre glosa_{numero}.pdf
    """
    from app.services.incapacidad_service import incapacidad_service
    from app.models.documento import Documento
    from sqlalchemy import select

    inc_id = incapacidad_arl_en_auditoria_con_siniestro.id
    numero = incapacidad_arl_en_auditoria_con_siniestro.numero

    # Patch SMTP para que no intente enviar email real
    with patch("app.services.glosada_notification_service.settings") as mock_smtp:
        mock_smtp.SMTP_USER = None
        mock_smtp.SMTP_PASSWORD = None
        mock_smtp.SMTP_TLS = True

        incapacidad_actualizada = await incapacidad_service.auditar_incapacidad(
            db=db_session,
            incapacidad_id=inc_id,
            accion="RECHAZAR",
            observaciones="Documentación insuficiente para validar el período de incapacidad",
            usuario_id=test_usuario.id,
        )

    assert incapacidad_actualizada.estado == EstadoIncapacidad.GLOSADA

    # Verificar que se creó el documento de glosa
    result = await db_session.execute(
        select(Documento).where(
            Documento.incapacidad_id == inc_id,
            Documento.nombre_archivo == f"glosa_{numero}.pdf",
        )
    )
    doc = result.scalar_one_or_none()
    assert doc is not None, "Debe existir un documento de glosa en la DB"
    assert doc.mime_type == "application/pdf"
    assert doc.tamanio_bytes > 0
    assert doc.hash_md5 is not None
    assert doc.hash_sha256 is not None
