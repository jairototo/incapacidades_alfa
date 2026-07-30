"""
Repositorio para Lote Previsional.

CRUD básico heredado de BaseRepository. `LotePrevisional` no tiene un campo
tipo "numero_lote" (el modelo de Task 2.1 solo tiene `nombre_archivo`, sin
identificador de negocio distinto del `id` UUID) — por eso no existe un
`get_by_numero_lote`, según lo previsto en el brief de Task 2.2.
"""
from app.db.repositories.base_repository import BaseRepository
from app.models.previsionales.lote_previsional import LotePrevisional


class LotePrevisionalRepository(BaseRepository[LotePrevisional]):
    """Repositorio para operaciones con LotePrevisional."""

    def __init__(self) -> None:
        super().__init__(LotePrevisional)


# Instancia global del repositorio
lote_previsional_repository = LotePrevisionalRepository()
