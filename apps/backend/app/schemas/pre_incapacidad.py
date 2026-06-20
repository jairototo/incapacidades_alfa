"""
Schemas Pydantic para PreIncapacidad y PreDocumento.
Validaciones de formato únicamente — sin búsquedas en BD.
"""
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

# Import for validation inconsistencies response
from app.schemas.validation_inconsistencia import ValidationInconsistenciaRead
# Fuente única de verdad compartida con la validación masiva/auditoría.
from app.utils.validacion_incapacidad import REGEX_CIE10 as _REGEX_CIE10, TIPOS_ENFERMEDAD


# ── Enums como literales ───────────────────────────────────────────────────────

TIPOS_DOCUMENTO = ["CC", "CE", "PA", "TI"]
TIPOS_DOCUMENTO_ARCHIVO = ["INCAPACIDAD_MEDICA", "HISTORIA_CLINICA", "SOPORTE_ADICIONAL"]
ESTADOS_PRE_INCAPACIDAD = ["PENDIENTE", "PROCESADA", "RECHAZADA", "ERROR", "DEVUELTA"]

_REGEX_SOLO_LETRAS = re.compile(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-']+$")
_REGEX_REGISTRO_MEDICO = re.compile(r"^[a-zA-Z0-9\-]+$")
_REGEX_NIT = re.compile(r"^\d{6,15}(-\d)?$")


# ── Sub-schemas ────────────────────────────────────────────────────────────────

class SolicitanteData(BaseModel):
    correo: EmailStr = Field(..., description="Correo electrónico del solicitante")
    nombres: str = Field(..., min_length=2, max_length=100)
    apellidos: Optional[str] = Field(None, min_length=2, max_length=100)
    telefono: Optional[str] = Field(None, min_length=7, max_length=20)

    @field_validator("nombres", "apellidos", mode="before")
    @classmethod
    def validar_solo_letras(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not _REGEX_SOLO_LETRAS.match(v):
            raise ValueError("Solo se permiten letras, espacios y guiones")
        return v

    @field_validator("telefono", mode="before")
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        if not v.isdigit():
            raise ValueError("El teléfono solo debe contener dígitos")
        return v


class EmpresaData(BaseModel):
    """Datos de empresa — opcionales. Si no se proveen, se asume trabajador independiente."""
    nit: Optional[str] = Field(None, max_length=20, description="NIT de la empresa")
    nombre: Optional[str] = Field(None, min_length=2, max_length=255)

    @field_validator("nit", mode="before")
    @classmethod
    def validar_nit(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        if not _REGEX_NIT.match(v):
            raise ValueError("Formato de NIT inválido (ej: 900123456-1)")
        return v


class EmpleadoData(BaseModel):
    tipo_documento: str = Field(..., description="CC | CE | PA | TI")
    numero_documento: str = Field(..., min_length=6, max_length=20)
    nombres: str = Field(..., min_length=2, max_length=100)
    apellidos: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, min_length=10, max_length=10)

    @field_validator("tipo_documento")
    @classmethod
    def validar_tipo_documento(cls, v: str) -> str:
        if v not in TIPOS_DOCUMENTO:
            raise ValueError(f"Tipo de documento debe ser uno de: {TIPOS_DOCUMENTO}")
        return v

    @field_validator("numero_documento", mode="before")
    @classmethod
    def validar_numero_documento(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit():
            raise ValueError("El número de documento solo debe contener dígitos")
        return v

    @field_validator("nombres", "apellidos", mode="before")
    @classmethod
    def validar_solo_letras(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not _REGEX_SOLO_LETRAS.match(v):
            raise ValueError("Solo se permiten letras, espacios y guiones")
        return v

    @field_validator("telefono", mode="before")
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        if not v.isdigit():
            raise ValueError("El teléfono solo debe contener dígitos")
        return v


class DatosIncapacidadData(BaseModel):
    tipo_enfermedad: str = Field(..., description="ACCIDENTE_TRABAJO | ENFERMEDAD_LABORAL | ACCIDENTE_TRAYECTO")
    fecha_inicio: date
    fecha_fin: date
    diagnostico_cie10: str = Field(..., max_length=10)
    descripcion_diagnostico: Optional[str] = Field(None, max_length=500)
    nombre_medico: str = Field(..., min_length=2, max_length=200)
    registro_medico: str = Field(..., min_length=3, max_length=50)
    ips: Optional[str] = Field(None, max_length=255)
    valor_dia: Optional[Decimal] = Field(None, ge=0)
    observaciones: Optional[str] = Field(None, max_length=1000)

    @field_validator("tipo_enfermedad")
    @classmethod
    def validar_tipo_enfermedad(cls, v: str) -> str:
        if v not in TIPOS_ENFERMEDAD:
            raise ValueError(f"Tipo de enfermedad debe ser uno de: {TIPOS_ENFERMEDAD}")
        return v

    @field_validator("diagnostico_cie10")
    @classmethod
    def validar_cie10(cls, v: str) -> str:
        v = v.strip().upper()
        if not _REGEX_CIE10.match(v):
            raise ValueError("Formato CIE-10 inválido (ej: A00 o A00.1)")
        return v

    @field_validator("registro_medico")
    @classmethod
    def validar_registro_medico(cls, v: str) -> str:
        v = v.strip()
        if not _REGEX_REGISTRO_MEDICO.match(v):
            raise ValueError("El registro médico solo permite letras, números y guiones")
        return v

    @model_validator(mode="after")
    def validar_fechas(self) -> "DatosIncapacidadData":
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de fin debe ser mayor o igual a la fecha de inicio")
        return self


# ── Schema principal de creación ───────────────────────────────────────────────

class PreIncapacidadCreate(BaseModel):
    """
    Payload que recibe el endpoint público de radicación.
    Solo ARL. Sin IDs de BD — datos planos de texto.
    """
    solicitante: SolicitanteData
    empresa: Optional[EmpresaData] = Field(
        None,
        description="Datos de empresa. Si se omite, se asume trabajador independiente."
    )
    empleado: EmpleadoData
    incapacidad: DatosIncapacidadData


# ── Schemas de respuesta ───────────────────────────────────────────────────────

class PreDocumentoResponse(BaseModel):
    id: UUID
    tipo_documento: str
    nombre_original: str
    tamanio_bytes: int
    estado_subida: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PreIncapacidadResponse(BaseModel):
    id: UUID
    numero_radicacion: int
    estado: str
    tipo: str
    # Solicitante
    solicitante_correo: str
    solicitante_nombres: str
    # Empleado
    empleado_tipo_documento: str
    empleado_numero_documento: str
    empleado_nombres: str
    # Incapacidad
    tipo_enfermedad: str
    fecha_inicio: date
    fecha_fin: date
    dias_totales: int
    diagnostico_cie10: str
    nombre_medico: str
    registro_medico: str
    # Empresa
    empresa_nit: Optional[str] = None
    empresa_nombre: Optional[str] = None
    # Vínculo a la incapacidad creada (set after unified job runs)
    incapacidad_id: Optional[UUID] = None
    # Documentos
    documentos: List[PreDocumentoResponse] = []
    # Validation issues found during promotion
    validation_inconsistencias: List[ValidationInconsistenciaRead] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class PreIncapacidadRadicadaResponse(BaseModel):
    """Respuesta mínima tras una radicación exitosa."""
    id: UUID
    numero_radicacion: int
    estado: str
    mensaje: str = "Radicación recibida exitosamente. Será procesada en breve."

    model_config = {"from_attributes": True}


class PreIncapacidadPromotionResponse(BaseModel):
    """Response para radicación exitosa con promoción encolada."""
    numero_radicacion: int
    estado: str  # "PENDIENTE"
    validation_enqueued: bool
    mensaje: str = "Radicación recibida. Procesamiento iniciado."

    model_config = {"from_attributes": True}


# ── Internal schemas (requires authentication) ─────────────────────────────────

class PreIncapacidadListItem(BaseModel):
    """Fila resumida para la bandeja interna."""
    id: UUID
    numero_radicacion: int
    estado: str
    tipo: str
    empleado_nombres: str
    empleado_numero_documento: str
    empresa_nit: Optional[str]
    empresa_nombre: Optional[str]
    fecha_inicio: date
    fecha_fin: date
    dias_totales: int
    total_errores: int = 0
    total_warnings: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class PreIncapacidadUpdate(BaseModel):
    """Campos editables por el usuario interno para corregir datos."""
    empresa_nit: Optional[str] = None
    empresa_nombre: Optional[str] = None
    empleado_tipo_documento: Optional[str] = None
    empleado_numero_documento: Optional[str] = None
    empleado_nombres: Optional[str] = None
    empleado_apellidos: Optional[str] = None
    empleado_email: Optional[str] = None
    tipo_enfermedad: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    diagnostico_cie10: Optional[str] = None
    descripcion_diagnostico: Optional[str] = None
    nombre_medico: Optional[str] = None
    registro_medico: Optional[str] = None
    ips: Optional[str] = None
    valor_dia: Optional[Decimal] = None


class DevolucionRequest(BaseModel):
    """Cuerpo del request para devolver una pre-incapacidad."""
    motivo: str = Field(..., min_length=20, max_length=2000,
                        description="Motivo de devolución (mínimo 20 caracteres)")


class DevolucionResponse(BaseModel):
    """Respuesta de la operación de devolución."""
    id: UUID
    estado: str
    motivo_devolucion: str
    email_enviado: bool


class PromocionResponse(BaseModel):
    """Respuesta de la operación de promoción manual."""
    success: bool
    pre_incapacidad_id: UUID
    incapacidad_id: Optional[UUID] = None
    errors: int
    warnings: int
    message: str
