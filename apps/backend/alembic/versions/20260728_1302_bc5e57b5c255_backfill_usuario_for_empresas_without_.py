"""backfill usuario for empresas without one

Revision ID: bc5e57b5c255
Revises: 4d58280019e6
Create Date: 2026-07-28 13:02:47.162520

"""
import csv
import secrets
import string
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext

# revision identifiers, used by Alembic.
revision: str = 'bc5e57b5c255'
down_revision: Union[str, None] = '4d58280019e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _generate_temp_password() -> str:
    alphabet = string.ascii_letters + string.digits
    password = list("".join(secrets.choice(alphabet) for _ in range(12)))
    password[0] = secrets.choice(string.ascii_uppercase)
    password[1] = secrets.choice(string.ascii_lowercase)
    password[2] = secrets.choice(string.digits)
    secrets.SystemRandom().shuffle(password)
    return "".join(password)


def upgrade() -> None:
    conn = op.get_bind()

    # DISTINCT ON (e.email_contacto) both dedupes empresas that share the same
    # email_contacto with each other (only the first per email, by nit, is
    # processed in this run -- inserting two Usuario rows with the same email
    # in the same migration run would collide just as badly) and the
    # NOT EXISTS guard skips any empresa whose nit or email_contacto already
    # matches an existing usuario.username/usuario.email (both columns are
    # UNIQUE, so either collision would otherwise abort the whole transaction).
    empresas_sin_usuario = conn.execute(sa.text("""
        SELECT DISTINCT ON (e.email_contacto)
            e.id, e.nit, e.razon_social, e.email_contacto
        FROM empresa e
        LEFT JOIN usuario u ON u.empresa_id = e.id AND u.rol = 'EMPRESA'
        WHERE u.id IS NULL
          AND e.email_contacto IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM usuario u2
              WHERE u2.username = e.nit OR u2.email = e.email_contacto
          )
        ORDER BY e.email_contacto, e.nit
    """)).fetchall()

    report_rows = []
    for empresa in empresas_sin_usuario:
        temp_password = _generate_temp_password()
        conn.execute(
            sa.text("""
                INSERT INTO usuario (
                    id, username, email, password_hash, nombre_completo,
                    rol, estado, empresa_id, intentos_fallidos, token_version,
                    must_change_password, incapacidades_asignadas_activas,
                    created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), :username, :email, :password_hash, :nombre_completo,
                    'EMPRESA', 'ACTIVO', :empresa_id, 0, 0,
                    false, 0,
                    now(), now()
                )
            """),
            {
                "username": empresa.nit,
                "email": empresa.email_contacto,
                "password_hash": pwd_context.hash(temp_password),
                "nombre_completo": empresa.razon_social,
                "empresa_id": str(empresa.id),
            },
        )
        report_rows.append((empresa.nit, empresa.razon_social, empresa.email_contacto, temp_password))

    if report_rows:
        report_path = f"backfill_usuario_empresa_{datetime.utcnow():%Y%m%d_%H%M%S}.csv"
        with open(report_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["nit", "razon_social", "email", "password_temporal"])
            writer.writerows(report_rows)
        print(f"[backfill] {len(report_rows)} usuarios creados. Credenciales en: {report_path}")

    total_sin_email = conn.execute(sa.text("""
        SELECT COUNT(*) FROM empresa e
        LEFT JOIN usuario u ON u.empresa_id = e.id AND u.rol = 'EMPRESA'
        WHERE u.id IS NULL AND e.email_contacto IS NULL
    """)).scalar()
    if total_sin_email:
        print(
            f"[backfill] AVISO: {total_sin_email} empresas sin email_contacto fueron "
            f"omitidas (no se les pudo crear usuario; requieren email_contacto primero)."
        )

    total_colision = conn.execute(sa.text("""
        SELECT COUNT(*) FROM (
            SELECT
                e.id,
                ROW_NUMBER() OVER (PARTITION BY e.email_contacto ORDER BY e.nit) AS rn,
                EXISTS (
                    SELECT 1 FROM usuario u2
                    WHERE u2.username = e.nit OR u2.email = e.email_contacto
                ) AS colisiona_con_usuario_existente
            FROM empresa e
            LEFT JOIN usuario u ON u.empresa_id = e.id AND u.rol = 'EMPRESA'
            WHERE u.id IS NULL AND e.email_contacto IS NOT NULL
        ) sub
        WHERE colisiona_con_usuario_existente OR rn > 1
    """)).scalar()
    if total_colision:
        print(
            f"[backfill] AVISO: {total_colision} empresas fueron omitidas por colisión "
            f"de username/email con un usuario ya existente, o por compartir "
            f"email_contacto con otra empresa procesada en esta misma corrida "
            f"(username/email son UNIQUE en usuario; requieren resolución manual)."
        )


def downgrade() -> None:
    # No-op: a backfilled Usuario is indistinguishable from one created normally
    # afterward via POST /empresas, so there is no safe way to identify and
    # remove only the backfilled rows. Reversing this migration is not supported.
    print("[backfill] downgrade is a no-op — backfilled usuarios are not distinguishable from later ones and are left in place.")
