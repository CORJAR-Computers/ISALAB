# AGENTS.md — Guía para agentes AI que trabajen en IsaLab

> **Audiencia:** Agentes de IA (Claude, Cursor, Copilot, etc.) que lean este
> repo para hacer modificaciones. Resumen ejecutivo de las convenciones y
> estado actual del proyecto.

---

## Identidad del proyecto

- **Nombre:** IsaLab — Centro de Diagnóstico Veterinario
- **Dominio:** Sistema de escritorio para gestión de clínica veterinaria y
  laboratorio (pacientes animales, muestras, consultas, cirugías, vacunación,
  historias clínicas, reportes PDF).
- **Stack:** Python 3.10+, PySide6, SQLAlchemy 2.x, Alembic, WeasyPrint,
  Jinja2, bcrypt, PyInstaller.
- **Repo:** https://github.com/CORJAR-Computers/ISALAB

> ⚠️ **Importante:** Este archivo antes era una copia literal del documento
> genérico "obra/superpowers" con claims falsos sobre "Pizzas Pastra". Ese
> contenido fue reemplazado en Fase 1 del roadmap. NO restaurarlo.

---

## Estado del roadmap de refactor

El proyecto se entregó con un solo commit de 39 KLOC y múltiples deficiencias.
El plan de refactor está organizado en fases:

| Fase | Alcance                                              | Estado  |
|------|------------------------------------------------------|---------|
| 1    | Higiene del repo + setup tooling                     | ✅ Done |
| 2    | Fix CRITICAL de base de datos (Alembic, dual-access) | ⏳ Todo |
| 3    | Fix CRITICAL de seguridad (RBAC, Jinja autoescape)   | ⏳ Todo |
| 4    | Fix CRITICAL de GUI (Dashboard, os.startfile, logo)  | ⏳ Todo |
| 5    | Issues HIGH (N+1, hilos Qt, etc.)                    | ⏳ Todo |
| 6    | Issues MEDIUM y LOW                                  | ⏳ Todo |

Si tu tarea toca una de las áreas pendientes, lee el worklog interno del
equipo para entender los issues ya identificados (no redescubrirlos).

---

## Convenciones que SÍ debes seguir

### Commits
- Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`,
  `chore:`, `ci:`.
- Tag `ISALAB` para issues del roadmap (ej. commit message puede terminar
  con `ISALAB: C1 base de datos` para referenciar el issue CRITICAL C1).

### Branches
- `main` — estable, solo recibe merges de `develop`.
- `develop` — integración activa.
- `feat/<topic>`, `fix/<topic>` — ramas de trabajo.

### Estilo de código
- Ruff + Black configurados en `pyproject.toml`. Ejecutar `pre-commit run
  --all-files` antes de commitear.
- Line length: 100 caracteres.
- Type hints: obligatorios en funciones nuevas; las existentes se tipan
  gradualmente.

### Paths
- NUNCA usar `Path.cwd()` para resolver assets o DB. SIEMPRE importar desde
  `config.py`: `BUNDLE_DIR`, `APP_DIR`, `DB_PATH`, `ASSETS_DIR`.

### Base de datos
- NUNCA usar `sqlite3` directamente. Usar `database/repositories.py` o
  `database/connection.py` (que abstraen SQLAlchemy).
- Para migraciones: `alembic revision --autogenerate -m "descripción"` y
  revisar manualmente el archivo generado.

### Seguridad
- Hashing de passwords: SIEMPRE bcrypt (vía `utils/security.py`).
- Generación de PDFs: SIEMPRE vía `reports/base.py` (que activa Jinja2
  autoescape). NO instanciar `jinja2.Environment` directamente.
- RBAC: SIEMPRE decorar endpoints de servicios con `Authorizer.require_role`
  (importar de `utils/security.py`).

### Tests
- Todo nuevo servicio o fix de bug debe venir con tests.
- Usar fixtures de `tests/conftest.py` (`qapp`, `tmp_db_path`).
- Marcadores: `@pytest.mark.slow`, `@pytest.mark.integration`, `@pytest.mark.gui`.

---

## Errores comunes a evitar

1. **No regenerar el `data/isalab.db`** — Si necesitas una DB limpia para
   desarrollo, bórrala y corre `alembic upgrade head`. El asistente de
   primera ejecución te pedirá crear el admin.

2. **No commitear `data/`, `logs/`, `*.pyc`, `__pycache__/`, `.idea/`,
   `.vscode/`, ni archivos `.env`** — El `.gitignore` los excluye, pero
   `git add -A` puede resucitarlos si se hace desde un checkout viejo.
   Verificar siempre con `git status` antes de commitear.

3. **No usar `os.startfile()` directamente** — Es Windows-only. Si necesitas
   abrir un archivo en el explorador del SO, usar `QDesktopServices.openUrl`
   de PySide6. (Issue CRITICAL de GUI pendiente en Fase 4.)

4. **No instanciar servicios en `__init__` de vistas** — Hace imposible
   swapear el contexto. Mejor lazy-init o inyección por parámetro. (Issue
   HIGH de GUI pendiente en Fase 5.)

5. **No usar `QThread` sin `deleteLater()`** — Filtra memoria y puede crashear
   al cerrar la app. (Issue HIGH de GUI pendiente en Fase 5.)

---

## Recursos útiles

- `ARCHITECTURE.md` — Diagrama de capas y responsabilidades.
- `SECURITY.md` — Política de seguridad y vulnerabilidades conocidas.
- `README.md` — Setup, ejecución, build, tests.
- `pyproject.toml` — Configuración de tooling.
- `.github/workflows/ci.yml` — Pipeline de CI (lint, tests, build).
- `tests/conftest.py` — Fixtures de pytest (DB temporal, QApplication).
