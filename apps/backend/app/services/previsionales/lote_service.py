"""
Servicio de carga de lotes previsionales (Task 3.1).

Primer orquestador real del modulo previsionales: conecta la logica pura de
Fase 1 (`segmentacion.py`, `liquidacion_previsional.py`, `excel_common.py`,
`auditoria_rules.py`, `arpis_export.py`) con la persistencia de Fase 2
(modelos y repositorios `app/db/repositories/previsionales/`).

Flujo de `cargar_lote`:
    desprotege -> valida encabezados criticos -> crea LotePrevisional ->
    por fila: parsea (tolerante, nunca aborta el lote) -> segmenta ->
    liquida -> persiste IncapacidadPrevisional + PeriodoPrevisional ->
    cruza referencia entre filas del lote (`agrupar_repetidas`,
    `encadenar_prorrogas`) -> archiva el libro original en storage ->
    UN SOLO `db.commit()` al final.

Mapeo de columnas A-AA de la hoja FORMALIZACION -> campos, verificado esta
sesion contra el workbook real de produccion
(`docs/recursos_previsionales/Copy_RADICADOS_AUDITORIA_20260706.xlsx`):

    A  = (Junio, consecutivo -- IGNORADA, encabezado espurio)
    B  = # IDENTIFICACION            -> identificacion
    C  = RADICADO                    -> radicado
    D  = FECHA RADICACION AFP        -> fecha_radicacion_afp
    E  = TIPO INGRESO                -> tipo_ingreso
    F  = FECHA_INICIAL               -> fecha_inicial
    G  = FECHA_FINAL                 -> fecha_final
    H  = No. DIAS                    -> informativa, no se persiste aparte
                                         (los periodos ya traen `dias`)
    I  = DIAS ACUMULADOS             -> metadata_["dias_acumulados"]
    J  = DIAGNOSTICOS                -> primer CIE10 -> cie10 (ver nota abajo)
    K  = IBC                         -> multivalor -> periodos[].ibc
    L  = SALARIO                     -> multivalor -> periodos[].salario
    M  = DIAS COTIZADOS              -> multivalor -> periodos[].dias_cotizados
    N  = FECHA DIA 181               -> dia_181_afp
    O  = FECHA DIA 360               -> IGNORADA (informativa, dia 540 =
                                         dia_181 + 359 ya cierra el debate,
                                         ver auditoria_rules.py)
    P  = VALOR                       -> valor_afp
    Q  = FECHA RADICACION ASEGURADORA -> metadata_["fecha_radicacion_aseguradora"]
    R  = ASEGURADORA                 -> metadata_["aseguradora"]
    S  = ESTADO AFILIADO             -> metadata_["estado_afiliado"]
    T  = DIA 181 ALFA                -> sin poblar (campo de auditor)
    U  = FECHA CRIE ALFA             -> sin poblar (campo de auditor)
    V  = OBSERVACIÓN ALFA            -> sin poblar (campo de auditor)
    W  = OBSERVACIÓN PORVENIR        -> observacion (ver nota abajo)
    X  = VALOR PAGADO                -> sin poblar (etapa de pago)
    Y  = FECHA DE PAGO ASEGURADORA   -> sin poblar (etapa de pago)
    Z  = INSTANCIA JUDICIAL          -> metadata_["instancia_judicial"]
    AA = OBSERVACION JURIDICA        -> metadata_["observacion_juridica"]

DECISIONES DE MAPEO (documentadas tambien en el reporte de la tarea):

1. `cie10` es una columna escalar pero la fuente trae codigos separados por
   "-". Siguiendo el precedente de `arpis_export.construir_libro_arpis`
   ("solo se usa el primero"), se guarda unicamente el primer codigo. El
   string crudo completo se conserva en `metadata_["diagnosticos_raw"]`.
2. `dia_181_alfa`/`dia_181_arpis` se dejan sin poblar a proposito -- los
   llena un auditor humano (alfa) o el cruce con SOLICITUDES (Task 3.2),
   ninguno de los cuales es parte de esta tarea.
3. Columnas AFP sin columna dedicada en `IncapacidadPrevisional`
   (dias_acumulados, fecha_radicacion_aseguradora, aseguradora,
   estado_afiliado, instancia_judicial, observacion_juridica) se guardan en
   `metadata_` (JSONB heredado de `BaseModel`) en vez de perderse.
4. La columna W ("OBSERVACIÓN PORVENIR") se mapea al campo `observacion`
   del modelo -- es el campo mas cercano semanticamente ("Observación AFP
   cruda, fuente de 'Rad No. ' cuando el radicado no es numérico", ver
   `arpis_export.normalizar_radicado`). No hay evidencia directa en los
   datos de muestra (todas las filas revisadas traen radicado numerico, por
   lo que W nunca se ejercito en la practica) -- si resulta incorrecto,
   es trivial de corregir en un solo lugar (`_parsear_fila`).
5. `tipo_identificacion` y `fecha_radicacion_alfa` no tienen columna fuente
   en FORMALIZACION (A-AA) y se dejan sin poblar.
6. `LotePrevisional` no tiene una columna dedicada para la ruta del archivo
   original en storage -- se usa `metadata_["archivo_original_path"]`.
"""
import io
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from loguru import logger
from sqlalchemy import String
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage_core import storage_backend
from app.db.repositories.previsionales import (
    incapacidad_previsional_repository,
    lote_previsional_repository,
    periodo_previsional_repository,
)
from app.db.repositories.smlmv_parametros_repository import smlmv_parametros_repository
from app.models.previsionales.incapacidad_previsional import IncapacidadPrevisional
from app.models.previsionales.lote_previsional import LotePrevisional
from app.services.previsionales.arpis_export import normalizar_radicado
from app.services.previsionales.auditoria_rules import agrupar_repetidas, encadenar_prorrogas
from app.services.previsionales.excel_common import (
    CeldaInvalidaError,
    es_vacio,
    parse_decimal,
    parse_entero,
    parse_fecha,
    parse_radicado,
    texto,
    validar_encabezados,
)
from app.services.previsionales.liquidacion_previsional import calcular_valor
from app.services.previsionales.lote_excel_reader import (
    cargar_hoja_desde_bytes_planos,
    descifrar_si_aplica,
)
from app.services.previsionales.segmentacion import (
    ConteoSegmentosError,
    parear_segmentos,
    segmentar,
    split_multivalor,
)

# ---------------------------------------------------------------------------
# Mapeo unico columna -> campo (ver docstring del modulo)
# ---------------------------------------------------------------------------

COLUMNAS_FORMALIZACION: dict[str, str] = {
    "B": "identificacion",
    "C": "radicado",
    "D": "fecha_radicacion_afp",
    "E": "tipo_ingreso",
    "F": "fecha_inicial",
    "G": "fecha_final",
    "H": "dias",
    "I": "dias_acumulados",
    "J": "diagnosticos",
    "K": "ibc_raw",
    "L": "salario_raw",
    "M": "dias_cotizados_raw",
    "N": "dia_181_afp",
    "O": "fecha_dia_360",
    "P": "valor_afp",
    "Q": "fecha_radicacion_aseguradora",
    "R": "aseguradora",
    "S": "estado_afiliado",
    "W": "observacion",
    "Z": "instancia_judicial",
    "AA": "observacion_juridica",
}

# Solo estas columnas son criticas para el negocio -- las demas se leen
# best-effort, sin bloquear la carga si su encabezado no coincide.
_ENCABEZADOS_CRITICOS: dict[str, str] = {
    "B": "# IDENTIFICACION",
    "C": "RADICADO",
    "D": "FECHA RADICACION AFP",
    "E": "TIPO INGRESO",
    "F": "FECHA_INICIAL",
    "G": "FECHA_FINAL",
    "H": "No. DIAS",
    "K": "IBC",
    "L": "SALARIO",
    "M": "DIAS COTIZADOS",
    "N": "FECHA DIA 181",
    "P": "VALOR",
}

_FILA_ENCABEZADO = 1
_PRIMERA_FILA_DATOS = 2

_TIPOS_INGRESO_VALIDOS = {"INICIAL", "PRORROGA", "TUTELA_I", "TUTELA_P", "AJUSTE"}

_CONTENT_TYPE_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_STORAGE_FOLDER = "lotes_previsionales"


def _col_num(letter: str) -> int:
    """Convierte una letra de columna Excel a indice 1-based (A=1, B=2, ..., AA=27)."""
    num = 0
    for ch in letter.upper():
        num = num * 26 + (ord(ch) - ord("A") + 1)
    return num


def _valor_crudo(row_values: tuple, letter: str) -> Any:
    idx = _col_num(letter) - 1
    return row_values[idx] if idx < len(row_values) else None


def _parse_tipo_ingreso(v: Any) -> str | None:
    """Normaliza (mayusculas/trim) y valida contra el CHECK constraint del modelo."""
    t = texto(v)
    if t is None:
        return None
    normalizado = t.strip().upper()
    if normalizado not in _TIPOS_INGRESO_VALIDOS:
        raise CeldaInvalidaError(
            f"Tipo de ingreso no reconocido: {t!r} "
            f"(esperado uno de {sorted(_TIPOS_INGRESO_VALIDOS)})"
        )
    return normalizado


def _decimales_a_enteros(valores: list[Decimal]) -> list[int]:
    """Convierte una lista de Decimal a int, sin truncar silenciosamente valores no enteros."""
    enteros = []
    for v in valores:
        if v != v.to_integral_value():
            raise ValueError(f"Valor no entero en DIAS COTIZADOS: {v}")
        enteros.append(int(v))
    return enteros


def _parsear_fila(row_values: tuple) -> tuple[dict, dict]:
    """
    Parsea una fila cruda de FORMALIZACION, columna por columna, de forma
    tolerante: ninguna celda invalida detiene el parseo de las demas.

    Returns:
        (datos, errores) -- `datos` trae solo los campos que se pudieron
        parsear (usar `.get(...)`); `errores` mapea nombre-de-campo ->
        mensaje, uno por cada celda que no pudo parsearse o que faltaba
        siendo requerida.
    """
    datos: dict[str, Any] = {}
    errores: dict[str, str] = {}

    def _campo(nombre: str, letter: str, parser, requerido: bool = False) -> None:
        crudo = _valor_crudo(row_values, letter)
        if es_vacio(crudo):
            if requerido:
                errores[nombre] = f"Falta {nombre} (columna {letter})"
            return
        try:
            valor = parser(crudo)
        except CeldaInvalidaError as exc:
            errores[nombre] = str(exc)
            return
        if valor is not None:
            datos[nombre] = valor

    def _campo_multivalor(nombre: str, letter: str) -> None:
        crudo = _valor_crudo(row_values, letter)
        try:
            datos[nombre] = split_multivalor(crudo)
        except (InvalidOperation, ValueError, TypeError) as exc:
            errores[nombre] = f"Valor múltiple inválido en columna {letter}: {exc}"
            datos[nombre] = []

    _campo("identificacion", "B", texto, requerido=True)
    _campo("radicado", "C", parse_radicado, requerido=True)
    _campo("fecha_radicacion_afp", "D", parse_fecha)
    _campo("tipo_ingreso", "E", _parse_tipo_ingreso)
    _campo("fecha_inicial", "F", parse_fecha, requerido=True)
    _campo("fecha_final", "G", parse_fecha, requerido=True)
    _campo("dias_acumulados", "I", parse_entero)
    _campo("diagnosticos", "J", texto)
    _campo_multivalor("ibc", "K")
    _campo_multivalor("salario", "L")
    _campo_multivalor("dias_cotizados", "M")
    _campo("dia_181_afp", "N", parse_fecha)
    _campo("valor_afp", "P", parse_decimal)
    _campo("fecha_radicacion_aseguradora", "Q", parse_fecha)
    _campo("aseguradora", "R", texto)
    _campo("estado_afiliado", "S", texto)
    _campo("observacion", "W", texto)
    _campo("instancia_judicial", "Z", texto)
    _campo("observacion_juridica", "AA", texto)

    return datos, errores


def _construir_metadata(datos: dict) -> dict | None:
    """Campos AFP sin columna dedicada en el modelo -- ver decision 3 en el docstring del módulo.

    Nota (fix round 1 / Finding 3, flagged forward -- sin cambio de codigo):
    `instancia_judicial`/`observacion_juridica` (columnas Z/AA, tutela/juridico)
    quedan aqui adentro del JSONB `metadata_` sin columna dedicada ni indice.
    Es un limite conocido de este esquema, no un descuido de esta tarea: una
    futura tarea de flujo AUDITOR_JURIDICO probablemente necesitara columnas
    propias (o un indice sobre este JSONB) si necesita filtrar/buscar por
    estado de tutela -- hoy esos dos campos son opacos para cualquier query.
    """
    fecha_rad_aseg = datos.get("fecha_radicacion_aseguradora")
    metadata = {
        "dias_acumulados": datos.get("dias_acumulados"),
        "aseguradora": datos.get("aseguradora"),
        "estado_afiliado": datos.get("estado_afiliado"),
        "fecha_radicacion_aseguradora": fecha_rad_aseg.isoformat() if fecha_rad_aseg else None,
        "instancia_judicial": datos.get("instancia_judicial"),
        "observacion_juridica": datos.get("observacion_juridica"),
        "diagnosticos_raw": datos.get("diagnosticos"),
    }
    metadata = {k: v for k, v in metadata.items() if v is not None}
    return metadata or None


def _extraer_cie10(diagnosticos_raw: str | None) -> str | None:
    if not diagnosticos_raw:
        return None
    partes = [p.strip() for p in diagnosticos_raw.split("-") if p.strip()]
    return partes[0] if partes else None


# ---------------------------------------------------------------------------
# Fix round 1 / Finding 1: reintento degradado ante fallo de BD por fila.
#
# `parse_radicado`/`normalizar_radicado` (excel_common.py, arpis_export.py)
# no acotan longitud -- un radicado anomalo (p.ej. 25 digitos) pasa el
# parseo tolerante sin error y solo revienta al hacer flush contra columnas
# `String(20)`/`String(16)` (`radicado`, `radicado_normalizado`). Este mapa
# se deriva de las columnas reales del modelo (no hardcodeado) para poder
# truncar defensivamente en el camino de reintento degradado -- pero NUNCA
# para los campos de identidad (ver Fix round 2 / Finding abajo).
#
# Fix round 2: `identificacion`, `radicado` y `radicado_normalizado` quedan
# EXCLUIDOS de todo truncamiento. Un `radicado` o una `identificacion`
# truncados no son "un best-effort aceptable" -- son un valor DISTINTO Y
# FALSO que puede referirse a una persona/reclamo equivocado para cualquier
# codigo downstream que no inspeccione `errores_carga` primero (el mismo
# principio que `arpis_export.py` ya aplica de forma explicita: nunca
# adivinar un radicado, fallar ruidosamente en su lugar). Si el flush falla
# porque alguno de estos tres campos excede su longitud de columna, la fila
# se trata como un fallo de nivel-parseo: se registra el error y NO se
# persiste ningun registro para ella (ver `_campo_identidad_excede_longitud`
# y `LotePrevisionalService._persistir_fila`).
# ---------------------------------------------------------------------------
_CAMPOS_IDENTIDAD_CRITICOS: frozenset[str] = frozenset(
    {"identificacion", "radicado", "radicado_normalizado"}
)

_LONGITUDES_MAXIMAS_STRING: dict[str, int] = {
    col.name: col.type.length
    for col in IncapacidadPrevisional.__table__.columns
    if isinstance(col.type, String) and col.type.length
}

# Subconjunto de `_LONGITUDES_MAXIMAS_STRING` que SI se puede truncar en el
# reintento degradado -- todo excepto los campos de identidad. En la
# practica hoy son columnas como `tipo_ingreso`/`cie10` (campos de bajo
# riesgo o de mapeo/clasificacion, no identificadores de persona/reclamo).
_LONGITUDES_MAXIMAS_TRUNCABLES: dict[str, int] = {
    nombre: longitud
    for nombre, longitud in _LONGITUDES_MAXIMAS_STRING.items()
    if nombre not in _CAMPOS_IDENTIDAD_CRITICOS
}


def _campo_identidad_excede_longitud(campos: dict) -> str | None:
    """Devuelve el nombre del primer campo de identidad
    (`_CAMPOS_IDENTIDAD_CRITICOS`) cuyo valor excede la longitud máxima de
    su columna, o `None` si ninguno la excede. Estos campos nunca se
    truncan -- ver nota arriba de `_LONGITUDES_MAXIMAS_STRING`."""
    for nombre in _CAMPOS_IDENTIDAD_CRITICOS:
        valor = campos.get(nombre)
        max_len = _LONGITUDES_MAXIMAS_STRING.get(nombre)
        if isinstance(valor, str) and max_len is not None and len(valor) > max_len:
            return nombre
    return None


def _truncar_campos_string(campos: dict) -> dict:
    """Copia `campos` truncando los valores string NO-IDENTITARIOS que
    excedan la longitud máxima de su columna en `IncapacidadPrevisional`
    (`_LONGITUDES_MAXIMAS_TRUNCABLES`) -- `identificacion`/`radicado`/
    `radicado_normalizado` quedan explícitamente fuera de este mapa y por lo
    tanto nunca se tocan aquí.

    Usado EXCLUSIVAMENTE como reintento degradado tras un fallo de BD en el
    intento normal (ver `LotePrevisionalService._persistir_fila`), y solo
    cuando ese fallo NO involucra un campo de identidad -- nunca se llama en
    el camino feliz, así que ningún dato se trunca en silencio salvo cuando
    la alternativa es perder la fila completa y el campo en cuestión no es
    un identificador.
    """
    truncado = dict(campos)
    for nombre, max_len in _LONGITUDES_MAXIMAS_TRUNCABLES.items():
        valor = truncado.get(nombre)
        if isinstance(valor, str) and len(valor) > max_len:
            truncado[nombre] = valor[:max_len]
    return truncado


class LotePrevisionalService:
    """Orquesta la carga completa de un lote previsional desde el excel de la AFP."""

    async def _persistir_fila(
        self,
        db: AsyncSession,
        campos_incapacidad: dict,
        periodos_data: list[dict],
        errores: dict,
    ) -> "IncapacidadPrevisional | None":
        """
        Persiste una fila (`IncapacidadPrevisional` + sus `PeriodoPrevisional`)
        dentro de un SAVEPOINT (`db.begin_nested()`), siguiendo el mismo
        patrón ya establecido en
        `RadicacionPipelineService._crear_incapacidad`
        (`app/services/radicacion_pipeline_service.py`) para aislar errores
        de BD por fila dentro de una carga masiva.

        Por qué SAVEPOINT y no un `try/except` a secas (Finding 1, fix
        round 1 de Task 3.1): un error de BD en el flush (p.ej. `DataError`
        por un campo `String(N)` que excede su longitud -- ver
        `_LONGITUDES_MAXIMAS_STRING` más arriba) dejaría la sesión en un
        estado inválido para las filas SIGUIENTES si solo se atrapara la
        excepción sin revertir nada; y un `db.rollback()` completo de la
        sesión descartaría también las filas ANTERIORES de este mismo lote
        que ya se habían flusheado con éxito (recordar: `cargar_lote` hace
        un único `db.commit()` al final, entonces todas las filas viven en
        la misma transacción externa). Un SAVEPOINT resuelve ambos
        problemas: al fallar, revierte únicamente lo que esta fila alcanzó
        a escribir, dejando intacto todo lo anterior y la sesión lista para
        la fila siguiente.

        Si el intento normal falla con `SQLAlchemyError`, el manejo se
        bifurca (Fix round 2 -- ver nota junto a `_LONGITUDES_MAXIMAS_STRING`):

        - Si el fallo involucra un campo de IDENTIDAD (`identificacion`,
          `radicado`, `radicado_normalizado` -- detectado vía
          `_campo_identidad_excede_longitud`, NO por inspeccionar el texto
          de la excepción de BD): NUNCA se reintenta con truncamiento. Un
          `radicado`/`identificacion` truncado es un valor DISTINTO Y FALSO,
          no un best-effort aceptable (mismo principio que
          `arpis_export.py` ya aplica: nunca adivinar/mutilar un radicado,
          fallar ruidosamente en su lugar). La fila se descarta sin
          persistir ningún registro -- se comporta como si fuera un error
          de nivel-parseo, no como una degradación de BD.
        - En cualquier otro caso (ningún campo de identidad involucrado): se
          reintenta UNA vez en modo degradado, truncando defensivamente
          solo los campos string NO-identitarios a su longitud máxima de
          columna (`_truncar_campos_string`) y omitiendo los
          `PeriodoPrevisional` (no hay forma genérica de saber cuál de los
          valores originales causó el error, así que se prioriza dejar un
          registro auditable de la incapacidad -- con el error de BD
          explícito en `errores_carga` -- sobre completar sus periodos). Si
          incluso ese reintento falla, la fila se descarta (se loguea) y el
          caller la trata como no persistida.
        """
        try:
            async with db.begin_nested():
                incapacidad = await incapacidad_previsional_repository.create_flushed(
                    db, campos_incapacidad
                )
                for periodo_data in periodos_data:
                    await periodo_previsional_repository.create_flushed(
                        db, {"incapacidad_id": incapacidad.id, **periodo_data}
                    )
            return incapacidad
        except SQLAlchemyError as exc:
            campo_identidad = _campo_identidad_excede_longitud(campos_incapacidad)
            if campo_identidad is not None:
                # Fix round 2: nunca truncar un campo de identidad -- la
                # fila se descarta sin persistir nada, tratada como un
                # fallo de nivel-parseo.
                logger.warning(
                    "Fallo de BD al persistir una fila del lote previsional -- "
                    f"el campo de identidad {campo_identidad!r} excede la "
                    "longitud máxima de su columna. No se trunca "
                    "(identificacion/radicado/radicado_normalizado nunca se "
                    "truncan, porque un valor truncado sería un identificador "
                    f"DISTINTO Y FALSO) -- la fila se descarta sin persistir "
                    f"ningún registro: {exc}"
                )
                errores["persistencia"] = (
                    f"No se pudo guardar la fila: el campo de identidad "
                    f"'{campo_identidad}' excede la longitud máxima permitida "
                    "de su columna. Este campo nunca se trunca (truncar "
                    "identificacion/radicado/radicado_normalizado produciría "
                    "un identificador distinto y falso), por lo que la fila "
                    f"NO se persiste. Error de BD original: {exc}"
                )
                return None

            logger.warning(
                "Fallo de BD al persistir una fila del lote previsional -- "
                "reintentando en modo degradado (solo campos no-identitarios "
                f"truncados, sin periodos): {exc}"
            )
            errores["persistencia"] = (
                "Error de base de datos al guardar la fila (persistida en modo "
                "degradado: campos no-identitarios truncados a la longitud de "
                f"columna, sin periodos): {exc}"
            )
            campos_degradados = _truncar_campos_string(campos_incapacidad)
            campos_degradados["errores_carga"] = errores
            try:
                async with db.begin_nested():
                    return await incapacidad_previsional_repository.create_flushed(
                        db, campos_degradados
                    )
            except SQLAlchemyError as exc2:
                logger.error(
                    "No se pudo persistir una fila del lote previsional ni "
                    f"siquiera en modo degradado -- fila descartada, el lote "
                    f"continúa con las demás: {exc2}"
                )
                return None

    async def cargar_lote(
        self,
        db: AsyncSession,
        file_bytes: bytes,
        password: str | None,
        nombre_archivo: str,
        usuario_id: UUID,
    ) -> LotePrevisional:
        """
        Carga un lote previsional desde el excel (posiblemente cifrado) de
        la AFP: desprotege, valida encabezados criticos, parsea/segmenta/
        liquida fila por fila (tolerante a errores por fila) y persiste
        todo en una sola transaccion.

        Args:
            db: Sesion de base de datos (el llamador NO debe commitear;
                esta funcion hace el unico `commit` de la operacion).
            file_bytes: Bytes crudos del archivo subido (cifrado o no).
            password: Contraseña del archivo, si esta cifrado.
            nombre_archivo: Nombre original del archivo (para
                `LotePrevisional.nombre_archivo` y el storage).
            usuario_id: Usuario que carga el lote.

        Returns:
            El `LotePrevisional` creado, con sus incapacidades y periodos
            ya persistidos (flush) y la transaccion commiteada.

        Raises:
            BadRequestException: contraseña faltante/incorrecta, archivo no
                es un Excel valido, hoja FORMALIZACION ausente, o
                encabezados criticos que no coinciden -- todos estos son
                fallos estructurales que abortan el lote completo ANTES de
                escribir nada en BD.
        """
        bytes_planos = descifrar_si_aplica(file_bytes, password)
        ws = cargar_hoja_desde_bytes_planos(bytes_planos)

        validar_encabezados(ws, _ENCABEZADOS_CRITICOS, fila=_FILA_ENCABEZADO)

        lote = await lote_previsional_repository.create_flushed(
            db,
            {
                "nombre_archivo": nombre_archivo,
                "cargado_por_id": usuario_id,
            },
        )

        smlmv_cache: dict[int, Decimal] = {}
        filas_procesadas: list[dict] = []

        total_filas = 0
        total_incapacidades = 0

        max_row = ws.max_row or 1
        for row_values in ws.iter_rows(
            min_row=_PRIMERA_FILA_DATOS, max_row=max_row, values_only=True
        ):
            if all(es_vacio(v) for v in row_values):
                continue

            total_filas += 1

            datos, errores = _parsear_fila(row_values)

            valor_auditado = None
            diferencia_valor_afp = None
            periodos_data: list[dict] = []

            fecha_inicial = datos.get("fecha_inicial")
            fecha_final = datos.get("fecha_final")

            if fecha_inicial is not None and fecha_final is not None:
                try:
                    segmentos = segmentar(fecha_inicial, fecha_final)
                    ibc_list = datos.get("ibc", [])
                    salario_list = datos.get("salario", [])
                    dias_cotizados_list = _decimales_a_enteros(datos.get("dias_cotizados", []))

                    pares = parear_segmentos(segmentos, ibc_list, salario_list, dias_cotizados_list)

                    anos = {seg.fecha_inicio.year for seg, *_ in pares}
                    for ano in anos:
                        if ano not in smlmv_cache:
                            params = await smlmv_parametros_repository.get_by_ano(db, ano)
                            if params is None:
                                raise ValueError(f"SMLMV no configurado para el año {ano}")
                            smlmv_cache[ano] = params.valor

                    pares_ibc = [(seg, ibc) for seg, ibc, _sal, _dc in pares]
                    valor_total, detalle = calcular_valor(pares_ibc, smlmv_cache)
                    valor_auditado = valor_total
                    if datos.get("valor_afp") is not None:
                        diferencia_valor_afp = valor_total - datos["valor_afp"]

                    for (seg, ibc, salario, dias_cot), det in zip(pares, detalle):
                        periodos_data.append(
                            {
                                "orden": seg.orden,
                                "fecha_inicio": seg.fecha_inicio,
                                "fecha_fin": seg.fecha_fin,
                                "dias": seg.dias,
                                "ibc": ibc,
                                "salario": salario,
                                "dias_cotizados": dias_cot,
                                "smlmv_aplicado": det.smlmv_aplicado,
                                "base_diaria": det.base_mensual / Decimal(30),
                                "valor_segmento": det.valor_segmento,
                            }
                        )
                except (ConteoSegmentosError, ValueError, KeyError) as exc:
                    errores["segmentacion"] = str(exc)

            radicado_normalizado = None
            if not errores.get("radicado"):
                try:
                    radicado_normalizado = normalizar_radicado(
                        datos.get("radicado") or "", datos.get("observacion")
                    )
                except ValueError as exc:
                    errores["radicado_normalizado"] = str(exc)

            cie10 = _extraer_cie10(datos.get("diagnosticos"))

            campos_incapacidad = {
                "lote_id": lote.id,
                "identificacion": datos.get("identificacion"),
                "radicado": datos.get("radicado"),
                "radicado_normalizado": radicado_normalizado,
                "tipo_ingreso": datos.get("tipo_ingreso"),
                "fecha_inicial": fecha_inicial,
                "fecha_final": fecha_final,
                "fecha_radicacion_afp": datos.get("fecha_radicacion_afp"),
                "dia_181_afp": datos.get("dia_181_afp"),
                "valor_afp": datos.get("valor_afp"),
                "cie10": cie10,
                "observacion": datos.get("observacion"),
                "valor_auditado": valor_auditado,
                "diferencia_valor_afp": diferencia_valor_afp,
                "errores_carga": errores or None,
                "metadata_": _construir_metadata(datos),
            }

            # `errores` se pasa por referencia: si `_persistir_fila` cae al
            # modo degradado, muta este mismo dict agregando la clave
            # "persistencia" -- así el `if not errores` de abajo (y
            # `errores_carga` en el propio registro) reflejan el fallo de BD
            # aunque la fila hubiera parseado perfecto a nivel de campo.
            incapacidad = await self._persistir_fila(
                db, campos_incapacidad, periodos_data, errores
            )

            if incapacidad is None:
                # `_persistir_fila` devuelve None por dos motivos (ver su
                # docstring): (a) un campo de identidad (identificacion/
                # radicado/radicado_normalizado) excede su longitud de
                # columna -- nunca se trunca, se descarta directo (Fix
                # round 2); o (b) fallo irrecuperable de BD incluso en modo
                # degradado (Finding 1, fix round 1). En ambos casos la
                # fila ya se contó en `total_filas` (leida del excel) pero
                # no queda ningun registro persistido para ella; no
                # participa en el cruce de referencia (repetidas/prorrogas)
                # porque no tiene id. El lote entero sigue sin abortar.
                continue

            if not errores:
                total_incapacidades += 1

            filas_procesadas.append(
                {
                    "id": str(incapacidad.id),
                    "identificacion": datos.get("identificacion"),
                    "fecha_inicial": fecha_inicial,
                    "fecha_final": fecha_final,
                    "tipo_ingreso": datos.get("tipo_ingreso"),
                    "_obj": incapacidad,
                }
            )

        # ------------------------------------------------------------
        # Cruce de referencia dentro del lote: repetidas + prorrogas
        # ------------------------------------------------------------
        filas_para_reglas = [
            {k: v for k, v in fila.items() if k != "_obj"} for fila in filas_procesadas
        ]
        objetos_por_id: dict[str, IncapacidadPrevisional] = {
            fila["id"]: fila["_obj"] for fila in filas_procesadas
        }

        # Fix round 1 / Finding 2: confirmado y documentado explicitamente
        # (antes solo implicito en el judgment call #16 del reporte) --
        # `es_duplicado_interno` es el UNICO campo que esta carga escribe
        # para marcar una repetida (regla AD). Se marca TRUE simetricamente
        # en TODAS las filas del grupo, sin elegir una "original": el FK
        # `incapacidad_origen_id` (que el modelo documenta como "la
        # incapacidad original de la que esta es duplicado interno")
        # deliberadamente se deja sin poblar aqui, porque
        # `auditoria_rules.py` es explicito en que este modulo nunca elige
        # silenciosamente "la primera" fila como ganadora/original (mismo
        # principio aplicado en la seleccion de siniestro AM). Si una tarea
        # futura necesita un puntero real "duplicado de cual", debe ser una
        # decision explicita de un auditor humano, no algo que esta carga
        # infiera. Cubierto por
        # test_cargar_lote_marca_es_duplicado_interno_en_filas_repetidas en
        # test_lote_service.py.
        repetidas = agrupar_repetidas(filas_para_reglas)
        for _clave, ids in repetidas.items():
            if len(ids) > 1:
                for row_id in ids:
                    objetos_por_id[row_id].es_duplicado_interno = True

        encadenadas = encadenar_prorrogas(filas_para_reglas)
        for row_id, predecesor_id in encadenadas.items():
            if predecesor_id is not None:
                objetos_por_id[row_id].prorroga_de_id = UUID(predecesor_id)

        # ------------------------------------------------------------
        # Archivar el libro original (decifrado) en storage
        # ------------------------------------------------------------
        ruta_storage, _hash_md5, _hash_sha256, _tamanio = storage_backend.upload_file(
            file_data=io.BytesIO(bytes_planos),
            file_name=nombre_archivo,
            content_type=_CONTENT_TYPE_XLSX,
            folder=_STORAGE_FOLDER,
        )

        lote.total_filas = total_filas
        lote.total_incapacidades = total_incapacidades
        lote.metadata_ = {"archivo_original_path": ruta_storage}

        await db.flush()
        await db.commit()
        await db.refresh(lote)

        return lote


lote_previsional_service = LotePrevisionalService()
