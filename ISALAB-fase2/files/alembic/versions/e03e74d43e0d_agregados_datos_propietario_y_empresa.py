"""agregados_datos_propietario_y_empresa

Revision ID: e03e74d43e0d
Revises: 5688c877a6a6
Create Date: 2026-04-06 22:52:35.287316

NOTA (Fase 2, issue C2):
    Esta migración originalmente hacía ``op.create_table('animales')`` (y otras
    7 tablas) que YA habían sido creadas por la migración baseline
    ``5688c877a6a6``. Eso provocaba ``sqlite3.OperationalError: table already
    exists`` al correr ``alembic upgrade head`` desde cero.

    La intención real era AGREGAR columnas nuevas (propietario_tipo_doc,
    propietario_documento, propietario_direccion, propietario_oficio) a la
    tabla ``animales`` existente, y la columna ``empresa`` a ``muestras``.

    Reescrito como ``add_column`` (idempotente vía PRAGMA check).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e03e74d43e0d'
down_revision: Union[str, Sequence[str], None] = '5688c877a6a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_columns(bind, table_name: str) -> set:
    """Devuelve el set de columnas existentes en una tabla (vacío si la tabla no existe)."""
    result = bind.execute(sa.text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=:t"
    ), {"t": table_name})
    if not result.fetchone():
        return set()
    cols = bind.execute(sa.text(f"PRAGMA table_info({table_name})"))
    return {row[1] for row in cols.fetchall()}


def upgrade() -> None:
    """Agrega columnas nuevas a animales y muestras (sin recrear tablas)."""
    bind = op.get_bind()

    # ── animales: 4 columnas nuevas de propietario ─────────────────────────
    animal_cols = _existing_columns(bind, 'animales')
    new_animal_cols = [
        ('propietario_tipo_doc', sa.String(length=20)),
        ('propietario_documento', sa.String(length=50)),
        ('propietario_direccion', sa.String(length=150)),
        ('propietario_oficio', sa.String(length=100)),
    ]
    for col_name, col_type in new_animal_cols:
        if col_name not in animal_cols:
            op.add_column('animales', sa.Column(col_name, col_type, nullable=True))

    # ── muestras: 1 columna nueva (empresa) ────────────────────────────────
    muestra_cols = _existing_columns(bind, 'muestras')
    if 'empresa' not in muestra_cols:
        op.add_column('muestras', sa.Column('empresa', sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Elimina las columnas agregadas por upgrade()."""
    bind = op.get_bind()

    # muestras
    muestra_cols = _existing_columns(bind, 'muestras')
    if 'empresa' in muestra_cols:
        op.drop_column('muestras', 'empresa')

    # animales (orden inverso)
    animal_cols = _existing_columns(bind, 'animales')
    for col in ('propietario_oficio', 'propietario_direccion',
                'propietario_documento', 'propietario_tipo_doc'):
        if col in animal_cols:
            op.drop_column('animales', col)
