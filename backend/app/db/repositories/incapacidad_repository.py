"""
Repository para operaciones de base de datos de Incapacidad.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repositories.base_repository import BaseRepository
from app.models.incapacidad import Incapacidad
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
