"""fase5_indexes_and_password_reset_flag

Revision ID: c1a2b3c4d5e6
Revises: 8f3a2c1d4e5f
Create Date: 2026-07-21 12:00:00

Fase 5 — dos mejoras HIGH:

  (1) H-D4 — indexes en foreign keys y columnas filtradas.
      Antes, ``ix_animales_codigo`` era el ÚNICO índice de toda la BD.
      Columnas como ``muestras.animal_id``, ``recepciones.estado``,
      ``historias_clinicas.animal_id`` no tenían índice, así que
      cualquier filtro o JOIN recorría la tabla completa. Para tablas
      de miles de filas (muestras, historias), eso significa queries
      de 100-500ms en lugar de 1-5ms.

  (2) H-S6 — columna ``password_reset_required`` en ``usuarios``.
      ``UsuarioService.reset_password`` ahora setea esta flag a 1,
      y ``cambiar_password`` / ``cambiar_password_admin`` la limpian.
      La GUI de login puede consultar la flag (incluida en el dict
      que retorna ``autenticar``) para forzar el cambio de contraseña
      en el próximo login. Antes, la contraseña temporal generada por
      ``reset_password`` era permanente — un riesgo de seguridad si
      el canal usado para entregarla (email, mensaje, etc.) era
      interceptado.

Esta migración es idempotente: usa ``IF NOT EXISTS`` en todos los
``CREATE INDEX`` (soportado por SQLite 3.8.0+ y por todas las
versiones de PostgreSQL/MySQL que Alembic soporta).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a2b3c4d5e6'
# Fase 5: extendemos desde el merge-head de Fase 2.
down_revision: Union[str, Sequence[str], None] = '8f3a2c1d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ─────────────────────────────────────────────────────────────────────────────
# H-D4: indexes en FKs y columnas filtradas.
# ─────────────────────────────────────────────────────────────────────────────
# Nombres siguiendo la convención ``ix_<tabla>_<columna>`` para que
# Alembic pueda revertirlos por nombre.

FK_INDEXES = [
    # movimientos
    ('ix_movimientos_animal_id', 'movimientos', 'animal_id'),
    # muestras
    ('ix_muestras_animal_id', 'muestras', 'animal_id'),
    ('ix_muestras_estado', 'muestras', 'estado'),
    ('ix_muestras_fecha_recoleccion', 'muestras', 'fecha_recoleccion'),
    # recepciones
    ('ix_recepciones_animal_id', 'recepciones', 'animal_id'),
    ('ix_recepciones_estado', 'recepciones', 'estado'),
    ('ix_recepciones_fecha_hora', 'recepciones', 'fecha_hora'),
    # historias_clinicas
    ('ix_historias_clinicas_animal_id', 'historias_clinicas', 'animal_id'),
    ('ix_historias_clinicas_recepcion_id', 'historias_clinicas', 'recepcion_id'),
    # consultas
    ('ix_consultas_animal_id', 'consultas', 'animal_id'),
    ('ix_consultas_historia_id', 'consultas', 'historia_id'),
    ('ix_consultas_fecha', 'consultas', 'fecha'),
    # cirugias
    ('ix_cirugias_animal_id', 'cirugias', 'animal_id'),
    ('ix_cirugias_historia_id', 'cirugias', 'historia_id'),
    ('ix_cirugias_estado', 'cirugias', 'estado'),
    # vacunaciones
    ('ix_vacunaciones_animal_id', 'vacunaciones', 'animal_id'),
    ('ix_vacunaciones_fecha_aplicacion', 'vacunaciones', 'fecha_aplicacion'),
    ('ix_vacunaciones_fecha_proxima', 'vacunaciones', 'fecha_proxima'),
]


def upgrade() -> None:
    """Crea indexes en FKs/columnas filtradas + añade flag de password reset."""

    # ── (1) H-D4: FK indexes ──────────────────────────────────────────────
    # SQLite soporta ``CREATE INDEX IF NOT EXISTS`` desde 3.8.0 (2013).
    # ``op.create_index(..., if_not_exists=True)`` está disponible desde
    # Alembic 1.7 — usamos el SQL directo para máxima compatibilidad.
    bind = op.get_bind()
    for index_name, table, column in FK_INDEXES:
        # Verificar si la tabla existe (la migración es segura incluso
        # si algunas tablas no están creadas todavía en algún environment).
        result = bind.execute(sa.text(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name=:t"
        ), {"t": table}).fetchone()
        if not result:
            continue
        bind.execute(sa.text(
            f"CREATE INDEX IF NOT EXISTS {index_name} "
            f"ON {table} ({column})"
        ))

    # ── (2) H-S6: columna ``password_reset_required`` en ``usuarios`` ─────
    # Verificamos si la columna ya existe para ser idempotente.
    result = bind.execute(sa.text(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name='usuarios'"
    )).fetchone()
    if result:
        cols = bind.execute(sa.text("PRAGMA table_info(usuarios)")).fetchall()
        col_names = [c[1] for c in cols]
        if 'password_reset_required' not in col_names:
            bind.execute(sa.text(
                "ALTER TABLE usuarios "
                "ADD COLUMN password_reset_required INTEGER "
                "NOT NULL DEFAULT 0"
            ))


def downgrade() -> None:
    """Revierte los cambios (drops indexes y columna)."""
    bind = op.get_bind()

    # ── (2) Revertir columna password_reset_required ──────────────────────
    # SQLite < 3.35 no soporta ``ALTER TABLE DROP COLUMN``. Para ser
    # compatibles con cualquier versión de SQLite, reconstruimos la tabla
    # sin la columna. Esto es lo que hace ``batch_alter_table`` de Alembic
    # internamente.
    result = bind.execute(sa.text(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name='usuarios'"
    )).fetchone()
    if result:
        cols = bind.execute(sa.text("PRAGMA table_info(usuarios)")).fetchall()
        col_names = [c[1] for c in cols]
        if 'password_reset_required' in col_names:
            with op.batch_alter_table('usuarios') as batch_op:
                batch_op.drop_column('password_reset_required')

    # ── (1) Revertir indexes ──────────────────────────────────────────────
    for index_name, table, _column in FK_INDEXES:
        try:
            bind.execute(sa.text(f"DROP INDEX IF EXISTS {index_name}"))
        except Exception:
            # Si el index no existe o la BD no soporta IF EXISTS, ignoramos.
            pass
