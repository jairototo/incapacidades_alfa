"""
Enumeraciones utilizadas en el sistema.
"""
from enum import Enum


class TipoIncapacidad(str, Enum):
    """Tipo de incapacidad."""
    ARL = "ARL"
    SALUD = "SALUD"


class EstadoIncapacidad(str, Enum):
    """Estado de la incapacidad en el workflow."""
    RADICADA = "RADICADA"
    EN_AUDITORIA = "EN_AUDITORIA"
    PENDIENTE = "PENDIENTE"
    CREACION_SINIESTRO = "CREACION_SINIESTRO"
    LIQUIDACION = "LIQUIDACION"
    LIQUIDACION_PARCIAL = "LIQUIDACION_PARCIAL"
    GLOSADA = "GLOSADA"
    PAGADA = "PAGADA"
    PAGADA_PARCIAL = "PAGADA_PARCIAL"


class Prioridad(str, Enum):
    """Prioridad de la incapacidad."""
    BAJA = "BAJA"
    NORMAL = "NORMAL"
    ALTA = "ALTA"
    URGENTE = "URGENTE"


class EstadoEmpresa(str, Enum):
    """Estado de la empresa."""
    ACTIVA = "ACTIVA"
    INACTIVA = "INACTIVA"
    SUSPENDIDA = "SUSPENDIDA"


class TipoEmpresa(str, Enum):
    """Tipo de empresa."""
    ARL = "ARL"
    SALUD = "SALUD"
    MIXTO = "MIXTO"


class EstadoEmpleado(str, Enum):
    """Estado del empleado."""
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    RETIRADO = "RETIRADO"


class EstadoAfiliado(str, Enum):
    """Estado del afiliado."""
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    SUSPENDIDO = "SUSPENDIDO"


class TipoPoliza(str, Enum):
    """Tipo de póliza de salud."""
    INDIVIDUAL = "INDIVIDUAL"
    FAMILIAR = "FAMILIAR"
    COLECTIVA = "COLECTIVA"


class TipoDocumento(str, Enum):
    """Tipo de documento de identidad."""
    CC = "CC"
    CE = "CE"
    TI = "TI"
    PASAPORTE = "PASAPORTE"
    PEP = "PEP"


class Genero(str, Enum):
    """Género."""
    M = "M"
    F = "F"
    O = "O"


class RolUsuario(str, Enum):
    """Roles de usuario."""
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"
    APROBADOR = "APROBADOR"
    EMPRESA = "EMPRESA"
    EMPLEADO = "EMPLEADO"
    READONLY = "READONLY"


class EstadoUsuario(str, Enum):
    """Estado del usuario."""
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    BLOQUEADO = "BLOQUEADO"


class TipoDocumentoAdjunto(str, Enum):
    """Tipo de documento adjunto."""
    INCAPACIDAD_MEDICA = "INCAPACIDAD_MEDICA"
    CEDULA = "CEDULA"
    HISTORIA_CLINICA = "HISTORIA_CLINICA"
    SOPORTE_PAGO = "SOPORTE_PAGO"
    OTROS = "OTROS"


# Alias para compatibilidad con modelo Documento
TipoDocumentoArchivo = TipoDocumentoAdjunto


class EstadoOrdenPago(str, Enum):
    """Estado de la orden de pago."""
    GENERADA = "GENERADA"
    APROBADA = "APROBADA"
    EN_PROCESO = "EN_PROCESO"
    PAGADA = "PAGADA"
    RECHAZADA = "RECHAZADA"
    ANULADA = "ANULADA"


class TipoBeneficiario(str, Enum):
    """Tipo de beneficiario de pago."""
    EMPLEADO = "EMPLEADO"
    EMPRESA = "EMPRESA"
    IPS = "IPS"
    AFILIADO = "AFILIADO"


# Alias para compatibilidad con modelo OrdenPago
BeneficiarioTipo = TipoBeneficiario


class MetodoPago(str, Enum):
    """Método de pago."""
    TRANSFERENCIA = "TRANSFERENCIA"
    CHEQUE = "CHEQUE"
    EFECTIVO = "EFECTIVO"


class TipoCuenta(str, Enum):
    """Tipo de cuenta bancaria."""
    AHORROS = "AHORROS"
    CORRIENTE = "CORRIENTE"


class SyncSource(str, Enum):
    """Fuente de sincronización."""
    API = "API"
    CSV = "CSV"
    EXCEL = "EXCEL"
    MANUAL = "MANUAL"


class AccionAuditoria(str, Enum):
    """Acciones de auditoría."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CAMBIO_ESTADO = "CAMBIO_ESTADO"
    UPLOAD_FILE = "UPLOAD_FILE"
    DOWNLOAD_FILE = "DOWNLOAD_FILE"
    EXPORT_DATA = "EXPORT_DATA"


class TipoSiniestro(str, Enum):
    """Tipo de siniestro laboral."""
    ACCIDENTE_TRABAJO = "ACCIDENTE_TRABAJO"
    ENFERMEDAD_LABORAL = "ENFERMEDAD_LABORAL"
    ACCIDENTE_TRAYECTO = "ACCIDENTE_TRAYECTO"


class GravedadSiniestro(str, Enum):
    """Gravedad del siniestro."""
    LEVE = "LEVE"
    MODERADO = "MODERADO"
    GRAVE = "GRAVE"
    MORTAL = "MORTAL"


class EstadoSiniestro(str, Enum):
    """Estado del siniestro."""
    REPORTADO = "REPORTADO"
    EN_INVESTIGACION = "EN_INVESTIGACION"
    CERRADO = "CERRADO"
    ANULADO = "ANULADO"


class MetodoPagoLiquidacion(str, Enum):
    """Método de pago para liquidación de incapacidades.

    CHEQUE: Pago mediante cheque físico.
    OXIRRE: Pago mediante plataforma Oxirre (transferencia electrónica gestionada por aseguradora).

    Nota (C2): La lista de entidades que pagan por CHEQUE vs OXIRRE está pendiente
    de confirmación con el cliente. El campo se muestra en el formulario pero aún
    no hay validación contra esa lista.
    """

    CHEQUE = "CHEQUE"
    OXIRRE = "OXIRRE"
