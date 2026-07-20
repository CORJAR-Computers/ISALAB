# IsaLab — Fase 2: Fix CRITICAL de Base de Datos

Este paquete contiene los parches y scripts para aplicar la **Fase 2** del
roadmap de refactor de IsaLab: fix de los 4 issues CRITICAL y 2 issues HIGH
de la capa de base de datos.

---

## 📦 Contenido del paquete

```
ISALAB-fase2/
├── README.md                                              ← Este archivo
├── patches/
│   ├── 0001-fix-ISALAB-Fase-2-Fix-CRITICAL-de-...patch   ← Parche consolidado (53 KB)
│   ├── alembic_env.patch                                  ← Parche individual: env.py
│   ├── alembic_versions_8f3a2c1d4e5f_merge_heads_fase2.patch
│   ├── alembic_versions_agregar_created_at_usuarios.patch
│   ├── alembic_versions_e03e74d43e0d_...patch
│   ├── database_connection.patch
│   ├── database_repositories.patch
│   ├── gui_pyside_views_historia.patch
│   └── tests_test_fase2_database.patch
├── scripts/
│   ├── apply-phase2.ps1                                   ← Windows (PowerShell)
│   └── apply-phase2.sh                                    ← Linux/Mac/Git Bash
└── files/                                                 ← 8 archivos sueltos para inspección
```

> **Recomendación:** usa el **parche consolidado** + **script** (opción A abajo).

---

## 🎯 Qué hace Fase 2

### Issue C1 — Cadena Alembic rota (multi-head) ✅

**Síntoma:** `alembic upgrade head` falla con:
```
CommandError: Multiple head revisions are present for given argument 'head';
agregar_created_at_todas_tablas, agregar_created_at_usuarios
```

**Causa:** las migraciones `agregar_created_at_todas_tablas` y
`agregar_created_at_usuarios` ambas declaraban `down_revision = '38d0897cfe7e'`,
generando dos heads paralelos sin merge.

**Fix:** nueva migración `8f3a2c1d4e5f_merge_heads_fase2.py` cuyo
`down_revision` es la tupla de ambos heads, unificando la cadena en un solo head.

### Issue C2 — `create_table('animales')` duplicado ✅

**Síntoma:** en una DB nueva, `alembic upgrade head` fallaba con:
```
sqlite3.OperationalError: table animales already exists
```

**Causa:** la migración `e03e74d43e0d` hacía `op.create_table('animales', ...)`
(y otras 7 tablas) que YA habían sido creadas por la baseline `5688c877a6a6`.
La intención real era AGREGAR columnas nuevas a las tablas existentes.

**Fix:** reescrita `e03e74d43e0d_agregados_datos_propietario_y_empresa.py`
para usar `op.add_column()` idempotente (verifica `PRAGMA table_info` antes
de agregar cada columna).

### Issue C3 — Columna `password` vs `password_hash` ✅

**Síntoma:** si Alembic creaba la tabla `usuarios` antes que
`DatabaseManager.__init__`, el login fallaba con:
```
sqlite3.OperationalError: no such column: password_hash
```

**Causa:** la migración `agregar_created_at_usuarios` creaba la tabla con
columna `password` (sin `_hash`), pero `usuario_service.py` y
`database/connection.py` usan `password_hash`.

**Fix:** reescrita `agregar_created_at_usuarios.py` para:
- Si la tabla no existe: crearla con `password_hash` (idéntico a
  `connection.py`) + `UNIQUE(username)` + trigger de CHECK de rol.
- Si la tabla existe con `password` pero no `password_hash`: rename de la
  columna (vía batch mode de Alembic, que recrea la tabla en SQLite).
- Agregar `created_at` y `ultimo_acceso` si faltan.

### Issue C4 — Anti-patrón dual sqlite3 + SQLAlchemy (parcial) ✅

**Síntoma:** `gui_pyside/views/historia.py:203` ejecutaba SQL crudo vía
`repo.db.fetch_all(...)` saltándose la capa de repositorio.

**Causa:** `HistoriaClinicaRepository` no tenía método `get_all()` (patrón
inconsistente con los demás repositorios).

**Fix:**
- Agregado `HistoriaClinicaRepository.get_all(filtros=None)` con joins de
  animal y recepción.
- `gui_pyside/views/historia.py` actualizado para usar `repo.get_all()`.

> **Nota:** el anti-patrón dual-access persiste en `database/connection.py`
> (coexistencia de `sqlite3` raw + SQLAlchemy `SessionLocal` en el mismo
> archivo). Su refactor completo queda para Fase 6 (issues MEDIUM).

### Issue M8 — URL Alembic incorrecta ✅

**Síntoma:** `alembic upgrade head` creaba `./isalab.db` en el CWD en vez de
usar `data/isalab.db`.

**Causa:** `alembic.ini` tenía `sqlalchemy.url = sqlite:///isalab.db`
hardcoded (corregido a vacío en Fase 1), pero `alembic/env.py` no inyectaba
la URL desde `config.DB_PATH`.

**Fix:** `alembic/env.py` ahora importa `DB_PATH` de `config.py` y ejecuta
`config.set_main_option('sqlalchemy.url', ...)`. También activa
`render_as_batch=True` para soportar `alter_column` en SQLite.

### HIGH — `AnimalRepository.update` pierde 12 campos ✅

**Síntoma:** al editar un animal desde la GUI, se perdían 12 campos:
`codigo, sexo, color, tipo_pelo, senas_particulares, microchip, unidad_edad,
fecha_nacimiento, propietario_tipo_doc, propietario_documento,
propietario_direccion, propietario_oficio`.

**Causa:** `AnimalRepository.update()` solo persistía 13 de los 25 campos
editables del modelo `Animal`.

**Fix:** `database/repositories.py:114` ahora persiste los 22 campos editables.

### HIGH — Thread-local connection leak ✅

**Síntoma:** al cerrar la app, las conexiones abiertas por threads
secundarios (workers de PDF, queries async) quedaban abiertas, causando
`database is locked` en siguientes accesos.

**Causa:** `DatabaseManager.close_all_connections()` solo cerraba
`self._local.connection` (la del thread actual).

**Fix:** agregado `self._all_connections: list` (registry thread-safe con
`_connections_lock`). Cada `get_connection()` registra la nueva conexión.
`close_all_connections()` las recorre todas.

### Tests de regresión ✅

`tests/test_fase2_database.py` — 7 tests nuevos:

1. `test_alembic_upgrade_head_no_multiple_heads` (C1)
2. `test_alembic_upgrade_head_creates_all_tables` (C2 parcial)
3. `test_alembic_no_duplicate_create_table_animales` (C2)
4. `test_usuarios_table_has_password_hash_not_password` (C3)
5. `test_animal_repository_update_persists_all_fields` (HIGH)
6. `test_historia_repository_get_all_exists` (C4)
7. `test_close_all_connections_closes_other_thread_connections` (HIGH)

---

## 🚀 Cómo aplicar (3 opciones)

### Opción A — Script automático (RECOMENDADA)

#### Windows (PowerShell)

```powershell
cd C:\ruta\a\ISALAB
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
C:\ruta\a\ISALAB-fase2\scripts\apply-phase2.ps1 -DryRun   # verificar primero
C:\ruta\a\ISALAB-fase2\scripts\apply-phase2.ps1            # aplicar
```

#### Linux / macOS / Git Bash

```bash
cd /ruta/a/ISALAB
bash /ruta/a/ISALAB-fase2/scripts/apply-phase2.sh --dry-run  # verificar
bash /ruta/a/ISALAB-fase2/scripts/apply-phase2.sh            # aplicar
```

El script:
- Verifica que Fase 1 esté aplicada.
- Crea la rama `feat/phase2-database-critical`.
- Aplica el parche consolidado (8 archivos).
- Corre `alembic upgrade head` en una DB temporal para verificar que la
  cadena funciona.
- Hace commit con mensaje Convencional Commits + tag `ISALAB`.
- **NO hace push**.

### Opción B — Aplicar el parche manualmente

```bash
git checkout -b feat/phase2-database-critical
git apply --whitespace=fix patches/0001-fix-ISALAB-Fase-2-Fix-CRITICAL-de-base-de-datos.patch
git add -A
git commit -m "fix(ISALAB): Fase 2 — Fix CRITICAL de base de datos"
```

### Opción C — Aplicar parches individuales por archivo

Si quieres aplicar selectivamente (por ejemplo, solo la cadena Alembic):

```bash
git checkout -b feat/phase2-database-critical

# Solo cadena Alembic (issues C1, C2, C3)
git apply patches/alembic_env.patch
git apply patches/alembic_versions_8f3a2c1d4e5f_merge_heads_fase2.patch
git apply patches/alembic_versions_agregar_created_at_usuarios.patch
git apply patches/alembic_versions_e03e74d43e0d_agregados_datos_propietario_y_empresa.patch

# Solo fixes de repositorios (issues HIGH, C4)
git apply patches/database_connection.patch
git apply patches/database_repositories.patch
git apply patches/gui_pyside_views_historia.patch

# Tests de regresión
git apply patches/tests_test_fase2_database.patch

git add -A
git commit -m "fix(ISALAB): Fase 2 — Fix CRITICAL de base de datos"
```

---

## 🖥️ Cómo seguir con GitHub Desktop

1. **Abre GitHub Desktop** y selecciona el repo ISALAB.
2. Verás la rama `feat/phase2-database-critical` con 1 commit nuevo.
3. **Publica la rama** → botón "Publish branch".
4. **Abre un Pull Request** → botón "Pull request" (o `Ctrl+R`).
   - Base: `main` (o `develop`).
   - Título: `Fase 2 — Fix CRITICAL de base de datos`.
5. **Antes de mergear**, verifica en la pestaña **Actions** que el CI pase
   (lint + tests).

---

## 🧪 Cómo verificar manualmente después de aplicar

```bash
# 1. Instalar dependencias (si no están):
pip install -r requirements-dev.txt

# 2. Borrar DB existente y recrear desde cero:
rm -f data/isalab.db
alembic upgrade head
# Debe mostrar: Running upgrade ... -> 8f3a2c1d4e5f, merge_heads_fase2

# 3. Verificar head:
python -c "import sqlite3; conn = sqlite3.connect('data/isalab.db'); print([r[0] for r in conn.execute('SELECT version_num FROM alembic_version')])"
# Debe mostrar: ['8f3a2c1d4e5f']

# 4. Verificar que usuarios tiene password_hash:
python -c "import sqlite3; conn = sqlite3.connect('data/isalab.db'); cols = [r[1] for r in conn.execute('PRAGMA table_info(usuarios)')]; print('password_hash' in cols, 'password' not in cols)"
# Debe mostrar: True True

# 5. Verificar que no hay tablas duplicadas:
python -c "import sqlite3; conn = sqlite3.connect('data/isalab.db'); print([r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='animales'\")])"
# Debe mostrar exactamente: ['animales']

# 6. Correr tests de regresión:
pytest tests/test_fase2_database.py -v
```

---

## ⚠️ Migración de DB existente

Si ya tienes una `data/isalab.db` con datos reales (probablemente con la
tabla `usuarios` ya creada por `DatabaseManager`):

### Escenario 1: DB creada por `DatabaseManager` (caso común)

Tu tabla `usuarios` ya tiene `password_hash` (no `password`). La migración
lo detectará y solo agregará `created_at` y `ultimo_acceso` si faltan. **No
hay pérdida de datos.**

### Escenario 2: DB creada por `alembic upgrade head` (caso raro)

Tu tabla `usuarios` tenía `password` (sin `_hash`). La migración hace
`ALTER TABLE usuarios RENAME COLUMN password TO password_hash` (vía batch
mode de Alembic). **Los hashes se preservan, solo cambia el nombre de la
columna.** Verifica después:

```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/isalab.db')
for row in conn.execute('SELECT id, username, substr(password_hash, 1, 20) FROM usuarios LIMIT 5'):
    print(row)
"
```

### Escenario 3: DB nueva (caso limpio)

Borra `data/isalab.db`, corre `alembic upgrade head`, y el instalador de
primera ejecución te pedirá crear el admin.

---

## 🆘 Troubleshooting

### `alembic upgrade head` falla con "table already exists"

Esto puede pasar si tu DB existente no está registrada en `alembic_version`.
Solución:

```bash
# 1. Backup
cp data/isalab.db data/isalab.db.bak

# 2. Marcar la DB como que ya está en la baseline
alembic stamp 5688c877a6a6

# 3. Ahora upgrade debería funcionar
alembic upgrade head
```

### El rename de `password` a `password_hash` falla

Si tienes una versión vieja de SQLite que no soporta `ALTER TABLE RENAME
COLUMN` (anterior a 3.25.0), Alembic usará batch mode (recreación de tabla).
Asegúrate de tener SQLite ≥ 3.25.0:

```bash
python -c "import sqlite3; print(sqlite3.sqlite_version)"
```

### Los tests fallan con `ModuleNotFoundError: bcrypt`

```bash
pip install -r requirements-dev.txt
```

### `git apply` falla con conflictos

Si modificaste alguno de los archivos afectados, usa `--3way`:

```bash
git apply --3way patches/0001-fix-ISALAB-Fase-2-Fix-CRITICAL-de-base-de-datos.patch
```

O aplica los parches individuales uno por uno (Opción C arriba).

---

## 📋 Issues del worklog cubiertos por Fase 2

| Severidad | Issues | Estado |
|-----------|--------|--------|
| CRITICAL  | C1 (multi-head), C2 (create_table dup), C3 (password_hash), C4 (dual-access, parcial), C5 (URL Alembic) | ✅ |
| HIGH      | AnimalRepository.update (12 campos), close_all_connections (thread leak) | ✅ |
| MEDIUM    | M8 (URL Alembic en env.py) | ✅ |

**Pendientes para Fase 3+:**
- Fase 3: Fix CRITICAL de seguridad (RBAC bypass, Jinja2 sin autoescape,
  PermissionError shadowing, colisión ISAL-0001).
- Fase 4: Fix CRITICAL de GUI (Dashboard no-op, `os.startfile` cross-platform,
  logo case-sensitive, `ref_text` AttributeError).
- Fase 6: Anti-patrón dual-access completo en `database/connection.py`
  (refactor mayor: eliminar sqlite3 raw, usar solo SQLAlchemy).

---

## ❓ Dudas

Si algo no funciona, abre un issue en
https://github.com/CORJAR-Computers/ISALAB/issues con etiqueta `phase2` y
adjunta el output completo del comando que falló.
