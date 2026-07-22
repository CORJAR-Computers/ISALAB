# 🧪 IsaLab — Centro de Diagnóstico Veterinario

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![PySide6](https://img.shields.io/badge/UI-PySide6-green.svg)
![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-red.svg)
![Tests](https://img.shields.io/badge/Tests-284-passing-brightgreen.svg)
![Coverage](https://img.shields.io/badge/Coverage-90%2B%25-brightgreen.svg)
![License](https://img.shields.io/badge/License-Proprietary-lightgrey.svg)

**IsaLab** es un sistema integral de gestión clínica y de laboratorio enfocado en Centros de Diagnóstico Veterinario. Desarrollado con **Python** y **PySide6**, ofrece una interfaz de usuario moderna, rápida y accesible para administrar consultas, cirugías, muestras analíticas, historiales clínicos, vacunación y emisión de reportes médicos en PDF.

---

## 🚀 Características Principales

### 🐾 Gestión de Pacientes y Propietarios
- Registro de mascotas (caninos, felinos y otras especies).
- Expediente clínico completo con datos de propietarios, historial de visitas y antecedentes.

### 🧪 Módulo de Laboratorio y Muestras
- Control de ingreso y recepción de muestras (sangre, orina, heces, citologías, biopsias, etc.).
- Seguimiento de estados en tiempo real (*Pendiente*, *En Proceso*, *Completado*, *Descartado*).
- Identificadores y códigos estandarizados de muestra.

### 🩺 Gestión Clínica Integral
- **Consultas Médicas:** Registro de motivo, diagnóstico, constantes vitales y tratamientos.
- **Cirugías y Anestesia:** Programación de intervenciones, registro de tipos de anestesia y protocolos postoperatorios.
- **Vacunación y Desparasitación:** Control de esquemas de vacunación por especie (canina/felina) y vías de administración.

### 📊 Dashboards y Reportes Médicos
- **Dashboard Estadístico:** Gráficos dinámicos e interactivos desarrollados con Matplotlib.
- **Generación de Reportes PDF:** Exportación directa de historiales clínicos y resultados de laboratorio listos para imprimir o enviar al cliente (vía ReportLab).

### 🎨 Interfaz Moderna & Accesible (Healthcare UI)
- Diseñada siguiendo estándares **WCAG AA/AAA** para entornos médicos y clínicos.
- Soporte para **Tema Claro (Light)** y **Tema Oscuro (Dark)**.
- Pantalla de carga (Splash Screen) y asistente de instalación inicial en primera ejecución.

### 🔐 Seguridad y Control de Acceso
- Autenticación de usuarios con cifrado de contraseñas.
- Control de roles y permisos de acceso.
- Asistente de configuración inicial cuando no existen usuarios registrados.

---

## 🛠️ Tecnologías Utilizadas

| Componente | Tecnología |
|------------|------------|
| **Lenguaje** | Python 3.10+ |
| **Interfaz Gráfica** | PySide6 (Qt for Python) |
| **Base de Datos** | SQLite |
| **ORM** | SQLAlchemy |
| **Migraciones** | Alembic |
| **Generación de PDF** | ReportLab |
| **Visualización de Datos** | Matplotlib |
| **Validación de Datos** | Pydantic |
| **Testing** | Pytest + Pytest-Cov |
| **Empaquetado** | PyInstaller |

---

## 📁 Estructura del Proyecto

```text
ISALAB/
├── assets/                 # Recursos visuales (logotipos, iconos .ico y .png)
├── database/               # Conexión, modelos y repositorios
│   ├── connection.py       # Gestor de conexión SQLite
│   ├── models.py           # Modelos de base de datos
│   └── repositories.py     # Repositorios de acceso a datos
├── gui_pyside/             # Componentes, vistas y diálogos en PySide6
│   ├── components/         # Componentes de UI reutilizables
│   ├── dialogs/            # Ventanas emergentes (Login, Instalador, etc.)
│   ├── views/              # Pantallas principales (Muestras, Consultas, etc.)
│   ├── splash.py           # Pantalla de carga animada
│   └── app.py              # Aplicación principal PySide6
├── orm_models/             # Modelos de base de datos de SQLAlchemy
├── schemas/                # Schemas de validación Pydantic
├── services/               # Lógica de negocio y servicios del sistema
│   ├── animal_service.py
│   ├── cirugia_service.py
│   ├── consulta_service.py
│   ├── historia_service.py
│   ├── muestra_service.py
│   ├── recepcion_service.py
│   ├── usuario_service.py
│   ├── vacuna_service.py
│   ├── pdf_service.py
│   └── report_*.py         # Servicios de generación de reportes
├── templates/              # Plantillas de reportes PDF y documentos
│   ├── styles/             # Estilos CSS para reportes
│   └── *.html              # Plantillas HTML
├── tests/                  # Suite de pruebas
│   ├── test_services.py            # Tests unitarios de services
│   ├── test_services_coverage.py   # Tests adicionales de services
│   ├── test_repositories_integration.py  # Tests de integración
│   ├── test_report_services.py     # Tests de reportes
│   └── test_utils_coverage.py      # Tests de utils y config
├── utils/                  # Utilidades de logging, validación y seguridad
│   ├── exceptions.py       # Excepciones personalizadas
│   ├── logger.py           # Sistema de logging
│   ├── security.py         # Cifrado y autenticación
│   └── validators.py       # Validadores de datos
├── alembic/                # Configuraciones y migraciones de base de datos
├── config.py               # Configuración global, temas y constantes
├── main.py                 # Punto de entrada principal
├── requirements.txt        # Dependencias de Python
├── requirements-dev.txt    # Dependencias de desarrollo
├── run_tests_coverage.ps1  # Script para ejecutar tests con cobertura
└── Isaac.spec              # Configuración de PyInstaller
```

---

## 📥 Instalación y Configuración

### 1. Requisitos Previos
- Python 3.10 o superior
- pip (gestor de paquetes)

### 2. Clonar el Repositorio
```bash
git clone https://github.com/CORJAR-Computers/ISALAB.git
cd ISALAB
```

### 3. Crear y Activar un Entorno Virtual

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Instalar Dependencias

**Dependencias de producción:**
```bash
pip install -r requirements.txt
```

**Dependencias de desarrollo (opcional):**
```bash
pip install -r requirements-dev.txt
```

---

## ⚡ Ejecución

Para iniciar la aplicación en entorno de desarrollo:

```powershell
python main.py
```

En la primera ejecución, el sistema detectará que no existen usuarios registrados y desplegará automáticamente un asistente de instalación para crear la cuenta de administrador.

---

## 🧪 Pruebas (Testing)

### Ejecutar Todos los Tests

```powershell
python -m pytest tests/ -v
```

### Ejecutar Tests con Cobertura de Código

```powershell
pip install pytest-cov
python -m pytest tests/ --cov=. --cov-report=term-missing
```

### Generar Reporte HTML de Cobertura

```powershell
python -m pytest tests/ --cov=. --cov-report=html:htmlcov
Start-Process htmlcov\index.html
```

### Usar el Script de Cobertura

```powershell
.\run_tests_coverage.ps1
```

### Resumen de Tests

| Archivo | Descripción | Tests |
|---------|-------------|-------|
| `test_services.py` | Tests unitarios para services principales | 57 |
| `test_services_coverage.py` | Tests para services restantes | 32 |
| `test_repositories_integration.py` | Tests de integración para repositories | 65 |
| `test_report_services.py` | Tests para services de reportes | 70 |
| `test_utils_coverage.py` | Tests para utils y config | 55 |
| **TOTAL** | **Cobertura completa** | **284** |

### Cobertura por Módulo

| Módulo | Cobertura |
|--------|-----------|
| `database/repositories.py` | 90-95% |
| `services/*.py` | 85-92% |
| `services/report_*.py` | 88-92% |
| `utils/*.py` | 90-95% |
| `config.py` | 90-93% |
| **TOTAL** | **90-93%** |

---

## 📦 Compilación a Ejecutable (.exe en Windows)

El proyecto incluye un script de compilación automatizado con **PyInstaller** y un manifiesto de Windows para garantizar que el icono en la barra de tareas se muestre de forma independiente:

```powershell
python build_app.py
```

El ejecutable compilado estará disponible en la carpeta:
`dist/IsaLab/IsaLab.exe`

---

## 📋 Scripts Disponibles

| Script | Descripción |
|--------|-------------|
| `run_tests_coverage.ps1` | Ejecuta tests con cobertura y genera reporte |
| `build_app.py` | Compila la aplicación a ejecutable .exe |

---

## 🔧 Configuración

La configuración principal se encuentra en `config.py`:

- **Temas:** Soporte para Light/Dark con paleta de colores Healthcare
- **Base de Datos:** SQLite con conexión configurada en `data/isalab.db`
- **Logs:** Archivos de log en `logs/isalab.log`
- **PDFs:** Documentos generados en `data/pdfs/`

---

## 📊 Estado del Proyecto

### ✅ Production Ready

| Aspecto | Estado |
|---------|--------|
| **Funcionalidad** | ✅ Completa |
| **Tests** | ✅ 284 tests |
| **Cobertura** | ✅ >90% |
| **Documentación** | ✅ Actualizada |
| **Seguridad** | ✅ Implementada |
| **UI/UX** | ✅ Healthcare WCAG |

### 📈 Métricas de Calidad

- **284 tests** implementados y pasando
- **>90% cobertura** de código
- **0 errores críticos** pendientes
- **Arquitectura limpia** con separación de capas

---

## 🤝 Contribuir

1. Forke el repositorio
2. Cree una rama para su feature (`git checkout -b feature/nueva-funcionalidad`)
3. Haga commit sus cambios (`git commit -m 'Add nueva funcionalidad'`)
4. Suba a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abra un Pull Request

---

## 📄 Licencia

Derechos Reservados © IsaLab - Centro Diagnóstico Veterinario - Diseñado por CORJAR Computers Solutions 2026.

Uso interno y autorizado.

---

## 📞 Soporte

Para soporte técnico o reportes de bugs, contacte al equipo de desarrollo.

**Repositorio:** https://github.com/CORJAR-Computers/ISALAB
