"""
Schemas Pydantic para Incapacidad.

Soporta dos tipos:
- ARL: Requiere empleado_id y empresa_id, puede tener siniestro
- SALUD: Requiere afiliado_id, no tiene empleado/empresa/siniestro
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Any, Dict
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator

from app.utils.enums import TipoIncapacidad, EstadoIncapacidad, Prioridad


class IncapacidadBase(BaseModel):
    """Schema base de Incapacidad."""
    tipo: TipoIncapacidad
    subtipo: Optional[str] = None
    fecha_inicio: date
    fecha_fin: date
    diagnostico_cie10: Optional[str] = Field(None, max_length=10)
    descripcion_diagnostico: Optional[str] = None
    nombre_medico: Optional[str] = Field(None, max_length=200, description="Nombre del médico tratante")
    registro_medico: Optional[str] = Field(None, max_length=50, description="Registro médico profesional")
    eps: Optional[str] = Field(None, max_length=255)
    ips: Optional[str] = Field(None, max_length=255)
    valor_dia: Optional[Decimal] = Field(None, ge=0, description="Valor por día de incapacidad")
    valor_total: Optional[Decimal] = Field(None, ge=0, description="Valor total de la incapacidad")
    observaciones: Optional[str] = None
    prioridad: Prioridad = Prioridad.NORMAL
    
    @field_validator("fecha_fin")
    @classmethod
    def validate_fechas(cls, v, info):
        if "fecha_inicio" in info.data and v < info.data["fecha_inicio"]:
            raise ValueError("fecha_fin debe ser mayor o igual a fecha_inicio")
        return v


class IncapacidadARLCreate(IncapacidadBase):
    """Schema para crear incapacidad de tipo ARL (empleado de empresa)."""
    tipo: TipoIncapacidad = Field(default=TipoIncapacidad.ARL, frozen=True)
    empleado_id: UUID = Field(..., description="ID del empleado")
    empresa_id: UUID = Field(..., description="ID de la empresa")
    solicitante_id: Optional[UUID] = Field(None, description="ID del solicitante")
    siniestro_id: Optional[UUID] = Field(None, description="ID del siniestro laboral")
    numero_siniestro: Optional[str] = Field(None, max_length=50, description="Número del siniestro")


class IncapacidadSaludCreate(IncapacidadBase):
    """Schema para crear incapacidad de tipo SALUD (afiliado con póliza)."""
    tipo: TipoIncapacidad = Field(default=TipoIncapacidad.SALUD, frozen=True)
    afiliado_id: UUID = Field(..., description="ID del afiliado con póliza")
    solicitante_id: Optional[UUID] = Field(None, description="ID del solicitante")


class IncapacidadCreate(IncapacidadBase):
    """Schema genérico para crear incapacidad (valida tipo)."""
    empleado_id: Optional[UUID] = Field(None, description="ID del empleado (requerido para ARL)")
    empresa_id: Optional[UUID] = Field(None, description="ID de la empresa (requerido para ARL)")
    afiliado_id: Optional[UUID] = Field(None, description="ID del afiliado (requerido para SALUD)")
    solicitante_id: Optional[UUID] = Field(None, description="ID del solicitante")
    siniestro_id: Optional[UUID] = Field(None, description="ID del siniestro (opcional para ARL)")
    numero_siniestro: Optional[str] = Field(None, max_length=50, description="Número del siniestro")
    
    @model_validator(mode='after')
    def validate_tipo_relacion(self):
        """Valida que los campos requeridos estén presentes según el tipo."""
        if self.tipo == TipoIncapacidad.ARL:
            if not self.empleado_id or not self.empresa_id:
                raise ValueError("empleado_id y empresa_id son obligatorios para incapacidades de tipo ARL")
            if self.afiliado_id:
                raise ValueError("afiliado_id no debe estar presente en incapacidades de tipo ARL")
        elif self.tipo == TipoIncapacidad.SALUD:
            if not self.afiliado_id:
                raise ValueError("afiliado_id es obligatorio para incapacidades de tipo SALUD")
            if self.empleado_id or self.empresa_id or self.siniestro_id or self.numero_siniestro:
                raise ValueError("empleado_id, empresa_id y siniestro no deben estar presentes en incapacidades de tipo SALUD")
        return self


class IncapacidadUpdate(BaseModel):
    """Schema para actualizar incapacidad."""
    siniestro_id: Optional[UUID] = None
    numero_siniestro: Optional[str] = None
    subtipo: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    diagnostico_cie10: Optional[str] = None
    descripcion_diagnostico: Optional[str] = None
    eps: Optional[str] = None
    ips: Optional[str] = None
    observaciones: Optional[str] = None
    prioridad: Optional[Prioridad] = None


class IncapacidadAuditar(BaseModel):
    """Schema para auditar incapacidad."""
    accion: str = Field(..., description="SOLICITAR_INFORMACION, APROBAR_PARA_PAGO, RECHAZAR")
    observaciones: str = Field(..., min_length=10)
    
    @field_validator("accion")
    @classmethod
    def validate_accion(cls, v):
        acciones_validas = ["SOLICITAR_INFORMACION", "APROBAR_PARA_PAGO", "RECHAZAR"]
        if v not in acciones_validas:
            raise ValueError(f"Acción debe ser una de: {', '.join(acciones_validas)}")
        return v


class IncapacidadResponder(BaseModel):
    """Schema para responder observaciones."""
    respuesta: str = Field(..., min_length=10)


class EmpleadoSimple(BaseModel):
    """Schema simplificado de empleado."""
    id: UUID
    nombre_completo: str
    documento: str
    
    model_config = {"from_attributes": True}


class AfiliadoSimple(BaseModel):
    """Schema simplificado de afiliado."""
    id: UUID
    nombre_completo: str
    numero_poliza: str
    documento: str
    
    model_config = {"from_attributes": True}


class EmpresaSimple(BaseModel):
    """Schema simplificado de empresa."""
    id: UUID
    razon_social: str
    nit: str
    
    model_config = {"from_attributes": True}


class UsuarioSimple(BaseModel):
    """Schema simplificado de usuario."""
    id: UUID
    nombre_completo: str
    rol: str
    
    model_config = {"from_attributes": True}


class DocumentoSimple(BaseModel):
    """Schema simplificado de documento."""
    id: UUID
    tipo_documento: str
    nombre_archivo: str
    mime_type: str
    tamanio_bytes: int
    created_at: datetime
    download_url: str
    
    model_config = {"from_attributes": True}


class HistorialEstadoSchema(BaseModel):
    """Schema de historial de estado."""
    estado_anterior: Optional[str]
    estado_nuevo: str
    observacion: Optional[str]
    cambiado_por: str
    fecha: datetime
    
    model_config = {"from_attributes": True}


class IncapacidadInDB(IncapacidadBase):
    """Schema de incapacidad completa desde DB."""
    id: UUID
    numero: str
    empleado_id: Optional[UUID]
    empresa_id: Optional[UUID]
    afiliado_id: Optional[UUID]
    solicitante_id: Optional[UUID]
    siniestro_id: Optional[UUID]
    numero_siniestro: Optional[str]
    dias_totales: int
    valor_dia: Optional[Decimal]
    valor_total: Optional[Decimal]
    estado: EstadoIncapacidad
    motivo_rechazo: Optional[str]
    radicado_por_id: Optional[UUID]
    auditado_por_id: Optional[UUID]
    aprobado_por_id: Optional[UUID]
    fecha_radicacion: datetime
    fecha_auditoria: Optional[datetime]
    fecha_aprobacion: Optional[datetime]
    fecha_rechazo: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Objetos completos (se cargan con eager loading)
    empleado: Optional[Any] = None
    empresa: Optional[Any] = None
    afiliado: Optional[Any] = None
    
    model_config = {"from_attributes": True}


class SolicitanteSimple(BaseModel):
    """Schema simplificado de solicitante."""
    id: UUID
    nombre_completo: str
    correo: str
    
    model_config = {"from_attributes": True}


class IncapacidadResponse(IncapacidadInDB):
    """Schema de respuesta de incapacidad con relaciones."""
    empleado: Optional["EmpleadoSimple"] = None
    empresa: Optional["EmpresaSimple"] = None
    afiliado: Optional["AfiliadoSimple"] = None
    solicitante: Optional["SolicitanteSimple"] = None
    radicado_por: Optional["UsuarioSimple"] = None
    auditado_por: Optional["UsuarioSimple"] = None
    aprobado_por: Optional["UsuarioSimple"] = None
    documentos: list["DocumentoSimple"] = []
    historial: list["HistorialEstadoSchema"] = []
    
    model_config = {"from_attributes": True}


class IncapacidadListResponse(BaseModel):
    """Schema de lista de incapacidades."""
    id: UUID
    numero: str
    empleado: Optional["EmpleadoSimple"] = None
    empresa: Optional["EmpresaSimple"] = None
    afiliado: Optional["AfiliadoSimple"] = None
    tipo: TipoIncapacidad
    subtipo: Optional[str]
    fecha_inicio: date
    fecha_fin: date
    dias_totales: int
    diagnostico_cie10: Optional[str]
    descripcion_diagnostico: Optional[str]
    valor_total: Optional[Decimal]
    estado: EstadoIncapacidad
    prioridad: Prioridad
    fecha_radicacion: datetime
    radicado_por: Optional[str]
    total_documentos: int
    
    model_config = {"from_attributes": True}


class IncapacidadPendienteResponse(IncapacidadInDB):
    """
    Schema para incapacidad pendiente de auditoría con datos adicionales.
    Incluye días desde radicación y días en estado actual.
    
    Nota: Las relaciones (empleado, empresa, afiliado) deben cargarse
    mediante eager loading en el service layer.
    """
    dias_desde_radicacion: int = Field(..., description="Días desde que fue radicada")
    dias_en_estado_actual: int = Field(..., description="Días en el estado actual")
    
    model_config = {"from_attributes": True}


class IncapacidadDetalleResponse(IncapacidadInDB):
    """
    Schema de respuesta detallada con objetos completos de relaciones.
    
    Para uso en el endpoint GET /incapacidades/{incapacidad_id}
    Incluye objetos completos en lugar de solo IDs:
    - empleado: EmpleadoResponse completo
    - empresa: EmpresaResponse completo
    - afiliado: AfiliadoResponse completo
    - siniestros_empleado: Lista de siniestros del empleado (para ARL)
    """
    # Objetos completos en lugar de IDs (usando Any para evitar imports circulares)
    empleado: Optional[Any] = Field(None, description="Objeto empleado completo (para tipo ARL)")
    empresa: Optional[Any] = Field(None, description="Objeto empresa completo (para tipo ARL)")
    afiliado: Optional[Any] = Field(None, description="Objeto afiliado completo (para tipo SALUD)")
    
    # Lista de siniestros del empleado (solo para ARL)
    siniestros_empleado: List[Any] = Field(
        default_factory=list,
        description="Lista de todos los siniestros del empleado (solo para tipo ARL)"
    )
    
    model_config = {"from_attributes": True}


class EstadisticasIncapacidades(BaseModel):
    """Schema de estadísticas de incapacidades."""
    
    class Resumen(BaseModel):
        total_incapacidades: int
        total_dias: int
        valor_total: Decimal
        promedio_dias: float
    
    class PorMes(BaseModel):
        mes: str
        total: int
        valor: Decimal
    
    class TopEmpresa(BaseModel):
        empresa: str
        nit: str
        total: int
        valor: Decimal
    
    resumen: Resumen
    por_estado: dict[str, int]
    por_tipo: dict[str, int]
    por_mes: list[PorMes]
    top_empresas: list[TopEmpresa]


# ========== SCHEMAS PARA CONSULTA PÚBLICA (SIN AUTENTICACIÓN) ==========

class HistorialEstadoSimple(BaseModel):
    """Versión simplificada del historial para consulta pública."""
    estado: EstadoIncapacidad
    fecha_cambio: datetime
    observaciones: Optional[str] = None
    
    model_config = {"from_attributes": True}


class DocumentoPublico(BaseModel):
    """Información básica de documento para consulta pública."""
    id: UUID
    nombre_archivo: str
    tipo_documento: str
    tamanio_kb: int
    fecha_upload: datetime
    
    model_config = {"from_attributes": True}


class ConsultaIncapacidadPublicResponse(BaseModel):
    """
    Response para consulta pública de incapacidad.
    
    NOTA IMPORTANTE: Esta respuesta NO incluye datos sensibles como:
    - Salarios o valores monetarios
    - Cuentas bancarias
    - Diagnósticos médicos detallados (solo código CIE-10)
    - Datos personales completos de auditores
    - IDs de usuarios internos
    """
    # Identificación
    numero: str = Field(..., description="Número de radicación único")
    
    # Estado y tipo
    estado: EstadoIncapacidad = Field(..., description="Estado actual")
    tipo: TipoIncapacidad = Field(..., description="ARL o SALUD")
    
    # Fechas de la incapacidad
    fecha_inicio: date = Field(..., description="Fecha de inicio de incapacidad")
    fecha_fin: date = Field(..., description="Fecha de fin de incapacidad")
    dias_totales: int = Field(..., description="Días totales de incapacidad")
    
    # Datos del solicitante (sanitizados)
    nombre_completo: str = Field(..., description="Nombre completo del solicitante")
    tipo_documento: str = Field(..., description="Tipo de documento (sin número)")
    
    # Información médica básica (sanitizada)
    diagnostico_cie10: Optional[str] = Field(None, description="Código CIE-10 del diagnóstico")
    descripcion_diagnostico: Optional[str] = Field(None, description="Descripción general del diagnóstico")
    eps: Optional[str] = Field(None, description="EPS del solicitante")
    
    # Timeline de estados
    historial_estados: List[HistorialEstadoSimple] = Field(
        default_factory=list,
        description="Historial de cambios de estado ordenado cronológicamente"
    )
    
    # Documentos descargables
    documentos: List[DocumentoPublico] = Field(
        default_factory=list,
        description="Lista de documentos adjuntos (solo públicos)"
    )
    
    # Observaciones públicas (si existen)
    observaciones_publicas: Optional[str] = Field(
        None,
        description="Observaciones visibles para el solicitante (solo si está OBSERVADA)"
    )
    
    # Metadata
    created_at: datetime = Field(..., description="Fecha de radicación")
    updated_at: datetime = Field(..., description="Última actualización")
    
    model_config = {"from_attributes": True}


class IncapacidadStatsResponse(BaseModel):
    """Estadísticas del dashboard de incapacidades."""
    pendientes: int = Field(..., description="Incapacidades en RADICADA o EN_AUDITORIA")
    auditadas_hoy: int = Field(..., description="Incapacidades auditadas hoy (APROBADA/RECHAZADA/OBSERVADA)")
    proximas_vencer: int = Field(..., description="Incapacidades con >7 días sin cambio de estado")
    rechazadas_observadas: int = Field(..., description="Incapacidades en RECHAZADA u OBSERVADA")
    
    # Metadata opcional
    fecha_calculo: datetime = Field(default_factory=datetime.utcnow)
    filtros_aplicados: Optional[Dict[str, Any]] = None
    
    model_config = {"from_attributes": True}


# ========== SCHEMAS PARA ESTADÍSTICAS EXTENDIDAS ==========

class TopEmpresaStats(BaseModel):
    """Top empresa por radicaciones."""
    empresa_id: UUID
    razon_social: str
    nit: str
    total_incapacidades: int
    valor_total: Decimal
    
    model_config = {"from_attributes": True}


class TopCIE10Stats(BaseModel):
    """Top diagnóstico CIE-10."""
    codigo_cie10: str
    descripcion: str
    total_incapacidades: int
    porcentaje: float  # % sobre el total
    
    model_config = {"from_attributes": True}


class TopEmpleadoStats(BaseModel):
    """Empleado con más días de incapacidad."""
    empleado_id: UUID
    nombres: str
    apellidos: str
    numero_documento: str
    empresa_razon_social: str
    total_dias: int
    total_incapacidades: int
    
    model_config = {"from_attributes": True}


class DistribucionEstados(BaseModel):
    """Distribución de incapacidades por estado."""
    estado: EstadoIncapacidad
    cantidad: int
    porcentaje: float
    
    model_config = {"from_attributes": True}


class DistribucionTipos(BaseModel):
    """Distribución de incapacidades por tipo."""
    tipo: TipoIncapacidad
    cantidad: int
    valor_total: Decimal
    promedio_dias: float
    
    model_config = {"from_attributes": True}


class TendenciaMensual(BaseModel):
    """Tendencia mensual de radicaciones."""
    mes: str  # formato: "2026-01"
    radicadas: int
    aprobadas: int
    rechazadas: int
    valor_total_aprobado: Decimal
    
    model_config = {"from_attributes": True}


class IncapacidadStatsExtendedResponse(BaseModel):
    """Estadísticas extendidas del dashboard con datos para gráficos."""
    # Métricas básicas (mantener compatibilidad)
    pendientes: int
    auditadas_hoy: int
    proximas_vencer: int
    rechazadas_observadas: int
    
    # Datos para gráficos
    top_empresas: List[TopEmpresaStats]
    top_diagnosticos: List[TopCIE10Stats]
    top_empleados: List[TopEmpleadoStats]
    distribucion_estados: List[DistribucionEstados]
    distribucion_tipos: List[DistribucionTipos]
    tendencia_mensual: List[TendenciaMensual]
    
    # Metadata
    fecha_calculo: datetime = Field(default_factory=datetime.utcnow)
    filtros_aplicados: Optional[Dict[str, Any]] = None
    
    model_config = {"from_attributes": True}
