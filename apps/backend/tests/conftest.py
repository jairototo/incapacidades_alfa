"""
Pytest configuration and fixtures.
"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
import sqlalchemy as sa
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, AsyncConnection, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.session import get_db
from app.models.base import Base
from app.core.config import settings


# Database URL para testing (usar base de datos de test)
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/incapacidades", "/incapacidades_test")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        # Crear tipos enum de forma idempotente usando bloques DO con EXCEPTION.
        # Los modelos usan create_type=False, así que create_all NUNCA los crea automáticamente.
        # Nota: CREATE TYPE IF NOT EXISTS no existe en PostgreSQL < 17; usamos DO+EXCEPTION.
        await conn.execute(sa.text("""
            DO $b$ BEGIN
                CREATE TYPE tipoincapacidad AS ENUM ('ARL', 'SALUD');
            EXCEPTION WHEN duplicate_object THEN null;
            END $b$;
        """))
        await conn.execute(sa.text("""
            DO $b$ BEGIN
                CREATE TYPE estadoincapacidad AS ENUM (
                    'RADICADA', 'EN_AUDITORIA', 'OBSERVADA', 'APROBADA',
                    'APROBADA_PARCIALMENTE', 'RECHAZADA', 'EN_PAGO',
                    'EN_PAGO_PARCIAL', 'PAGADA', 'PAGADA_PARCIALMENTE', 'CANCELADA'
                );
            EXCEPTION WHEN duplicate_object THEN null;
            END $b$;
        """))
        await conn.execute(sa.text("""
            DO $b$ BEGIN
                CREATE TYPE prioridad AS ENUM ('BAJA', 'NORMAL', 'ALTA', 'URGENTE');
            EXCEPTION WHEN duplicate_object THEN null;
            END $b$;
        """))
        await conn.execute(sa.text("""
            DO $b$ BEGIN
                CREATE TYPE tiposiniestro AS ENUM (
                    'ACCIDENTE_TRABAJO', 'ENFERMEDAD_LABORAL', 'ACCIDENTE_TRAYECTO'
                );
            EXCEPTION WHEN duplicate_object THEN null;
            END $b$;
        """))
        await conn.execute(sa.text("""
            DO $b$ BEGIN
                CREATE TYPE gravedadsiniestro AS ENUM ('LEVE', 'MODERADO', 'GRAVE', 'MORTAL');
            EXCEPTION WHEN duplicate_object THEN null;
            END $b$;
        """))
        await conn.execute(sa.text("""
            DO $b$ BEGIN
                CREATE TYPE estadosiniestro AS ENUM (
                    'REPORTADO', 'EN_INVESTIGACION', 'CERRADO', 'ANULADO'
                );
            EXCEPTION WHEN duplicate_object THEN null;
            END $b$;
        """))
        await conn.execute(sa.text("""
            DO $b$ BEGIN
                CREATE TYPE syncsource AS ENUM ('API', 'CSV', 'EXCEL', 'MANUAL');
            EXCEPTION WHEN duplicate_object THEN null;
            END $b$;
        """))

        # Crear todas las tablas (create_all es idempotente con checkfirst=True por defecto)
        await conn.run_sync(Base.metadata.create_all)

        # Crear función y trigger para registro automático de historial
        # DROP TRIGGER IF EXISTS evita DuplicateObjectError si ya existía de un test anterior
        await conn.execute(sa.text("""
            CREATE OR REPLACE FUNCTION registrar_radicacion_incapacidad()
            RETURNS TRIGGER AS $$
            BEGIN
                INSERT INTO historial_estado (
                    id,
                    entity_type,
                    entity_id,
                    estado_anterior,
                    estado_nuevo,
                    cambiado_por_id,
                    observacion,
                    fecha_cambio,
                    created_at,
                    updated_at
                ) VALUES (
                    gen_random_uuid(),
                    'incapacidad',
                    NEW.id,
                    NULL,
                    NEW.estado,
                    NEW.radicado_por_id,
                    'Estado inicial al radicar la incapacidad',
                    NOW(),
                    NOW(),
                    NOW()
                );

                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))

        await conn.execute(sa.text("""
            DROP TRIGGER IF EXISTS trigger_registrar_radicacion_incapacidad ON incapacidad;
        """))

        await conn.execute(sa.text("""
            CREATE TRIGGER trigger_registrar_radicacion_incapacidad
                AFTER INSERT ON incapacidad
                FOR EACH ROW
                EXECUTE FUNCTION registrar_radicacion_incapacidad();
        """))

    yield engine

    # Limpiar después de los tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with overridden database session."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# Fixtures para datos de prueba
@pytest_asyncio.fixture
async def seed_cie10(db_session: AsyncSession) -> list[str]:
    """Siembra un set de códigos CIE-10 reales en el catálogo de pruebas.

    Las rutas de radicación (masiva, individual y pública) rechazan los códigos
    que cumplen el formato pero NO existen en el catálogo, así que las pruebas que
    esperan una fila/radicación válida deben sembrar los códigos que usan.
    """
    from app.models.catalogo_cie10 import CatalogoCIE10

    codigos = [
        ("M545", "Dorsalgia"),
        ("A048", "Otras enfermedades intestinales bacterianas especificadas"),
        ("A09X", "Diarrea y gastroenteritis de presunto origen infeccioso"),
        ("A009", "Cólera, no especificado"),
        ("S060", "Conmoción cerebral"),
    ]
    db_session.add_all([CatalogoCIE10(codigo=c, descripcion=d) for c, d in codigos])
    await db_session.commit()
    return [c for c, _ in codigos]


@pytest_asyncio.fixture
async def test_empresa(db_session: AsyncSession):
    """Create a test empresa."""
    from app.models.empresa import Empresa
    from app.utils.enums import EstadoEmpresa

    empresa = Empresa(
        nit="900123456",
        razon_social="Empresa Test SAS",
        direccion="Calle 123 #45-67",
        ciudad="Bogotá",
        telefono="3001234567",
        email_contacto="test@empresa.com",
        estado=EstadoEmpresa.ACTIVA,
    )

    db_session.add(empresa)
    await db_session.commit()
    await db_session.refresh(empresa)

    return empresa


@pytest_asyncio.fixture
async def test_empleado(db_session: AsyncSession, test_empresa):
    """Create a test empleado."""
    from app.models.empleado import Empleado
    from app.utils.enums import EstadoEmpleado, TipoDocumento, Genero
    from datetime import date
    from decimal import Decimal

    empleado = Empleado(
        empresa_id=test_empresa.id,
        numero_documento="1234567890",
        tipo_documento=TipoDocumento.CC,
        nombres="Juan Carlos",
        apellidos="Pérez González",
        fecha_nacimiento=date(1990, 5, 15),
        genero=Genero.M,
        email="juan.perez@test.com",
        telefono="3009876543",
        cargo="Desarrollador",
        salario_base=Decimal("5000000.00"),
        fecha_ingreso=date(2020, 1, 1),
        estado=EstadoEmpleado.ACTIVO,
    )

    db_session.add(empleado)
    await db_session.commit()
    await db_session.refresh(empleado)

    return empleado


@pytest_asyncio.fixture
async def test_afiliado(db_session: AsyncSession):
    """Create a test afiliado (persona asegurada independiente)."""
    from app.models.afiliado import Afiliado
    from app.utils.enums import EstadoAfiliado, TipoPoliza, TipoDocumento
    from datetime import date

    afiliado = Afiliado(
        numero_poliza="POL-TEST-001",
        tipo_poliza="INDIVIDUAL",
        numero_documento="9876543210",
        tipo_documento="CC",
        nombres="María Fernanda",
        apellidos="López García",
        fecha_nacimiento=date(1985, 3, 20),
        genero="F",
        email="maria.lopez@test.com",
        telefono="3101234567",
        fecha_inicio_poliza=date(2023, 1, 1),
        fecha_fin_poliza=date(2024, 12, 31),
        estado=EstadoAfiliado.ACTIVO,
    )

    db_session.add(afiliado)
    await db_session.commit()
    await db_session.refresh(afiliado)

    return afiliado


@pytest_asyncio.fixture
async def test_incapacidad(db_session: AsyncSession, test_empleado, test_empresa):
    """Create a test incapacidad."""
    from app.models.incapacidad import Incapacidad
    from app.utils.enums import TipoIncapacidad, EstadoIncapacidad, Prioridad
    from datetime import date, datetime
    from decimal import Decimal

    incapacidad = Incapacidad(
        numero="INC-TEST-001",
        empleado_id=test_empleado.id,
        empresa_id=test_empresa.id,
        tipo=TipoIncapacidad.ARL,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 10),
        dias_totales=10,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Lumbago no especificado",
        valor_dia=Decimal("100000.00"),
        valor_total=Decimal("1000000.00"),
        estado=EstadoIncapacidad.RADICADA,
        fecha_radicacion=datetime.utcnow(),
        prioridad=Prioridad.NORMAL,
    )

    db_session.add(incapacidad)
    await db_session.commit()
    await db_session.refresh(incapacidad)

    return incapacidad


@pytest_asyncio.fixture
async def test_usuario(db_session: AsyncSession):
    """Create a test usuario."""
    from app.models.usuario import Usuario
    from app.utils.enums import RolUsuario, EstadoUsuario
    from app.core.security import get_password_hash

    usuario = Usuario(
        username="testuser",
        email="testuser@example.com",
        password_hash=get_password_hash("Test123!"),
        nombre_completo="Usuario de Test",
        rol=RolUsuario.ADMIN,
        estado=EstadoUsuario.ACTIVO,
    )

    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)

    return usuario


@pytest_asyncio.fixture
async def test_user_auditor(db_session: AsyncSession):
    """Create a test auditor user."""
    from app.models.usuario import Usuario
    from app.utils.enums import RolUsuario, EstadoUsuario
    from app.core.security import get_password_hash

    usuario = Usuario(
        username="auditor",
        email="auditor@example.com",
        password_hash=get_password_hash("Auditor123!"),
        nombre_completo="Usuario Auditor",
        rol=RolUsuario.AUDITOR,
        estado=EstadoUsuario.ACTIVO,
    )

    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)

    return usuario


@pytest_asyncio.fixture
async def test_documento(db_session: AsyncSession, test_incapacidad, test_usuario):
    """Create a test documento."""
    from app.models.documento import Documento
    from app.utils.enums import TipoDocumentoAdjunto

    documento = Documento(
        incapacidad_id=test_incapacidad.id,
        tipo_documento=TipoDocumentoAdjunto.INCAPACIDAD_MEDICA,
        nombre_archivo="test-uuid-123.pdf",
        nombre_original="certificado_medico.pdf",
        ruta_storage="documentos/test-uuid-123.pdf",
        bucket="incapacidades",
        mime_type="application/pdf",
        tamanio_bytes=245680,
        hash_md5="5d41402abc4b2a76b9719d911017c592",
        hash_sha256="2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
        uploaded_by_id=test_usuario.id,
        validado=False,
    )

    db_session.add(documento)
    await db_session.commit()
    await db_session.refresh(documento)

    return documento


@pytest_asyncio.fixture
async def admin_token_headers(test_usuario) -> dict:
    """Create authentication headers with admin token."""
    from app.core.security import create_access_token

    # Usar el ID del usuario (UUID) como sub en el token
    token = create_access_token(
        data={
            "sub": str(test_usuario.id),
            "token_version": test_usuario.token_version
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def empresa_user_token(db_session: AsyncSession, test_empresa) -> str:
    """Create a raw access token for an EMPRESA-role user linked to test_empresa."""
    from app.models.usuario import Usuario
    from app.utils.enums import RolUsuario, EstadoUsuario
    from app.core.security import get_password_hash, create_access_token

    usuario = Usuario(
        username="empresa_user",
        email="empresa_user@example.com",
        password_hash=get_password_hash("Empresa123!"),
        nombre_completo="Usuario Empresa Test",
        rol=RolUsuario.EMPRESA,
        estado=EstadoUsuario.ACTIVO,
        empresa_id=test_empresa.id,
    )

    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)

    token = create_access_token(
        data={
            "sub": str(usuario.id),
            "token_version": usuario.token_version,
        }
    )
    return token
