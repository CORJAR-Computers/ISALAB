import pytest
from database.connection import DatabaseManager
from config import DB_CONFIG

def test_database_singleton():
    """Verifica que el DatabaseManager es un singleton"""
    db1 = DatabaseManager()
    db2 = DatabaseManager()
    assert db1 is db2

def test_database_health():
    """Verifica el estado de salud de la base de datos"""
    DatabaseManager._instance = None
    db = DatabaseManager()
    health = db.health_check()
    assert health['status'] == 'healthy'
    assert health['write_access'] is True
    assert 'usuarios' in health['tables']
