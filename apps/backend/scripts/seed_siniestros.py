"""
seed_siniestros.py — Crea 10 siniestros de prueba para una empresa existente.

Selecciona la empresa con más empleados activos, toma los 10 primeros empleados
activos (por numero_documento) que NO tengan un siniestro activo (estado
REPORTADO o EN_INVESTIGACION), y crea un siniestro por cada uno con
fecha_siniestro cercana a hoy/ayer (nunca posterior).

Al final imprime en stdout un resumen en formato CSV con los siniestros creados.

Uso (desde apps/backend/):
    python scripts/seed_siniestros.py
O vía docker (desde apps/backend/):
    docker compose exec api python scripts/seed_siniestros.py
"""

import asyncio
import csv
import io
import random
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

# Agregar el directorio raíz del backend al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.siniestro_repository import siniestro_repository
from app.db.session import AsyncSessionLocal
from app.models.empleado import Empleado
from app.models.empresa import Empresa
from app.models.siniestro import Siniestro
from app.utils.enums import (
    EstadoSiniestro,
    GravedadSiniestro,
    SucursalSiniestro,
    SyncSource,
    TipoSiniestro,
)

CANTIDAD_SINIESTROS = 10
REPORTE_AUTOR = "seed-siniestros"


def _hora_laboral_aleatoria() -> time:
    """Hora entre 07:00 y 17:30."""
    minutos = random.randint(7 * 60, 17 * 60 + 30)
    return time(minutos // 60, minutos % 60, 0)


def _fecha_siniestro_cercana(hoy: date) -> tuple[date, int]:
    """
    Devuelve (fecha_siniestro, dias_atras). Nunca posterior a hoy.
    Distribución: 70% hoy, 30% ayer.
    """
    dias_atras = 0 if random.random() < 0.7 else 1
    fecha_siniestro = hoy - timedelta(days=dias_atras)
    fecha_siniestro = min(fecha_siniestro, hoy)  # guard: nunca posterior a hoy
    return fecha_siniestro, dias_atras


def _next_numero_siniestro_suffix(nums_existentes: set[str], base: date) -> str:
    """
    Genera un numero_siniestro único con formato SIN-YYYYMMDD-NNNN.
    nums_existentes: conjunto de numeros ya usados en esta corrida.
    """
    prefijo = f"SIN-{base.strftime('%Y%m%d')}"
    idx = 1
    while True:
        candidato = f"{prefijo}-{idx:04d}"
        if candidato not in nums_existentes:
            nums_existentes.add(candidato)
            return candidato
        idx += 1


async def _get_empresa_y_empleados(db: AsyncSession) -> tuple[Empresa, list[Empleado]]:
    """
    Toma la empresa con más empleados activos, y los 10 primeros empleados
    activos por numero_documento que NO tengan siniestro activo
    (estado en REPORTADO o EN_INVESTIGACION).
    """
    # Empresa con más empleados activos
    stmt_empresa = (
        select(Empresa)
        .join(Empleado, Empleado.empresa_id == Empresa.id)
        .where(Empleado.estado == "ACTIVO")
        .group_by(Empresa.id)
        .order_by(func.count(Empleado.id).desc(), Empresa.razon_social.asc())
        .limit(1)
    )
    empresa = (await db.execute(stmt_empresa)).scalar_one_or_none()
    if empresa is None:
        raise RuntimeError("No hay empresas con empleados activos en la BD.")

    # IDs de empleados con al menos un siniestro activo
    stmt_con_activo = (
        select(Siniestro.empleado_id)
        .where(
            Siniestro.estado.in_(
                [EstadoSiniestro.REPORTADO, EstadoSiniestro.EN_INVESTIGACION]
            )
        )
        .distinct()
    )
    con_activo = {row[0] for row in (await db.execute(stmt_con_activo)).all()}

    stmt_empleados = (
        select(Empleado)
        .where(
            Empleado.empresa_id == empresa.id,
            Empleado.estado == "ACTIVO",
        )
        .order_by(Empleado.numero_documento.asc())
        .limit(CANTIDAD_SINIESTROS * 5)  # margen para saltar los que ya tienen activo
    )
    candidatos = list((await db.execute(stmt_empleados)).scalars().all())
    empleados = [e for e in candidatos if e.id not in con_activo][:CANTIDAD_SINIESTROS]

    if len(empleados) < CANTIDAD_SINIESTROS:
        raise RuntimeError(
            f"Solo se encontraron {len(empleados)} empleados activos sin siniestro activo "
            f"en la empresa '{empresa.razon_social}'. Se requieren {CANTIDAD_SINIESTROS}."
        )
    return empresa, empleados


escenarios = [
    # tipo, descripcion, lugar, parte, naturaleza, agente, requiere_hosp
    (
        TipoSiniestro.ACCIDENTE_TRABAJO,
        "Caída durante la jornada laboral al resbalar en piso mojado del área de trabajo.",
        "Área de trabajo — piso mojado",
        "Rodilla derecha",
        "Contusión",
        "Superficie resbaladiza",
        False,
    ),
    (
        TipoSiniestro.ACCIDENTE_TRABAJO,
        "Golpe con objeto contundente al manipular materiales en bodega.",
        "Bodega de materiales",
        "Mano izquierda",
        "Herida abierta",
        "Material almacenado",
        False,
    ),
    (
        TipoSiniestro.ACCIDENTE_TRAYECTO,
        "Accidente de tránsito en trayecto domicilio-trabajo.",
        "Vía pública — carrera 7",
        "Tobillo izquierdo",
        "Esguince",
        "Vehículo automotor",
        False,
    ),
    (
        TipoSiniestro.ENFERMEDAD_LABORAL,
        "Síntomas musculoesqueléticos por postura sostenida en estación de trabajo.",
        "Puesto de trabajo",
        "Región lumbar",
        "Lumbalgia",
        "Postura sostenida",
        False,
    ),
    (
        TipoSiniestro.ACCIDENTE_TRABAJO,
        "Atrapamiento de dedo al operar cerradura de equipo de oficina.",
        "Oficina — equipo",
        "Dedo pulgar derecho",
        "Aplastamiento",
        "Equipo de oficina",
        False,
    ),
    (
        TipoSiniestro.ACCIDENTE_TRAYECTO,
        "Caída en vía pública al descender del transporte público rumbo al trabajo.",
        "Andén estación de transporte",
        "Muñeca derecha",
        "Fractura",
        "Superficie irregular",
        True,
    ),
    (
        TipoSiniestro.ACCIDENTE_TRABAJO,
        "Contacto con superficie caliente al manipular equipo de la cafetería.",
        "Cafetería",
        "Antebrazo derecho",
        "Quemadura primer grado",
        "Superficie caliente",
        False,
    ),
    (
        TipoSiniestro.ENFERMEDAD_LABORAL,
        "Síndrome de sobrecarga por movimientos repetitivos en miembro superior.",
        "Puesto de trabajo",
        "Hombro derecho",
        "Tendinitis",
        "Movimiento repetitivo",
        False,
    ),
    (
        TipoSiniestro.ACCIDENTE_TRABAJO,
        "Esguince de tobillo al descender escaleras del área administrativa.",
        "Escaleras administrativas",
        "Tobillo derecho",
        "Esguince grado II",
        "Escaleras",
        False,
    ),
    (
        TipoSiniestro.ACCIDENTE_TRAYECTO,
        "Colisión leve en bicicleta durante trayecto trabajo-domicilio.",
        "Vía pública — ciclo ruta",
        "Codo izquierdo",
        "Contusión",
        "Bicicleta",
        False,
    ),
]


async def build_and_create(
    db: AsyncSession,
    empleado: Empleado,
    empresa_id,
    idx: int,
    nums_existentes: set[str],
    hoy: date,
) -> dict:
    """Crea un siniestro para el empleado y devuelve el dict de resumen."""
    escenario = escenarios[idx % len(escenarios)]
    tipo, descripcion, lugar, parte, naturaleza, agente, requiere_hosp = escenario
    fecha, _dias_atras = _fecha_siniestro_cercana(hoy)
    hora = _hora_laboral_aleatoria()
    gravedad = GravedadSiniestro.GRAVE if requiere_hosp else GravedadSiniestro.LEVE
    sucursal = list(SucursalSiniestro)[idx % len(SucursalSiniestro)]
    # fecha_reporte: 1-3 horas después del siniestro, mismo día, no futuro.
    fecha_reporte = datetime.combine(fecha, hora) + timedelta(
        hours=random.randint(1, 3)
    )
    if fecha_reporte > datetime.now():  # noqa: DTZ005
        fecha_reporte = datetime.now() - timedelta(  # noqa: DTZ005
            minutes=random.randint(5, 90)
        )
    numero = _next_numero_siniestro_suffix(nums_existentes, hoy)

    payload = {
        "numero_siniestro": numero,
        "empleado_id": empleado.id,
        "empresa_id": empresa_id,
        "fecha_siniestro": fecha,
        "hora_siniestro": hora,
        "tipo_siniestro": tipo,
        "descripcion": descripcion,
        "lugar_ocurrencia": lugar,
        "parte_cuerpo_afectada": parte,
        "naturaleza_lesion": naturaleza,
        "agente_causante": agente,
        "gravedad": gravedad,
        "sucursal": sucursal,
        "testigos": None,
        "requirio_hospitalizacion": requiere_hosp,
        "dias_estimados_incapacidad": random.randint(2, 15)
        if requiere_hosp
        else random.randint(1, 5),
        "estado": EstadoSiniestro.REPORTADO,
        "fecha_reporte": fecha_reporte,
        "reportado_por": REPORTE_AUTOR,
        "observaciones": None,
        "sync_source": SyncSource.MANUAL,
    }
    siniestro = await siniestro_repository.create_flushed(db, payload)
    return {
        "numero_siniestro": siniestro.numero_siniestro,
        "identificacion_empleado": empleado.numero_documento,
        "nombre_empleado": f"{empleado.nombres} {empleado.apellidos}".strip(),
        "fecha_siniestro": fecha.isoformat(),
        "hora_siniestro": hora.isoformat(timespec="minutes"),
        "tipo_siniestro": tipo.value,
        "gravedad": gravedad.value,
        "estado": EstadoSiniestro.REPORTADO.value,
        "sucursal": sucursal.value,
        "lugar_ocurrencia": lugar,
        "descripcion": descripcion,
    }


def _print_csv(rows: list[dict]) -> None:
    if not rows:
        return
    campos = list(rows[0].keys())
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=campos, quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    writer.writerows(rows)
    print("\n" + "=" * 80)
    print("RESUMEN DE SINIESTROS CREADOS (CSV):")
    print("=" * 80)
    sys.stdout.write(buf.getvalue())
    sys.stdout.flush()


async def main() -> None:
    hoy = date.today()  # noqa: DTZ011
    nums_existentes: set[str] = set()
    async with AsyncSessionLocal() as db:
        print(" Buscando empresa con empleados activos...")
        empresa, empleados = await _get_empresa_y_empleados(db)
        print(
            f" Empresa: {empresa.razon_social} (NIT: {empresa.nit}, id: {empresa.id})"
        )
        print(f" Empleados seleccionados ({len(empleados)}):")
        for i, e in enumerate(empleados, 1):
            print(
                f"   {i:>2}. {e.numero_documento} — {e.nombres} {e.apellidos} ({e.cargo})"
            )

        rows: list[dict] = []
        for idx, empleado in enumerate(empleados):
            try:
                row = await build_and_create(
                    db, empleado, empresa.id, idx, nums_existentes, hoy
                )
                rows.append(row)
                print(
                    f"  ✅ {row['numero_siniestro']} → {row['identificacion_empleado']} ({row['fecha_siniestro']} {row['hora_siniestro']})"
                )
            except Exception as exc:
                print(
                    f"  ❌ Error creando siniestro para {empleado.numero_documento}: {exc}"
                )
                raise

        await db.commit()
        print(f"\n Commit OK. {len(rows)}/{CANTIDAD_SINIESTROS} siniestros creados.")
        _print_csv(rows)


if __name__ == "__main__":
    asyncio.run(main())
