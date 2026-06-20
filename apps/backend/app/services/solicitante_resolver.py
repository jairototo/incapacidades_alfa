"""Resuelve (o crea) el Solicitante a partir de la empresa autenticada.

El portal no recibe datos de solicitante desde el frontend: el solicitante de toda
radicación es la propia empresa, identificada por su email de contacto.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.empresa import Empresa
from app.models.solicitante import Solicitante


async def resolve_solicitante_for_empresa(db: AsyncSession, empresa: Empresa) -> Solicitante:
    correo = (empresa.email_contacto or f"{empresa.nit}@empresa.local").strip().lower()
    existing = (
        await db.execute(select(Solicitante).where(Solicitante.correo == correo))
    ).scalar_one_or_none()
    if existing:
        return existing

    solicitante = Solicitante(
        correo=correo,
        nombres=empresa.razon_social[:100],
        apellidos="(Empresa)",
        telefono=getattr(empresa, "telefono", None),
    )
    db.add(solicitante)
    await db.flush()
    return solicitante
