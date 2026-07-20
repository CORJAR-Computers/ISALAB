from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# Añade estas importaciones arriba para que Alembic conozca tu proyecto
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.connection import Base
from orm_models.animal import Animal  # Importamos nuestro modelo
from orm_models.clinica import * # Importamos los modelos clínicos

# Y cambia el target_metadata
target_metadata = Base.metadata

# ─────────────────────────────────────────────────────────────────────────────
# Inyectar la URL de la DB desde config.py (issue M8 / Fase 2 DB-03).
#
# Antes, ``alembic.ini`` tenía ``sqlalchemy.url = sqlite:///isalab.db``
# hardcoded, lo que hacía que ``alembic upgrade head`` creara ``./isalab.db``
# en el CWD en vez de usar ``data/isalab.db`` (la DB real de la aplicación).
#
# Ahora ``alembic.ini`` tiene ``sqlalchemy.url =`` vacío, y lo inyectamos aquí
# desde ``config.DB_PATH``. Para override manual, se puede usar la variable
# de entorno ``ISALAB_DB_PATH``.
# ─────────────────────────────────────────────────────────────────────────────
try:
    from config import DB_PATH
    _db_url = f"sqlite:///{DB_PATH}"
    config.set_main_option("sqlalchemy.url", _db_url)
except ImportError:
    # Si config.py no está disponible (ej. tests aislados), dejar que el
    # valor de alembic.ini (vacío) se use. Alembic lanzará error claro.
    pass

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # SQLite no soporta ALTER completos; batch mode sí
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite: permite alter_column vía recreación
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
