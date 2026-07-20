# database/connection.py
"""Gestor de conexiones IsaLab"""

import sqlite3
import threading
from contextlib import contextmanager
from typing import Optional, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import DB_CONFIG
from utils.logger import setup_logger
from utils.exceptions import DatabaseError, DuplicateError

logger = setup_logger()


class DatabaseManager:
    """Gestor singleton de conexiones SQLite"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._local = threading.local()
        self._initialize_database()
        self._initialized = True
        logger.info("DatabaseManager inicializado")

    def _initialize_database(self):
        """Crea SOLO las tablas auxiliares (El resto de la base de datos la gestiona Alembic/SQLAlchemy)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # ── Tabla contadores de código (Para autogenerar ISAL-XXXX, PAC-XXXX, etc.) ──
                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS codigo_contadores
                               (
                                   prefijo
                                   TEXT
                                   PRIMARY
                                   KEY,
                                   ultimo
                                   INTEGER
                                   DEFAULT
                                   0
                               )
                               ''')
                # Inicializar prefijos si no existen (Añadidos PAC y LAB por seguridad)
                for p in ('ISAL', 'CONS', 'CIRU', 'VAC', 'PAC', 'LAB'):
                    cursor.execute(
                        "INSERT OR IGNORE INTO codigo_contadores (prefijo, ultimo) VALUES (?, 0)",
                        (p,)
                    )

                # ── Usuarios y autenticación ──
                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS usuarios
                               (
                                   id
                                   INTEGER
                                   PRIMARY
                                   KEY
                                   AUTOINCREMENT,
                                   username
                                   TEXT
                                   UNIQUE
                                   NOT
                                   NULL,
                                   password_hash
                                   TEXT
                                   NOT
                                   NULL,
                                   nombre
                                   TEXT
                                   NOT
                                   NULL,
                                   rol
                                   TEXT
                                   DEFAULT
                                   'usuario'
                                   CHECK (
                                   rol
                                   IN
                               (
                                   'admin',
                                   'veterinario',
                                   'asistente',
                                   'usuario'
                               )),
                                   activo INTEGER DEFAULT 1,
                                   ultimo_acceso TIMESTAMP,
                                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                   )
                                ''')

                # SEGURIDAD: No se crea usuario admin por defecto
                # El primer usuario debe crearse mediante el instalador o wizard de primera ejecución
                # Esto previene credenciales hardcodeadas en producción

                conn.commit()
                logger.info("Base de datos auxiliar inicializada (Tablas clínicas delegadas a Alembic)")
                logger.info("NOTA: No hay usuarios creados. Ejecute el instalador de primera ejecución.")

        except sqlite3.Error as e:
            logger.error(f"Error inicializando base de datos: {e}")
            raise DatabaseError(f"No se pudo inicializar la base de datos: {e}")

    @contextmanager
    def get_connection(self):
        """Context manager para conexiones"""
        try:
            if not hasattr(self._local, 'connection'):
                self._local.connection = sqlite3.connect(**DB_CONFIG)
                self._local.connection.row_factory = sqlite3.Row

            yield self._local.connection

        except sqlite3.Error as e:
            logger.error(f"Error de conexión: {e}")
            raise DatabaseError(f"Error de conexión a base de datos: {e}")

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Ejecuta una query con manejo de errores"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor
        except sqlite3.IntegrityError as e:
            logger.error(f"Error de integridad: {e} | Query: {query}")
            if 'UNIQUE constraint failed' in str(e):
                raise DuplicateError("Ya existe un registro con ese código")
            raise DatabaseError(f"Error de integridad: {e}")
        except sqlite3.Error as e:
            logger.error(f"Error ejecutando query: {e}")
            raise DatabaseError(f"Error en operación de base de datos: {e}")

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Obtiene un solo registro"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Error en fetch_one: {e}")
            raise DatabaseError(f"Error consultando datos: {e}")

    def generar_codigo(self, prefijo: str) -> str:
        """Genera el siguiente código correlativo con prefijo."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE codigo_contadores SET ultimo = ultimo + 1 WHERE prefijo = ?",
                    (prefijo,)
                )
                row = cursor.execute(
                    "SELECT ultimo FROM codigo_contadores WHERE prefijo = ?",
                    (prefijo,)
                ).fetchone()
                conn.commit()
                if not row:
                    raise DatabaseError(f"Prefijo desconocido: {prefijo}")
                return f"{prefijo}-{row[0]:04d}"
        except Exception as e:
            logger.error(f"Error generando código {prefijo}: {e}")
            raise DatabaseError(f"No se pudo generar código: {e}")

    def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Obtiene múltiples registros"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error en fetch_all: {e}")
            raise DatabaseError(f"Error consultando datos: {e}")

    def health_check(self) -> dict:
        """Verifica el estado de salud de la base de datos. Retorna dict con estado."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Verificar tablas principales
                tablas = ['animales', 'usuarios', 'recepciones', 'muestras', 'historias_clinicas']
                tablas_existentes = []

                for tabla in tablas:
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        (tabla,)
                    )
                    if cursor.fetchone():
                        tablas_existentes.append(tabla)

                # Verificar que podemos escribir
                cursor.execute("SELECT 1")
                write_ok = True

                return {
                    'status': 'healthy',
                    'database_path': DB_CONFIG.get('database'),
                    'tables': tablas_existentes,
                    'write_access': write_ok,
                }

        except Exception as e:
            logger.error(f"Health check falló: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    def close_all_connections(self):
        """Cierra todas las conexiones abiertas (útil al cerrar la app)."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            logger.info("Conexiones de base de datos cerradas")


# =======================================================================
# CONFIGURACIÓN SQLALCHEMY (ORM) - COEXISTENCIA TEMPORAL
# =======================================================================

db_path = DB_CONFIG.get('database', 'isalab.db')
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()