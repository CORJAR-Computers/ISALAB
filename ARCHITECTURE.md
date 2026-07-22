# Arquitectura de IsaLab

> **Estado:** Documento vivo. Última revisión: Fase 1 (higiene de repositorio).
> **Audiencia:** Desarrolladores nuevos y mantenedores del proyecto.

---

## 1. Visión general

IsaLab es un sistema de escritorio (no web) para la gestión de un centro de
diagnóstico veterinario: pacientes animales, propietarios, recepción de
muestras de laboratorio, consultas clínicas, cirugías, vacunación, historias
clínicas y emisión de reportes médicos en PDF.

La aplicación está construida con **Python 3.10+** y **PySide6** (Qt for
Python). Persiste en **SQLite** mediante **SQLAlchemy 2.x** como ORM y
**Alembic** para migraciones de esquema. Los PDFs se generan con
**WeasyPrint** + **Jinja2** (HTML+CSS → PDF), NO con ReportLab.

```
┌────────────────────────────────────────────────────────────┐
│                      main.py (entry point)                 │
│   Splash → Login → LabVetApp (ventana principal)           │
└──────────────────────────┬─────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        ▼                                     ▼
┌───────────────────┐                ┌──────────────────┐
│   gui_pyside/     │                │     services/    │
│  (vistas PySide6) │  ── llama ──▶  │  (lógica negocio)│
│                   │                │                  │
│  views/           │                │  usuario_service │
│  dialogs/         │                │  animal_service  │
│  components/      │                │  muestra_service │
│  utils/           │                │  recepcion_...   │
│  styles.py        │                │  consulta_...    │
└────────┬──────────┘                │  cirugia_...     │
         │                           │  vacuna_...      │
         │                           │  historia_...    │
         │                           │  report_*.py     │
         │                           └────────┬─────────┘
         │                                    │
         ▼                                    ▼
┌───────────────────┐                ┌──────────────────┐
│   reports/        │                │   database/      │
│  (generadores PDF)│  ◀── usa ──   │  connection.py   │
│   generators.py   │                │  repositories.py │
│   base.py         │                │  models.py       │
│   helpers.py      │                └────────┬─────────┘
└───────────────────┘                         │
                                              ▼
                                    ┌──────────────────┐
                                    │  SQLite (file)   │
                                    │  data/isalab.db  │
                                    └──────────────────┘
```

---

## 2. Capas y responsabilidades

### 2.1. `config.py`
Configuración global: paths (`BUNDLE_DIR`, `APP_DIR`, `DB_PATH`, `ASSETS_DIR`),
temas (`THEME_LIGHT`, `THEME_DARK`), validaciones, íconos. Todo módulo debe
importar paths desde aquí, nunca construirlos con `Path.cwd()`.

### 2.2. `database/` (capa de datos)
- `connection.py` — `DatabaseManager` (singleton, thread-local sessions).
- `repositories.py` — patrón Repository para cada tabla.
- `models.py` — esquema de tablas (Pydantic schemas para I/O).

### 2.3. `orm_models/` (ORM SQLAlchemy 2.x)
Modelos declarativos que mapean a las tablas. **Nota:** existe un anti-patrón
documentado en el análisis (Tarea 3) donde algunos servicios usan `sqlite3`
crudo en paralelo al ORM — pendiente de corregir en Fase 2.

### 2.4. `services/` (lógica de negocio)
Servicios por dominio: `usuario_service.py`, `animal_service.py`,
`muestra_service.py`, `recepcion_service.py`, `consulta_service.py`,
`cirugia_service.py`, `vacuna_service.py`, `historia_service.py`,
`configuracion_service.py`. Más los generadores de reportes (`report_*.py`,
`pdf_service.py`).

### 2.5. `gui_pyside/` (UI)
- `app.py` — ventana principal `LabVetApp` con sidebar y content area.
- `views/` — pantallas principales (dashboard, animales, muestras, …).
- `dialogs/` — formularios modales (login, nuevo paciente, nueva muestra, …).
- `components/` — widgets reutilizables (`DataTable`, `SearchBar`, `FormField`).
- `utils/` — helpers de UI (`messages.py`, `window_manager.py`).
- `styles.py` — sistema de temas.
- `splash.py` — pantalla de carga inicial.

### 2.6. `reports/` (generación PDF)
- `generators.py` — `ReportGenerator` con Jinja2 + WeasyPrint.
- `base.py` — clase base con autoescape habilitado.
- `helpers.py` — utilidades (imágenes a base64, formato de fechas, etc.).
- `templates/` — plantillas HTML de cada reporte.

### 2.7. `utils/`
- `security.py` — `Authorizer` (RBAC), hashing bcrypt, validación de password.
- `validators.py` — validadores de dominio (DNI, teléfono, código, etc.).
- `exceptions.py` — jerarquía `IsaLabException`.
- `logger.py` — configuración de logging.

### 2.8. `alembic/`
Migraciones de esquema. Comando: `alembic upgrade head`. La URL se inyecta
desde `config.DB_PATH` (no usar el valor de `alembic.ini`).

---

## 3. Decisiones técnicas

### ¿Por qué SQLite y no PostgreSQL?
La aplicación es de escritorio, instalada en clínicas veterinarias sin
infraestructura de servidor. SQLite es un único archivo (`data/isalab.db`)
respaldable copiando el archivo. Cuando la app escale a multi-sucursal, se
migrará a PostgreSQL sin tocar la capa de servicios (solo `config.DB_PATH`
y `alembic/env.py`).

### ¿Por qué PySide6 y no web?
Los usuarios son personal de clínica que trabaja con una sola máquina por
puesto. La UI de escritorio permite mejor manejo de impresoras, escáneres de
código de barras y modo offline. Si en el futuro se necesita acceso remoto,
se evaluará una capa FastAPI sobre los servicios existentes.

### ¿Por qué WeasyPrint y no ReportLab?
WeasyPrint permite diseñar reportes con HTML+CSS (más mantenible y permite a
diseñadores trabajar sin tocar Python). ReportLab requiere construir el PDF
programáticamente, lo que hace difícil iterar el diseño.

---

## 4. Roadmap de refactor

El proyecto fue entregado con un solo commit de 39 KLOC. El plan de refactor
está organizado en fases:

| Fase | Alcance                                              | Estado |
|------|------------------------------------------------------|--------|
| 1    | Higiene del repo + setup tooling (este commit)       | ✅     |
| 2    | Fix CRITICAL de base de datos (cadena Alembic, etc.) | ⏳     |
| 3    | Fix CRITICAL de seguridad (RBAC, Jinja autoescape)   | ⏳     |
| 4    | Fix CRITICAL de GUI (Dashboard, `os.startfile`, …)   | ⏳     |
| 5    | Issues HIGH (N+1 queries, hilos Qt, etc.)            | ⏳     |
| 6    | Issues MEDIUM y LOW                                  | ⏳     |

El detalle de cada issue está documentado en el worklog interno del equipo.

---

## 5. Convenciones

- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`,
  `test:`, `chore:`, `ci:`). Tag `ISALAB` para issues del roadmap.
- **Branches:** `main` (estable), `develop` (integración),
  `feat/<topic>`, `fix/<topic>`.
- **Estilo:** Ruff + Black (configurado en `pyproject.toml`).
- **Tests:** Cobertura mínima 30 % al inicio, objetivo 70 % en Fase 5.
