"""agregar_created_at_todas_tablas

Revision ID: agregar_created_at_todas_tablas
Revises: 38d0897cfe7e
Create Date: 2026-04-18 18:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'agregar_created_at_todas_tablas'
down_revision: Union[str, Sequence[str], None] = '38d0897cfe7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agregar columna created_at a todas las tablas que la necesitan."""
    conn = op.get_bind()
    
    # Lista de tablas y sus columnas actuales
    tables_info = [
        ('muestras', 15),
        ('animales', 24),
        ('consultas', 13),
        ('cirugias', 16),
        ('vacunaciones', 12),
        ('recepciones', 9),
        ('historias_clinicas', 32),
        ('movimientos', 7),
    ]
    
    for table_name, expected_cols in tables_info:
        try:
            # Verificar si la tabla existe
            result = conn.execute(sa.text(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            ))
            if not result.fetchone():
                continue
                
            # Obtener columnas actuales
            result = conn.execute(sa.text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in result.fetchall()]
            
            # Agregar created_at si no existe
            if 'created_at' not in columns:
                op.add_column(table_name, sa.Column('created_at', sa.String(length=50), nullable=True))
                print(f"Added created_at to {table_name}")
            else:
                print(f"{table_name} already has created_at")
                
        except Exception as e:
            print(f"Error processing {table_name}: {e}")


def downgrade() -> None:
    """Eliminar columnas created_at de todas las tablas."""
    tables = ['muestras', 'animales', 'consultas', 'cirugias', 
             'vacunaciones', 'recepciones', 'historias_clinicas', 'movimientos']
    
    for table_name in tables:
        try:
            op.drop_column(table_name, 'created_at')
        except Exception as e:
            print(f"Error dropping from {table_name}: {e}")