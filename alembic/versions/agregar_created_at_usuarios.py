"""agregar_created_at_usuarios

Revision ID: agregar_created_at_usuarios
Revises: 5688c877a6a6
Create Date: 2026-04-18 18:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'agregar_created_at_usuarios'
down_revision: Union[str, Sequence[str], None] = '38d0897cfe7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agregar columna created_at a tabla usuarios si no existe."""
    # Verificar si la tabla existe
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'"
    ))
    if not result.fetchone():
        # La tabla no existe, crearla
        op.create_table('usuarios',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('username', sa.String(length=50), nullable=False),
            sa.Column('password', sa.String(length=255), nullable=False),
            sa.Column('nombre', sa.String(length=100), nullable=False),
            sa.Column('rol', sa.String(length=20), nullable=True),
            sa.Column('activo', sa.Integer(), nullable=True),
            sa.Column('ultimo_acceso', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.String(length=50), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    else:
        # La tabla existe, agregar columna si no existe
        result = conn.execute(sa.text(
            "PRAGMA table_info(usuarios)"
        ))
        columns = [row[1] for row in result.fetchall()]
        
        if 'created_at' not in columns:
            op.add_column('usuarios', sa.Column('created_at', sa.String(length=50), nullable=True))
        
        if 'ultimo_acceso' not in columns:
            op.add_column('usuarios', sa.Column('ultimo_acceso', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Eliminar columna created_at."""
    op.drop_column('usuarios', 'created_at')