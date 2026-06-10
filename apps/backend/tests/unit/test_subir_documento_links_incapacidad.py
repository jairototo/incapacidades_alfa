"""
Unit tests for PreIncapacidadService.subir_documento() —
specifically the new behaviour that links a Documento to the already-promoted
incapacidad when pre_incapacidad.incapacidad_id is set.
"""
import io
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4

import pytest

from app.services.pre_incapacidad_service import PreIncapacidadService
from app.models.pre_incapacidad import PreIncapacidad
from app.models.pre_documento import PreDocumento
from app.models.documento import Documento


def _make_pre_inc(incapacidad_id=None) -> PreIncapacidad:
    m = MagicMock(spec=PreIncapacidad)
    m.id = uuid4()
    m.incapacidad_id = incapacidad_id
    return m


def _make_pre_doc(tipo_documento="INCAPACIDAD_MEDICA") -> PreDocumento:
    m = MagicMock(spec=PreDocumento)
    m.id = uuid4()
    m.tipo_documento = tipo_documento
    m.nombre_original = "incapacidad.pdf"
    m.ruta_storage = "pre-documentos/2026/06/abc.pdf"
    m.bucket = "incapacidades"
    m.mime_type = "application/pdf"
    m.tamanio_bytes = 12345
    return m


@pytest.fixture
def service():
    db = AsyncMock()
    db.add = MagicMock()   # session.add() is synchronous in SQLAlchemy
    db.flush = AsyncMock()
    svc = PreIncapacidadService.__new__(PreIncapacidadService)
    svc.db = db
    svc.repo = MagicMock()
    svc.doc_repo = MagicMock()
    svc.storage = MagicMock()
    return svc


@pytest.mark.asyncio
async def test_subir_documento_no_incapacidad_linked_does_not_create_documento(service):
    """When incapacidad_id is None, no Documento row should be added."""
    pre_inc = _make_pre_inc(incapacidad_id=None)
    pre_doc = _make_pre_doc()

    service.repo.get_by_id_with_documentos = AsyncMock(return_value=pre_inc)
    service.doc_repo.create = AsyncMock(return_value=pre_doc)
    service.storage.upload_file = MagicMock(
        return_value=("pre-documentos/2026/06/abc.pdf", "md5", "sha256", 12345)
    )

    result = await service.subir_documento(
        pre_incapacidad_id=pre_inc.id,
        file_data=io.BytesIO(b"fake pdf content"),
        filename="incapacidad.pdf",
        content_type="application/pdf",
        tipo_documento="INCAPACIDAD_MEDICA",
    )

    assert result is pre_doc
    # db.add should NOT have been called (no Documento to link)
    service.db.add.assert_not_called()
    service.db.flush.assert_not_called()


@pytest.mark.asyncio
async def test_subir_documento_with_incapacidad_linked_creates_documento(service):
    """When incapacidad_id is set, a Documento linked to the incapacidad is added."""
    incapacidad_id = uuid4()
    pre_inc = _make_pre_inc(incapacidad_id=incapacidad_id)
    pre_doc = _make_pre_doc(tipo_documento="INCAPACIDAD_MEDICA")

    service.repo.get_by_id_with_documentos = AsyncMock(return_value=pre_inc)
    service.doc_repo.create = AsyncMock(return_value=pre_doc)
    service.storage.upload_file = MagicMock(
        return_value=("pre-documentos/2026/06/abc.pdf", "md5", "sha256", 12345)
    )

    result = await service.subir_documento(
        pre_incapacidad_id=pre_inc.id,
        file_data=io.BytesIO(b"fake pdf content"),
        filename="incapacidad.pdf",
        content_type="application/pdf",
        tipo_documento="INCAPACIDAD_MEDICA",
    )

    assert result is pre_doc
    # db.add should have been called once with a Documento
    service.db.add.assert_called_once()
    added_obj = service.db.add.call_args[0][0]
    assert isinstance(added_obj, Documento)
    assert added_obj.incapacidad_id == incapacidad_id
    assert added_obj.ruta_storage == pre_doc.ruta_storage
    assert added_obj.nombre_original == pre_doc.nombre_original
    assert added_obj.validado is False
    service.db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_subir_documento_tipo_map_historia_clinica(service):
    """HISTORIA_CLINICA maps to TipoDocumentoArchivo.HISTORIA_CLINICA."""
    from app.utils.enums import TipoDocumentoArchivo
    incapacidad_id = uuid4()
    pre_inc = _make_pre_inc(incapacidad_id=incapacidad_id)
    pre_doc = _make_pre_doc(tipo_documento="HISTORIA_CLINICA")

    service.repo.get_by_id_with_documentos = AsyncMock(return_value=pre_inc)
    service.doc_repo.create = AsyncMock(return_value=pre_doc)
    service.storage.upload_file = MagicMock(
        return_value=("pre-documentos/2026/06/abc.pdf", "md5", "sha256", 5000)
    )

    await service.subir_documento(
        pre_incapacidad_id=pre_inc.id,
        file_data=io.BytesIO(b"pdf"),
        filename="historia.pdf",
        content_type="application/pdf",
        tipo_documento="HISTORIA_CLINICA",
    )

    added_obj = service.db.add.call_args[0][0]
    assert added_obj.tipo_documento == TipoDocumentoArchivo.HISTORIA_CLINICA


@pytest.mark.asyncio
async def test_subir_documento_tipo_map_soporte_adicional_becomes_otros(service):
    """SOPORTE_ADICIONAL (not in enum) falls back to TipoDocumentoArchivo.OTROS."""
    from app.utils.enums import TipoDocumentoArchivo
    incapacidad_id = uuid4()
    pre_inc = _make_pre_inc(incapacidad_id=incapacidad_id)
    pre_doc = _make_pre_doc(tipo_documento="SOPORTE_ADICIONAL")

    service.repo.get_by_id_with_documentos = AsyncMock(return_value=pre_inc)
    service.doc_repo.create = AsyncMock(return_value=pre_doc)
    service.storage.upload_file = MagicMock(
        return_value=("pre-documentos/2026/06/abc.pdf", "md5", "sha256", 7000)
    )

    await service.subir_documento(
        pre_incapacidad_id=pre_inc.id,
        file_data=io.BytesIO(b"pdf"),
        filename="soporte.pdf",
        content_type="application/pdf",
        tipo_documento="SOPORTE_ADICIONAL",
    )

    added_obj = service.db.add.call_args[0][0]
    assert added_obj.tipo_documento == TipoDocumentoArchivo.OTROS


@pytest.mark.asyncio
async def test_subir_documento_storage_error_skips_incapacidad_link(service):
    """When storage upload fails (estado_subida=ERROR), no Documento is created."""
    incapacidad_id = uuid4()
    pre_inc = _make_pre_inc(incapacidad_id=incapacidad_id)
    pre_doc = _make_pre_doc()

    service.repo.get_by_id_with_documentos = AsyncMock(return_value=pre_inc)
    service.doc_repo.create = AsyncMock(return_value=pre_doc)
    # Simulate storage failure
    service.storage.upload_file = MagicMock(side_effect=OSError("disk full"))

    result = await service.subir_documento(
        pre_incapacidad_id=pre_inc.id,
        file_data=io.BytesIO(b"pdf"),
        filename="incapacidad.pdf",
        content_type="application/pdf",
        tipo_documento="INCAPACIDAD_MEDICA",
    )

    assert result is pre_doc
    # Storage failed → estado_subida=ERROR → must NOT link to incapacidad
    service.db.add.assert_not_called()
