# 🧪 IsaLab — Centro de Diagnóstico Veterinario

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![PySide6](https://img.shields.io/badge/UI-PySide6-green.svg)
![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-red.svg)
![License](https://img.shields.io/badge/License-Proprietary-lightgrey.svg)
![CI](https://github.com/CORJAR-Computers/ISALAB/actions/workflows/ci.yml/badge.svg)

**IsaLab** es un sistema integral de gestión clínica y de laboratorio enfocado
en Centros de Diagnóstico Veterinario. Desarrollado con **Python** y
**PySide6**, ofrece una interfaz de usuario moderna, rápida y accesible para
administrar consultas, cirugías, muestras analíticas, historiales clínicos,
vacunación y emisión de reportes médicos en PDF.

---

## 🚀 Características Principales

### 🐾 Gestión de Pacientes y Propietarios
- Registro de mascotas (caninos, felinos y otras especies).
- Expediente clínico completo con datos de propietarios, historial de visitas
  y antecedentes.

### 🧪 Módulo de Laboratorio y Muestras
- Control de ingreso y recepción de muestras (sangre, orina, heces,
  citologías, biopsias, etc.).
- Seguimiento de estados en tiempo real (*Pendiente*, *En Proceso*,
  *Completado*, *Descartado*).
- Identificadores y códigos estandarizados de muestra.

### 🩺 Gestión Clínica Integral
- **Consultas Médicas:** Registro de motivo, diagnóstico, constantes vitales
  y tratamientos.
- **Cirugías y Anestesia:** Programación de intervenciones, registro de tipos
  de anestesia y protocolos postoperatorios.
- **Vacunación y Desparasitación:** Control de esquemas de vacunación por
  especie (canina/felina) y vías de administración.

### 📊 Dashboards y Reportes Médicos
- **Dashboard Estadístico:** Gráficos dinámicos e interactivos desarrollados
  con Matplotlib.
- **Generación de Reportes PDF:** Exportación directa de historiales clínicos
  y resultados de laboratorio listos para imprimir o enviar al cliente, usando
  **WeasyPrint + Jinja2** (HTML+CSS → PDF).

### 🎨 Interfaz Moderna & Accesible (Healthcare UI)
- Diseñada siguiendo estándares **WCAG AA/AAA** para entornos médicos y
  clínicos.
- Soporte para **Tema Claro (Light)** y **Tema Oscuro (Dark)**.
- Pantalla de carga (Splash Screen) y asistente de instalación inicial en
  primera ejecución.

### 🔐 Seguridad y Control de Acceso
- Autenticación de usuarios con cifrado de contraseñas (**bcrypt**).
- Control de roles y permisos de acceso (RBAC).
- Asistente de configuración inicial cuando no existen usuarios registrados.

---

## 🛠️ Tecnologías Utilizadas

- **Lenguaje:** Python 3.10+
- **Interfaz Gráfica (GUI):** PySide6 (Qt for Python)
- **Base de Datos & ORM:** SQLite, SQLAlchemy 2.x, Alembic (migraciones)
- **Generación de Reportes:** WeasyPrint + Jinja2 (HTML+CSS → PDF)
- **Visualización de Datos:** Matplotlib
- **Validación de Datos:** Pydantic 2.x
- **Hashing de contraseñas:** bcrypt
- **Empaquetado:** PyInstaller

> ℹ️ **Nota histórica:** Versiones anteriores usaban CustomTkinter y ReportLab.
> Esas dependencias fueron removidas en Fase 1 del roadmap de refactor.

---

## 📁 Estructura del Proyecto

```text
ISALAB/
├── .github/workflows/  # CI/CD (lint, tests, build .exe)
├── alembic/            # Migraciones de base de datos
├── assets/             # Recursos visuales (logotipos, iconos .ico y .png)
├── database/           # Conexión, modelos y repositorios SQLite
├── gui_pyside/         # Componentes, vistas y diálogos en PySide6
│   ├── components/     # Componentes de UI reutilizables
│   ├── dialogs/        # Ventanas emergentes (Login, Instalador, etc.)
│   ├── utils/          # Helpers (mensajes, window_manager)
│   ├── views/          # Pantallas principales (Muestras, Consultas, Cirugías, etc.)
│   └── splash.py       # Pantalla de carga animada
├── orm_models/         # Modelos SQLAlchemy 2.x declarativos
├── reports/            # Generadores de PDF (WeasyPrint + Jinja2)
├── services/           # Lógica de negocio y servicios del sistema
├── templates/          # Plantillas HTML para reportes PDF
├── tests/              # Suite de pruebas con pytest
├── utils/              # Utilidades (logging, validación, seguridad)
├── AGENTS.md           # Notas para agentes AI que trabajen en el repo
├── ARCHITECTURE.md     # Documentación de arquitectura
├── SECURITY.md         # Política de seguridad y reporte de vulnerabilidades
├── alembic.ini         # Configuración de Alembic
├── build_app.py        # Script para compilar la aplicación a ejecutable .exe
├── config.py           # Configuración global, constantes y sistema de temas
├── IsaLab.spec         # Spec de PyInstaller
├── main.py             # Punto de entrada principal de la aplicación
├── pyproject.toml      # Tooling config (ruff, black, mypy, pytest)
├── requirements.txt    # Dependencias de runtime
├── requirements-dev.txt# Dependencias de desarrollo (linters, tests, build)
└── .env.example        # Plantilla de variables de entorno
```

> 📖 Para detalle de capas y responsabilidades, ver
> [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## 📥 Instalación y Configuración

### 1. Requisitos Previos
- **Python 3.10** o superior.
- En Linux: `libpango-1.0-0` y `libpangoft2-1.0-0` (requeridos por WeasyPrint).
- En Windows: Visual C++ Redistributable (incluido en instalaciones recientes).

### 2. Clonar el Repositorio
```bash
git clone https://github.com/CORJAR-Computers/ISALAB.git
cd ISALAB
```

### 3. Crear y Activar un Entorno Virtual
En Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

En Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Configurar Variables de Entorno
```bash
cp .env.example .env
# Edita .env según tu entorno (modo desarrollo, log level, etc.)
```

### 5. Instalar Dependencias
```bash
# Solo runtime:
pip install -r requirements.txt

# O runtime + herramientas de desarrollo (recomendado):
pip install -r requirements-dev.txt
pip install -e .
```

### 6. Inicializar la Base de Datos
```bash
alembic upgrade head
```

---

## ⚡ Ejecución

Para iniciar la aplicación en entorno de desarrollo:

```bash
python main.py
```

Para imprimir la versión y salir (útil para scripts de CI / empaquetado):

```bash
python main.py --version   # o: python main.py -V
```

En la primera ejecución, el sistema detectará que no existen usuarios
registrados y desplegará automáticamente un asistente de instalación para
crear la cuenta de administrador.

---

## 📦 Compilación a Ejecutable (.exe en Windows)

El proyecto incluye un script de compilación automatizado con **PyInstaller**
y un manifiesto de Windows para garantizar que el icono en la barra de tareas
se muestre de forma independiente:

```bash
# Build de producción (default): consola oculta, optimize=2 (strips docstrings)
python build_app.py
```

Para builds de **diagnóstico** (con consola visible para ver `print`s y
tracebacks, y `optimize=0` para preservar docstrings/asserts):

```bash
# Pasa --debug y se setea ISALAB_DEBUG=1 automáticamente:
python build_app.py --debug
```

> ⚙️ **Cómo funciona el flag `--debug`**: `build_app.py` exporta
> `ISALAB_DEBUG=1` en el entorno del subprocess de PyInstaller. El archivo
> `IsaLab.spec` lee esa variable para fijar `console=True` (en vez de
> `False`) y `optimize=0` (en vez de `2`). Esto evita tener que editar el
> `.spec` manualmente para depurar. Si compilas directamente con
> `pyinstaller IsaLab.spec` sin pasar por `build_app.py`, puedes setear la
> variable a mano:
>
> ```bash
> # En PowerShell:
> $env:ISALAB_DEBUG=1
> pyinstaller --noconfirm IsaLab.spec
> ```
>
> (En Linux/macOS: `ISALAB_DEBUG=1 pyinstaller --noconfirm IsaLab.spec`.)

El ejecutable compilado estará disponible en la carpeta:
`dist/IsaLab/IsaLab.exe`

---

## 🧪 Pruebas (Testing)

```bash
# Ejecutar toda la suite con cobertura:
pytest

# Solo tests rápidos (excluye lentos):
pytest -m "not slow"

# Solo tests de servicios:
pytest tests/test_services/

# Ver reporte HTML de cobertura:
# (se genera en htmlcov/index.html)
```

> ℹ️ Los tests corren automáticamente en CI sobre Python 3.10/3.11/3.12
> en Ubuntu y Windows. Ver [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

---

## 🛠️ Calidad de Código

El proyecto usa **Ruff** (linter + formatter), **Black** (formatter) y
**Mypy** (type-checker). Para correrlos localmente:

```bash
ruff check .
black --check .
mypy --ignore-missing-imports database services utils
```

Para instalar los hooks de pre-commit (corren automáticamente antes de cada
commit):

```bash
pre-commit install
pre-commit run --all-files  # primer run
```

---

## 🤝 Contribuir

1. Crea un fork del repositorio.
2. Crea una rama desde `develop`: `git checkout -b feat/mi-mejora`.
3. Haz tus cambios siguiendo Conventional Commits (`feat:`, `fix:`, etc.).
4. Asegúrate de que pasen los tests: `pytest`.
5. Abre un Pull Request contra `develop`.

Para detalles de arquitectura antes de contribuir, leer
[`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## 📄 Licencia

Derechos Reservados © 2026 CORJAR Computers / IsaLab - Centro de Diagnóstico
Veterinario. Uso interno y autorizado. Ver archivo [`LICENSE`](LICENSE).

Para reportar vulnerabilidades de seguridad, ver [`SECURITY.md`](SECURITY.md).
