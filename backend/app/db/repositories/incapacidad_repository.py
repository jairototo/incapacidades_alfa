"""
Repository para operaciones de base de datos de Incapacidad.
"""
from typing import List, Optional, Dict
from uuid import UUID
from datetime import date, datetime, timedelta
from sqlalchemy import select, and_, or_, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repositories.base_repository import BaseRepository
from app.models.incapacidad import Incapacidad
from app.models.historial_estado import HistorialEstado
from app.utils.enums import EstadoIncapacidad, TipoIncapacidad, Prioridad


class IncapacidadRepository(BaseRepository[Incapacidad]):
    """Repository para Incapacidad con operaciones específicas."""

    def __init__(self):
        """Inicializa el repository con el modelo Incapacidad."""
        super().__init__(Incapacidad)

    async def get_by_id_with_relations(
        self,
        db: AsyncSession,
        incapacidad_id: UUID
    ) -> Optional[Incapacidad]:
        """
        Obtiene una incapacidad por ID con todas sus relaciones cargadas.
        
        Carga eager loading de:
        - empleado (si es ARL)
        - empresa (si es ARL)
        - afiliado (si es SALUD)
        - siniestros del empleado (si es ARL)
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            
        Returns:
            Incapacidad con relaciones cargadas, None si no existe
        """
        query = (
            select(Incapacidad)
            .where(Incapacidad.id == incapacidad_id)
            .options(
                selectinload(Incapacidad.empleado),
                selectinload(Incapacidad.empresa),
                selectinload(Incapacidad.afiliado),
            )
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_numero(
        self,
        db: AsyncSession,
        numero: str
    ) -> Optional[Incapacidad]:
        """
        Obtiene una incapacidad por su número único.
        
        Args:
            db: Sesión de base de datos
            numero: Número de la incapacidad
            
        Returns:
            Incapacidad si existe, None si no
        """
        query = select(Incapacidad).where(Incapacidad.numero == numero)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_empleado(
        self,
        db: AsyncSession,
        empleado_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Incapacidad]:
        """
        Obtiene todas las incapacidades de un empleado (tipo ARL).
        
        Args:
            db: Sesión de base de datos
            empleado_id: ID del empleado
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de incapacidades del empleado
        """
        query = select(Incapacidad).where(
            Incapacidad.empleado_id == empleado_id
        ).order_by(
            Incapacidad.fecha_inicio.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_afiliado(
        self,
        db: AsyncSession,
        afiliado_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Incapacidad]:
        """
        Obtiene todas las incapacidades de un afiliado (tipo SALUD).
        
        Args:
            db: Sesión de base de datos
            afiliado_id: ID del afiliado
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de incapacidades del afiliado
        """
        query = select(Incapacidad).where(
            Incapacidad.afiliado_id == afiliado_id
        ).order_by(
            Incapacidad.fecha_inicio.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_estado(
        self,
        db: AsyncSession,
        estado: EstadoIncapacidad,
        skip: int = 0,
        limit: int = 100
    ) -> List[Incapacidad]:
        """
        Obtiene incapacidades por estado.
        
        Args:
            db: Sesión de base de datos
            estado: Estado de la incapacidad
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de incapacidades en el estado especificado
        """
        query = select(Incapacidad).where(
            Incapacidad.estado == estado
        ).order_by(
            Incapacidad.created_at.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_arl_by_siniestro(
        self,
        db: AsyncSession,
        siniestro_id: UUID
    ) -> List[Incapacidad]:
        """
        Obtiene incapacidades ARL asociadas a un siniestro.
        
        Args:
            db: Sesión de base de datos
            siniestro_id: ID del siniestro
            
        Returns:
            Lista de incapacidades del siniestro
        """
        query = select(Incapacidad).where(
            and_(
                Incapacidad.tipo == TipoIncapacidad.ARL,
                Incapacidad.siniestro_id == siniestro_id
            )
        ).order_by(Incapacidad.fecha_inicio.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def search(
        self,
        db: AsyncSession,
        tipo: Optional[TipoIncapacidad] = None,
        estado: Optional[EstadoIncapacidad] = None,
        empleado_id: Optional[UUID] = None,
        afiliado_id: Optional[UUID] = None,
        empresa_id: Optional[UUID] = None,
        fecha_inicio_desde: Optional[date] = None,
        fecha_inicio_hasta: Optional[date] = None,
        fecha_fin_desde: Optional[date] = None,
        fecha_fin_hasta: Optional[date] = None,
        prioridad: Optional[Prioridad] = None,
        numero: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Incapacidad]:
        """
        Busca incapacidades con múltiples filtros.
        
        Args:
            db: Sesión de base de datos
            tipo: Filtrar por tipo (ARL/SALUD)
            estado: Filtrar por estado
            empleado_id: Filtrar por empleado
            afiliado_id: Filtrar por afiliado
            empresa_id: Filtrar por empresa
            fecha_inicio_desde: Fecha inicio mínima
            fecha_inicio_hasta: Fecha inicio máxima
            fecha_fin_desde: Fecha fin mínima
            fecha_fin_hasta: Fecha fin máxima
            prioridad: Filtrar por prioridad
            numero: Búsqueda parcial en número
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de incapacidades que cumplen los criterios
        """
        query = select(Incapacidad)
        
        # Aplicar filtros
        if tipo:
            query = query.where(Incapacidad.tipo == tipo)
        
        if estado:
            query = query.where(Incapacidad.estado == estado)
        
        if empleado_id:
            query = query.where(Incapacidad.empleado_id == empleado_id)
        
        if afiliado_id:
            query = query.where(Incapacidad.afiliado_id == afiliado_id)
        
        if empresa_id:
            query = query.where(Incapacidad.empresa_id == empresa_id)
        
        if fecha_inicio_desde:
            query = query.where(Incapacidad.fecha_inicio >= fecha_inicio_desde)
        
        if fecha_inicio_hasta:
            query = query.where(Incapacidad.fecha_inicio <= fecha_inicio_hasta)
        
        if fecha_fin_desde:
            query = query.where(Incapacidad.fecha_fin >= fecha_fin_desde)
        
        if fecha_fin_hasta:
            query = query.where(Incapacidad.fecha_fin <= fecha_fin_hasta)
        
        if prioridad:
            query = query.where(Incapacidad.prioridad == prioridad)
        
        if numero:
            query = query.where(Incapacidad.numero.ilike(f"%{numero}%"))
        
        # Ordenar por fecha de radicación descendente
        query = query.order_by(Incapacidad.fecha_radicacion.desc())
        
        # Paginación
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_external_id(
        self,
        db: AsyncSession,
        external_id: str,
        sync_source: str
    ) -> Optional[Incapacidad]:
        """
        Obtiene una incapacidad por su ID externo.
        
        Args:
            db: Sesión de base de datos
            external_id: ID en sistema externo
            sync_source: Fuente de sincronización
            
        Returns:
            Incapacidad si existe, None si no
        """
        # TODO: Agregar campos sync_source y external_id al modelo si son necesarios
        # Por ahora retorna None
        return None

    async def count_by_estado(
        self,
        db: AsyncSession,
        estado: EstadoIncapacidad
    ) -> int:
        """
        Cuenta incapacidades por estado.
        
        Args:
            db: Sesión de base de datos
            estado: Estado a contar
            
        Returns:
            Número de incapacidades en el estado
        """
        return await self.count(db, filters={'estado': estado})

    async def get_pendientes_auditoria(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Incapacidad]:
        """
        Obtiene incapacidades pendientes de auditoría.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de incapacidades en estado RADICADA o OBSERVADA
        """
        query = select(Incapacidad).where(
            or_(
                Incapacidad.estado == EstadoIncapacidad.RADICADA,
                Incapacidad.estado == EstadoIncapacidad.OBSERVADA
            )
        ).order_by(
            Incapacidad.prioridad.desc(),
            Incapacidad.fecha_radicacion.asc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def listar_pendientes(
        self,
        db: AsyncSession,
        estados: List[EstadoIncapacidad],
        tipo: Optional[TipoIncapacidad] = None,
        prioridad: Optional[Prioridad] = None,
        empresa_nit: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Incapacidad]:
        """
        Listar incapacidades pendientes con filtros y ordenamiento por prioridad.
        
        Orden: 
        1. Prioridad (URGENTE → ALTA → NORMAL → BAJA)
        2. Antigüedad (created_at ASC - más antiguas primero)
        
        Args:
            db: Sesión de base de datos
            estados: Lista de estados pendientes
            tipo: Filtro opcional por tipo (ARL/SALUD)
            prioridad: Filtro opcional por prioridad
            empresa_nit: Filtro opcional por NIT de empresa (solo ARL)
            skip: Offset para paginación
            limit: Límite de resultados
            
        Returns:
            Lista de incapacidades ordenadas por prioridad y antigüedad
        """
        from sqlalchemy import case
        from sqlalchemy.orm import selectinload
        from app.models.empresa import Empresa
        from app.models.empleado import Empleado
        from app.models.afiliado import Afiliado
        
        # Query base con eager loading
        query = (
            select(Incapacidad)
            .where(Incapacidad.estado.in_(estados))
            .options(
                selectinload(Incapacidad.empleado).selectinload(Empleado.empresa),
                selectinload(Incapacidad.afiliado),
                selectinload(Incapacidad.empresa)
            )
        )
        
        # Filtros opcionales
        if tipo:
            query = query.where(Incapacidad.tipo == tipo)
        
        if prioridad:
            query = query.where(Incapacidad.prioridad == prioridad)
        
        if empresa_nit:
            # Join con empresa para filtrar por NIT
            query = query.join(Empresa).where(Empresa.nit == empresa_nit)
        
        # Ordenamiento por prioridad custom
        prioridad_order = case(
            (Incapacidad.prioridad == Prioridad.URGENTE, 1),
            (Incapacidad.prioridad == Prioridad.ALTA, 2),
            (Incapacidad.prioridad == Prioridad.NORMAL, 3),
            (Incapacidad.prioridad == Prioridad.BAJA, 4),
            else_=5
        )
        
        query = query.order_by(
            prioridad_order,
            Incapacidad.created_at.asc()  # Más antiguas primero
        )
        
        # Paginación
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    async def get_stats(
        self,
        db: AsyncSession,
        empresa_id: Optional[UUID] = None,
        tipo: Optional[TipoIncapacidad] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
    ) -> Dict[str, int]:
        """
        Calcular estadísticas de incapacidades con filtros opcionales.
        
        Usa queries SQL específicas por métrica para máxima eficiencia.
        NO cargar objetos completos, solo COUNT().
        
        Args:
            db: Sesión de base de datos
            empresa_id: Filtrar por empresa (opcional)
            tipo: Filtrar por tipo ARL/SALUD (opcional)
            fecha_desde: Filtrar desde fecha (opcional)
            fecha_hasta: Filtrar hasta fecha (opcional)
            
        Returns:
            Dict con métricas: pendientes, auditadas_hoy, proximas_vencer, rechazadas_observadas
        """
        # Query base con filtros comunes
        base_conditions = []
        
        if empresa_id:
            base_conditions.append(Incapacidad.empresa_id == empresa_id)
        if tipo:
            base_conditions.append(Incapacidad.tipo == tipo)
        if fecha_desde:
            base_conditions.append(Incapacidad.created_at >= datetime.combine(fecha_desde, datetime.min.time()))
        if fecha_hasta:
            base_conditions.append(Incapacidad.created_at <= datetime.combine(fecha_hasta, datetime.max.time()))
        
        # Métrica 1: Pendientes (RADICADA o EN_AUDITORIA)
        pendientes_query = select(func.count(Incapacidad.id)).where(
            Incapacidad.estado.in_([EstadoIncapacidad.RADICADA, EstadoIncapacidad.EN_AUDITORIA]),
            *base_conditions
        )
        result = await db.execute(pendientes_query)
        pendientes = result.scalar() or 0
        
        # Métrica 2: Auditadas hoy
        # JOIN con historial_estado para obtener cambios de estado de hoy
        hoy = date.today()
        auditadas_query = (
            select(func.count(distinct(HistorialEstado.entity_id)))
            .select_from(HistorialEstado)
            .where(
                HistorialEstado.entity_type == "incapacidad",
                HistorialEstado.estado_nuevo.in_([
                    EstadoIncapacidad.APROBADA.value,
                    EstadoIncapacidad.RECHAZADA.value,
                    EstadoIncapacidad.OBSERVADA.value
                ]),
                func.date(HistorialEstado.created_at) == hoy
            )
        )
        
        # Aplicar filtros de incapacidad si existen
        if base_conditions:
            auditadas_query = auditadas_query.join(
                Incapacidad,
                HistorialEstado.entity_id == Incapacidad.id
            ).where(*base_conditions)
        
        result = await db.execute(auditadas_query)
        auditadas_hoy = result.scalar() or 0
        
        # Métrica 3: Próximas a vencer (>7 días sin cambio)
        siete_dias_atras = datetime.utcnow() - timedelta(days=7)
        
        # Subquery: última fecha de cambio por incapacidad
        ultima_actualizacion_subquery = (
            select(
                HistorialEstado.entity_id,
                func.max(HistorialEstado.created_at).label('ultima_actualizacion')
            )
            .where(HistorialEstado.entity_type == "incapacidad")
            .group_by(HistorialEstado.entity_id)
            .subquery()
        )
        
        proximas_vencer_query = (
            select(func.count(Incapacidad.id))
            .select_from(Incapacidad)
            .join(
                ultima_actualizacion_subquery,
                Incapacidad.id == ultima_actualizacion_subquery.c.entity_id
            )
            .where(
                Incapacidad.estado.in_([
                    EstadoIncapacidad.RADICADA,
                    EstadoIncapacidad.EN_AUDITORIA,
                    EstadoIncapacidad.OBSERVADA
                ]),
                ultima_actualizacion_subquery.c.ultima_actualizacion <= siete_dias_atras,
                *base_conditions
            )
        )
        
        result = await db.execute(proximas_vencer_query)
        proximas_vencer = result.scalar() or 0
        
        # Métrica 4: Rechazadas u Observadas
        rechazadas_query = select(func.count(Incapacidad.id)).where(
            Incapacidad.estado.in_([EstadoIncapacidad.RECHAZADA, EstadoIncapacidad.OBSERVADA]),
            *base_conditions
        )
        result = await db.execute(rechazadas_query)
        rechazadas_observadas = result.scalar() or 0
        
        return {
            "pendientes": pendientes,
            "auditadas_hoy": auditadas_hoy,
            "proximas_vencer": proximas_vencer,
            "rechazadas_observadas": rechazadas_observadas,
        }

    async def get_extended_stats(
        self,
        db: AsyncSession,
        empresa_id: Optional[UUID] = None,
        tipo: Optional[TipoIncapacidad] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        top_limit: int = 10,
    ) -> Dict[str, any]:
        """
        Calcular estadísticas extendidas con datos para gráficos.
        
        Args:
            db: Sesión de base de datos
            empresa_id: Filtrar por empresa (opcional)
            tipo: Filtrar por tipo ARL/SALUD (opcional)
            fecha_desde: Filtrar desde fecha (opcional)
            fecha_hasta: Filtrar hasta fecha (opcional)
            top_limit: Límite para rankings TOP (default 10)
            
        Returns:
            Dict con métricas básicas + datos agregados para gráficos
        """
        from sqlalchemy import desc, case, extract
        from app.models.empresa import Empresa
        from app.models.empleado import Empleado
        from dateutil.relativedelta import relativedelta
        
        # 1. Obtener métricas básicas (reutilizar método existente)
        basic_stats = await self.get_stats(db, empresa_id, tipo, fecha_desde, fecha_hasta)
        
        # Condiciones base
        base_conditions = []
        if empresa_id:
            base_conditions.append(Incapacidad.empresa_id == empresa_id)
        if tipo:
            base_conditions.append(Incapacidad.tipo == tipo)
        if fecha_desde:
            base_conditions.append(Incapacidad.created_at >= datetime.combine(fecha_desde, datetime.min.time()))
        if fecha_hasta:
            base_conditions.append(Incapacidad.created_at <= datetime.combine(fecha_hasta, datetime.max.time()))
        
        # 2. Top 10 Empresas por Radicaciones
        top_empresas_query = (
            select(
                Empresa.id,
                Empresa.razon_social,
                Empresa.nit,
                func.count(Incapacidad.id).label('total_incapacidades'),
                func.coalesce(func.sum(Incapacidad.valor_total), 0).label('valor_total')
            )
            .select_from(Incapacidad)
            .join(Empresa, Incapacidad.empresa_id == Empresa.id)
            .where(*base_conditions)
            .group_by(Empresa.id, Empresa.razon_social, Empresa.nit)
            .order_by(desc('total_incapacidades'))
            .limit(top_limit)
        )
        result = await db.execute(top_empresas_query)
        top_empresas = [
            {
                "empresa_id": row.id,
                "razon_social": row.razon_social,
                "nit": row.nit,
                "total_incapacidades": row.total_incapacidades,
                "valor_total": row.valor_total
            }
            for row in result.all()
        ]
        
        # 3. Top 10 Diagnósticos CIE-10
        # Primero obtener el total de incapacidades
        total_query = select(func.count(Incapacidad.id)).where(*base_conditions)
        total_result = await db.execute(total_query)
        total_incapacidades = total_result.scalar() or 1  # Evitar división por 0
        
        top_cie10_query = (
            select(
                Incapacidad.diagnostico_cie10,
                Incapacidad.descripcion_diagnostico,
                func.count(Incapacidad.id).label('total')
            )
            .where(*base_conditions)
            .group_by(Incapacidad.diagnostico_cie10, Incapacidad.descripcion_diagnostico)
            .order_by(desc('total'))
            .limit(top_limit)
        )
        result = await db.execute(top_cie10_query)
        top_diagnosticos = [
            {
                "codigo_cie10": row.diagnostico_cie10,
                "descripcion": row.descripcion_diagnostico or "Sin descripción",
                "total_incapacidades": row.total,
                "porcentaje": round((row.total / total_incapacidades) * 100, 2)
            }
            for row in result.all()
        ]
        
        # 4. Top 10 Empleados con más Días de Incapacidad
        top_empleados_query = (
            select(
                Empleado.id,
                Empleado.nombres,
                Empleado.apellidos,
                Empleado.numero_documento,
                Empresa.razon_social.label('empresa_razon_social'),
                func.sum(Incapacidad.dias_totales).label('total_dias'),
                func.count(Incapacidad.id).label('total_incapacidades')
            )
            .select_from(Incapacidad)
            .join(Empleado, Incapacidad.empleado_id == Empleado.id)
            .join(Empresa, Empleado.empresa_id == Empresa.id)
            .where(
                Incapacidad.tipo == TipoIncapacidad.ARL,
                *base_conditions
            )
            .group_by(
                Empleado.id,
                Empleado.nombres,
                Empleado.apellidos,
                Empleado.numero_documento,
                Empresa.razon_social
            )
            .order_by(desc('total_dias'))
            .limit(top_limit)
        )
        result = await db.execute(top_empleados_query)
        top_empleados = [
            {
                "empleado_id": row.id,
                "nombres": row.nombres,
                "apellidos": row.apellidos,
                "numero_documento": row.numero_documento,
                "empresa_razon_social": row.empresa_razon_social,
                "total_dias": row.total_dias,
                "total_incapacidades": row.total_incapacidades
            }
            for row in result.all()
        ]
        
        # 5. Distribución de Pendientes por Estado
        # Solo estados activos: RADICADA, EN_AUDITORIA, OBSERVADA
        estados_pendientes = [
            EstadoIncapacidad.RADICADA,
            EstadoIncapacidad.EN_AUDITORIA,
            EstadoIncapacidad.OBSERVADA
        ]
        
        distribucion_estados_query = (
            select(
                Incapacidad.estado,
                func.count(Incapacidad.id).label('cantidad')
            )
            .where(
                Incapacidad.estado.in_(estados_pendientes),
                *base_conditions
            )
            .group_by(Incapacidad.estado)
        )
        result = await db.execute(distribucion_estados_query)
        distribucion_data = result.all()
        total_pendientes = sum(row.cantidad for row in distribucion_data)
        
        distribucion_estados = [
            {
                "estado": row.estado,
                "cantidad": row.cantidad,
                "porcentaje": round((row.cantidad / total_pendientes * 100) if total_pendientes > 0 else 0, 2)
            }
            for row in distribucion_data
        ]
        
        # 6. Distribución por Tipo (ARL vs SALUD)
        distribucion_tipos_query = (
            select(
                Incapacidad.tipo,
                func.count(Incapacidad.id).label('cantidad'),
                func.coalesce(func.sum(Incapacidad.valor_total), 0).label('valor_total'),
                func.avg(Incapacidad.dias_totales).label('promedio_dias')
            )
            .where(*base_conditions)
            .group_by(Incapacidad.tipo)
        )
        result = await db.execute(distribucion_tipos_query)
        distribucion_tipos = [
            {
                "tipo": row.tipo,
                "cantidad": row.cantidad,
                "valor_total": row.valor_total,
                "promedio_dias": round(row.promedio_dias, 2) if row.promedio_dias else 0
            }
            for row in result.all()
        ]
        
        # 7. Tendencia Mensual (últimos 6 meses)
        # Calcular rango de 6 meses
        hoy = datetime.utcnow()
        hace_6_meses = hoy - relativedelta(months=6)
        
        tendencia_query = (
            select(
                func.to_char(Incapacidad.created_at, 'YYYY-MM').label('mes'),
                func.count(
                    case((Incapacidad.estado == EstadoIncapacidad.RADICADA or Incapacidad.estado == EstadoIncapacidad.EN_AUDITORIA, 1))
                ).label('radicadas'),
                func.count(
                    case((Incapacidad.estado == EstadoIncapacidad.APROBADA, 1))
                ).label('aprobadas'),
                func.count(
                    case((Incapacidad.estado == EstadoIncapacidad.RECHAZADA, 1))
                ).label('rechazadas'),
                func.coalesce(
                    func.sum(
                        case((Incapacidad.estado == EstadoIncapacidad.APROBADA, Incapacidad.valor_total))
                    ), 0
                ).label('valor_total_aprobado')
            )
            .where(
                Incapacidad.created_at >= hace_6_meses,
                *base_conditions
            )
            .group_by('mes')
            .order_by('mes')
        )
        result = await db.execute(tendencia_query)
        tendencia_mensual = [
            {
                "mes": row.mes,
                "radicadas": row.radicadas,
                "aprobadas": row.aprobadas,
                "rechazadas": row.rechazadas,
                "valor_total_aprobado": row.valor_total_aprobado
            }
            for row in result.all()
        ]
        
        # Combinar todo
        return {
            **basic_stats,
            "top_empresas": top_empresas,
            "top_diagnosticos": top_diagnosticos,
            "top_empleados": top_empleados,
            "distribucion_estados": distribucion_estados,
            "distribucion_tipos": distribucion_tipos,
            "tendencia_mensual": tendencia_mensual,
        }

    async def get_aprobadas_pendientes_pago(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Incapacidad]:
        """
        Obtiene incapacidades aprobadas pendientes de pago.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de incapacidades en estado APROBADA
        """
        return await self.get_by_estado(db, EstadoIncapacidad.APROBADA, skip, limit)


# Singleton instance
incapacidad_repository = IncapacidadRepository()
