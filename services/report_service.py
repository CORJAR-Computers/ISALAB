# services/report_service.py (si no lo tienes)
"""
Dashboard y métricas — ISALAB.

Fase 3 (issue C1 — RBAC bypass): las operaciones de lectura de
estadísticas solo requieren usuario autenticado.
"""
from database.connection import DatabaseManager
from datetime import datetime, timedelta
from typing import Optional
from utils.security import Authorizer


class ReportService:
    def __init__(self, usuario_actual: Optional[dict] = None):
        self.db = DatabaseManager()
        self.authorizer = Authorizer(usuario_actual)

    def get_dashboard_stats(self):
        """Obtiene estadísticas para el dashboard"""
        # RBAC: cualquier usuario autenticado
        self.authorizer.require_authenticated()

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
        # Fase 6 (S-M8): antes, ``AVG(julianday(fecha_entrega) - julianday(fecha_recoleccion))``
        # podía producir valores NEGATIVOS si ``fecha_entrega < fecha_recoleccion``
        # (data integrity issue — un usuario carga fecha de entrega anterior
        # a la de recolección). El AVG incluía esos negativos, bajando
        # artificialmente el tiempo promedio y pudiendo mostrar incluso
        # números negativos en el dashboard. Ahora filtramos con
        # ``fecha_entrega >= fecha_recoleccion`` para excluir registros
        # corruptos del cálculo (preferimos excluirlos a incluirlos como
        # cero, porque un cero falsamente positivo también destruye el
        # promedio).
        row = self.db.fetch_one("""
            SELECT AVG(julianday(fecha_entrega) - julianday(fecha_recoleccion)) as promedio
            FROM muestras
            WHERE estado = 'Completado'
              AND fecha_entrega IS NOT NULL
              AND fecha_recoleccion IS NOT NULL
              AND fecha_entrega >= fecha_recoleccion
        """)
        stats['tiempo_promedio'] = round(
            row['promedio'], 1) if row and row['promedio'] else 0

        # Fase 4 (C2): consultas registradas hoy. Antes el dashboard
        # mostraba "0" permanentemente porque `refresh()` era no-op.
        # Esta stat alimenta la 3ra tarjeta ("Consultas Hoy").
        row = self.db.fetch_one(
            "SELECT COUNT(*) as total FROM consultas WHERE date(fecha_hora) = ?",
            (hoy,)
        )
        stats['consultas_hoy'] = row['total'] if row else 0

        return stats

    def get_efficiency_metrics(self):
        """Obtiene métricas de eficiencia"""
        # RBAC: cualquier usuario autenticado
        self.authorizer.require_authenticated()

        metrics = {}

        # Tasa de cumplimiento
        # Fase 6 (S-M9): antes, la query filtraba ``WHERE estado =
        # 'Completado' AND fecha_entrega IS NOT NULL``, lo que
        # SILENCIOSAMENTE excluía del denominador todas las muestras
        # "Completado" con ``fecha_entrega IS NULL``. El resultado era
        # que una muestra marcada como Completado pero sin fecha de
        # entrega cargada inflaba la tasa de cumplimiento (no contaba
        # en contra). Eso es un data integrity issue común cuando el
        # flujo de trabajo permite marcar "Completado" sin obligar a
        # cargar ``fecha_entrega``.
        #
        # Ahora el denominador incluye TODAS las muestras Completado
        # (con o sin ``fecha_entrega``), y el numerador solo cuenta las
        # cumplidas (``fecha_entrega`` dentro de las 72h desde
        # recolección). Las Completado sin ``fecha_entrega`` caen al
        # denominador pero no al numerador → se contabilizan como no
        # cumplidas, que es el comportamiento correcto.
        #
        # ``COUNT(CASE WHEN ...)`` maneja NULLs: ``date(NULL)`` es NULL,
        # y ``NULL <= date(...)`` es NULL, que el CASE trata como no-match,
        # así que las NULL no entran al numerador. OK.
        row = self.db.fetch_one("""
            SELECT
                COUNT(CASE WHEN fecha_entrega IS NOT NULL
                            AND date(fecha_entrega) <= date(fecha_recoleccion, '+3 days')
                           THEN 1 END) * 100.0 / COUNT(*) as tasa
            FROM muestras
            WHERE estado = 'Completado'
        """)
        metrics['tasa_cumplimiento'] = round(
            row['tasa'], 1) if row and row['tasa'] is not None else 0

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
        # RBAC: cualquier usuario autenticado
        self.authorizer.require_authenticated()

        query = """
            SELECT m.*, a.nombre as animal_nombre, a.codigo as animal_codigo
            FROM muestras m
            LEFT JOIN animales a ON m.animal_id = a.id
            WHERE date(m.fecha_recoleccion) >= ? AND date(m.fecha_recoleccion) <= ?
            ORDER BY m.fecha_recoleccion DESC
        """
        rows = self.db.fetch_all(query, (fecha_inicio, fecha_fin))
        return [dict(row) for row in rows]
