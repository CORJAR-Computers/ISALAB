# 🧪 IsaLab — Centro de Diagnóstico Veterinario

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![PySide6](https://img.shields.io/badge/UI-PySide6-green.svg)
![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-red.svg)
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

- **Lenguaje:** Python 3.10+
- **Interfaz Gráfica (GUI):** PySide6 (Qt for Python), CustomTkinter
- **Base de Datos & ORM:** SQLite, SQLAlchemy, Alembic (migraciones)
- **Generación de Reportes:** ReportLab (PDF)
- **Visualización de Datos:** Matplotlib
- **Validación de Datos:** Pydantic
- **Empaquetado:** PyInstaller

---

## 📁 Estructura del Proyecto

```text
ISALAB/
├── assets/             # Recursos visuales (logotipos, iconos .ico y .png)
├── database/           # Conexión, inicialización y gestor de SQLite
├── gui_pyside/         # Componentes, vistas y diálogos en PySide6
│   ├── components/     # Componentes de UI reutilizables
│   ├── dialogs/        # Ventanas emergentes (Login, Instalador, etc.)
│   ├── views/          # Pantallas principales (Muestras, Consultas, Cirugías, etc.)
│   └── splash.py       # Pantalla de carga animada
├── orm_models/         # Modelos de base de datos de SQLAlchemy
├── services/           # Lógica de negocio y servicios del sistema
├── templates/          # Plantillas de reportes PDF y documentos
├── utils/              # Utilidades de logging, validación y formato
├── alembic/            # Configuraciones y migraciones de base de datos
├── build_app.py        # Script para compilar la aplicación a ejecutable .exe
├── config.py           # Configuración global, constantes y sistema de temas
├── main.py             # Punto de entrada principal de la aplicación
└── requirements.txt    # Dependencias de Python
```

---

## 📥 Instalación y Configuración

### 1. Requisitos Previos
Asegúrate de contar con **Python 3.10** o superior instalado en tu sistema.

### 2. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/ISALAB.git
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

### 4. Instalar Dependencias
```bash
pip install -r requirements.txt
```

---

## ⚡ Ejecución

Para iniciar la aplicación en entorno de desarrollo:

```bash
python main.py
```

En la primera ejecución, el sistema detectará que no existen usuarios registrados y desplegará automáticamente un asistente de instalación para crear la cuenta de administrador.

---

## 📦 Compilación a Ejecutable (.exe en Windows)

El proyecto incluye un script de compilación automatizado con **PyInstaller** y un manifiesto de Windows para garantizar que el icono en la barra de tareas se muestre de forma independiente:

```bash
python build_app.py
```

El ejecutable compilado estará disponible en la carpeta:
`dist/IsaLab/IsaLab.exe`

---

## 🧪 Pruebas (Testing)

Para ejecutar la suite de pruebas unitarias e integración con Pytest:

```bash
pytest
```

---

## 📄 Licencia

Derechos Reservados © IsaLab - Centro Diagnóstico Veterinario - Diseñado por CORJAR Computers Solutions 2026. 
Uso interno y autorizado.
