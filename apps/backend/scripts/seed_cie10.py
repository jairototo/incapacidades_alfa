"""
Script para poblar la tabla catalogo_cie10 con códigos CIE-10
desde un archivo CSV.

Uso:
    python scripts/seed_cie10.py [--file ruta/al/archivo.csv]

El archivo CSV debe tener el formato:
    codigo,descripcion
    A00,Cólera
    A00.0,Cólera debido a Vibrio cholerae 01, biotipo cholerae
    ...
"""

import sys
import asyncio
import csv
from pathlib import Path
from typing import List, Tuple

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.db.session import AsyncSessionLocal
from apps.backend.app.models.catalogo_cie10 import CatalogoCIE10
from apps.backend.app.core.logging import logger


async def cargar_cie10_desde_csv(archivo_csv: str, session: AsyncSession) -> int:
    """
    Carga códigos CIE-10 desde un archivo CSV a la base de datos.
    
    Args:
        archivo_csv: Ruta al archivo CSV
        session: Sesión de base de datos
        
    Returns:
        Número de registros insertados
    """
    ruta = Path(archivo_csv)
    
    if not ruta.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {archivo_csv}")
    
    logger.info(f"Leyendo archivo CIE-10: {archivo_csv}")
    
    codigos: List[CatalogoCIE10] = []
    
    with open(ruta, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader, start=1):
            if 'codigo' not in row or 'descripcion' not in row:
                logger.warning(f"Fila {idx} sin columnas requeridas: {row}")
                continue
            
            codigo = row['codigo'].strip().upper()
            descripcion = row['descripcion'].strip()
            
            if not codigo or not descripcion:
                logger.warning(f"Fila {idx} con datos vacíos")
                continue
            
            codigos.append(
                CatalogoCIE10(
                    codigo=codigo,
                    descripcion=descripcion
                )
            )
    
    if not codigos:
        logger.warning("No se encontraron códigos válidos en el archivo")
        return 0
    
    logger.info(f"Códigos CIE-10 leídos: {len(codigos)}")
    
    # Insertar en lotes de 1000 para mejor performance
    batch_size = 1000
    total_insertados = 0
    
    for i in range(0, len(codigos), batch_size):
        batch = codigos[i:i + batch_size]
        session.add_all(batch)
        await session.flush()
        total_insertados += len(batch)
        logger.info(f"Insertados {total_insertados}/{len(codigos)} códigos")
    
    await session.commit()
    logger.success(f"✅ Total de códigos CIE-10 insertados: {total_insertados}")
    
    return total_insertados


async def limpiar_tabla(session: AsyncSession) -> int:
    """
    Elimina todos los registros de la tabla catalogo_cie10.
    
    Args:
        session: Sesión de base de datos
        
    Returns:
        Número de registros eliminados
    """
    logger.warning("Limpiando tabla catalogo_cie10...")
    
    result = await session.execute(delete(CatalogoCIE10))
    await session.commit()
    
    eliminados = result.rowcount or 0
    logger.info(f"Registros eliminados: {eliminados}")
    
    return eliminados


async def contar_registros(session: AsyncSession) -> int:
    """
    Cuenta los registros actuales en catalogo_cie10.
    
    Args:
        session: Sesión de base de datos
        
    Returns:
        Número de registros
    """
    from sqlalchemy import func
    
    result = await session.execute(
        select(func.count()).select_from(CatalogoCIE10)
    )
    count = result.scalar() or 0
    
    return count


async def main():
    """Función principal del script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Poblar tabla catalogo_cie10 con códigos CIE-10'
    )
    parser.add_argument(
        '--file',
        type=str,
        default='backend/data/cie10.csv',
        help='Ruta al archivo CSV con códigos CIE-10 (default: backend/data/cie10.csv)'
    )
    parser.add_argument(
        '--limpiar',
        action='store_true',
        help='Limpiar tabla antes de insertar'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("SEED: Catálogo CIE-10")
    logger.info("=" * 60)
    
    async with AsyncSessionLocal() as session:
        try:
            # Contar registros existentes
            count_inicial = await contar_registros(session)
            logger.info(f"Registros actuales en catalogo_cie10: {count_inicial}")
            
            # Limpiar si se solicitó
            if args.limpiar and count_inicial > 0:
                confirmacion = input(
                    f"\n⚠️  ¿Eliminar {count_inicial} registros existentes? (s/N): "
                )
                if confirmacion.lower() in ['s', 'si', 'sí', 'yes']:
                    await limpiar_tabla(session)
                else:
                    logger.info("Operación cancelada por el usuario")
                    return
            
            # Cargar desde CSV
            insertados = await cargar_cie10_desde_csv(args.file, session)
            
            # Contar registros finales
            count_final = await contar_registros(session)
            logger.info(f"Registros finales en catalogo_cie10: {count_final}")
            
            logger.success("\n✅ Proceso completado exitosamente")
            
        except FileNotFoundError as e:
            logger.error(f"❌ Error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            await session.rollback()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
