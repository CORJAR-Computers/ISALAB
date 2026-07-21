# services/report_service.py (si no lo tienes)
from database.connection import DatabaseManager
from datetime import datetime, timedelta


class ReportService:
    def __init__(self):
        self.db = DatabaseManager()

    def get_dashboard_stats(self):
        """Obtiene estadísticas para el dashboard"""
        stats = {}

        # Animales activos
        row = self.db.fetch_one(
            "SELECT COUNT(*) as total FROM animales WHERE estado = 'Activo'")
        stats['activos'] = row['total'] if row else 0

        # Ingresos hoy
        hoy = datetime.now().strftime('%Y-%m-%d')
        row = self.db.fetch_one(
            "SELECT COUNT(*) as total FROM animales WHERE date(fecha_ingreso) = ?",
            (hoy,)
        )
        stats['hoy'] = row['total'] if row else 0

        # Muestras pendientes
        row = self.db.fetch_one(
            "SELECT COUNT(*) as total FROM muestras WHERE estado = 'Pendiente'")
        stats['muestras_pendientes'] = row['total'] if row else 0

        # Muestras urgentes
        row = self.db.fetch_one(
            "SELECT COUNT(*) as total FROM muestras WHERE urgente = 1 AND estado != 'Completado'"
        )
        stats['urgentes'] = row['total'] if row else 0

        # Muestras completadas semana
        semana = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        row = self.db.fetch_one(
            "SELECT COUNT(*) as total FROM muestras WHERE estado = 'Completado' AND date(created_at) >= ?",
            (semana,)
        )
        stats['completadas_semana'] = row['total'] if row else 0

        # Tiempo promedio
        row = self.db.fetch_one("""
            SELECT AVG(julianday(fecha_entrega) - julianday(fecha_recoleccion)) as promedio
            FROM muestras
            WHERE estado = 'Completado' AND fecha_entrega IS NOT NULL
        """)
        stats['tiempo_promedio'] = round(
            row['promedio'], 1) if row and row['promedio'] else 0

        return stats

    def get_efficiency_metrics(self):
        """Obtiene métricas de eficiencia"""
        metrics = {}

        # Tasa de cumplimiento
        row = self.db.fetch_one("""
            SELECT
                COUNT(CASE WHEN date(fecha_entrega) <= date(fecha_recoleccion, '+3 days') THEN 1 END) * 100.0 / COUNT(*) as tasa
            FROM muestras
            WHERE estado = 'Completado' AND fecha_entrega IS NOT NULL
        """)
        metrics['tasa_cumplimiento'] = round(
            row['tasa'], 1) if row and row['tasa'] else 0

        # Muestras por técnico
        rows = self.db.fetch_all("""
            SELECT tecnico, COUNT(*) as total
            FROM muestras
            WHERE tecnico IS NOT NULL AND tecnico != ''
            GROUP BY tecnico
            ORDER BY total DESC
            LIMIT 5
        """)
        metrics['por_tecnico'] = [(r['tecnico'], r['total']) for r in rows]

        return metrics

    def get_reporte_muestras(self, fecha_inicio, fecha_fin):
        """Obtiene reporte detallado de muestras"""
        query = """
            SELECT m.*, a.nombre as animal_nombre, a.codigo as animal_codigo
            FROM muestras m
            LEFT JOIN animales a ON m.animal_id = a.id
            WHERE date(m.fecha_recoleccion) >= ? AND date(m.fecha_recoleccion) <= ?
            ORDER BY m.fecha_recoleccion DESC
        """
        rows = self.db.fetch_all(query, (fecha_inicio, fecha_fin))
        return [dict(row) for row in rows]
