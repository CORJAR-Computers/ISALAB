# 🏭 Production Ready — IsaLab

## Visión General

IsaLab está listo para producción después de completar las 6 fases de corrección de errores. Este documento explica cómo ejecutar los scripts de limpieza, verificación y commit en el orden correcto.

---

## 📋 Prerrequisitos

Antes de ejecutar cualquier script, asegúrate de tener:

- **Python 3.10+** instalado
- **pip** actualizado
- **Git** configurado con acceso al repositorio
- **PowerShell** (Windows) o terminal compatible

### Instalar dependencias de desarrollo:

```powershell
cd D:\ISALAB
pip install -r requirements-dev.txt
```

---

## 🔄 Flujo de Ejecución Recomendado

### Orden CORRECTO de ejecución:

```
┌─────────────────────────────────────────────────────────────┐
│  Paso 1: LIMPIEZA                                           │
│  └── cleanup_production.ps1                                 │
│      Elimina archivos muertos y temporales                  │
├─────────────────────────────────────────────────────────────┤
│  Paso 2: VERIFICACIÓN                                       │
│  └── run_tests.ps1                                          │
│      Ejecuta suite completa de tests (~67+ tests)           │
├─────────────────────────────────────────────────────────────┤
│  Paso 3: COMMIT                                             │
│  └── commit_production_readiness.ps1                        │
│      Crea commit con todos los cambios                      │
├─────────────────────────────────────────────────────────────┤
│  Paso 4: PUSH (opcional)                                    │
│  └── git push origin feat/phase5-high-issues                │
│      Sube cambios al repositorio remoto                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📜 Descripción de Scripts

### 1. `cleanup_production.ps1` — Limpieza

**Propósito:** Elimina archivos muertos, scripts temporales y patches residuales.

**Archivos eliminados:**
- `gui_pyside/utils/window_manager.py` (dead code)
- `gui_pyside/views/boton_generar_reportes.py` (dead code)
- `fix_f541.py`, `fix_jinja_format.py`, `fix_jinja_format_2.py`, `fix_jinja_format_3.py` (temp scripts)
- `_cleanup_isalab_fase.py`, `_run_tests.py` (temp scripts)
- `0001-chore-ISALAB-Fase-1-*.patch`, `0001-slim-*.patch` (residual patches)
- `.coverage*` (coverage files)

**Uso:**
```powershell
cd D:\ISALAB
.\cleanup_production.ps1
```

**Salida esperada:**
```
========================================
  IsaLab - Limpieza Production Ready   
========================================

1. Eliminando archivos muertos (CRITICO)...
   [OK] gui_pyside\utils\window_manager.py eliminado
   [OK] gui_pyside\views\boton_generar_reportes.py eliminado

2. Eliminando scripts temporales...
   [OK] fix_f541.py eliminado
   ...

[LIMPIEZA COMPLETADA EXITOSAMENTE]
```

---

### 2. `run_tests.ps1` — Verificación

**Propósito:** Ejecuta la suite completa de tests para verificar que todo funciona.

**Uso:**
```powershell
cd D:\ISALAB
.\run_tests.ps1
```

**Opciones:**
```powershell
# Con reporte de cobertura
.\run_tests.ps1 -WithCoverage

# Saltar verificación de dependencias
.\run_tests.ps1 -SkipDependencyCheck
```

**Salida esperada:**
```
========================================
  IsaLab - Suite de Tests Completa    
========================================

3. Ejecutando suite de tests...
...
======================================== 67 passed in 45.32s ========================================

[TODOS LOS TESTS PASARON]
```

---

### 3. `commit_production_readiness.ps1` — Commit

**Propósito:** Crea un commit con todos los cambios de production readiness.

**Uso:**
```powershell
cd D:\ISALAB
.\commit_production_readiness.ps1
```

**Opciones:**
```powershell
# Con mensaje personalizado
.\commit_production_readiness.ps1 -CommitMessage "Tu mensaje aquí"
```

**Salida esperada:**
```
========================================
  COMMIT CREADO EXITOSAMENTE
========================================

Ultimo commit:
a1b2c3d chore: Production readiness cleanup

Archivos en el commit:
.gitignore
cleanup_production.ps1
run_tests.ps1
commit_production_readiness.ps1
```

---

### 4. `verify_and_test.ps1` — Verificación Combinada

**Propósito:** Combina limpieza y verificación en un solo paso (alternativa a los pasos 1 y 2).

**Uso:**
```powershell
cd D:\ISALAB
.\verify_and_test.ps1
```

**Opciones:**
```powershell
# Solo eliminar archivos (sin ejecutar tests)
.\verify_and_test.ps1 -SkipTests
```

---

## 🚀 Comandos Rápidos

### Flujo completo en una línea:

```powershell
cd D:\ISALAB; .\cleanup_production.ps1; .\run_tests.ps1; .\commit_production_readiness.ps1
```

### Solo verificación rápida:

```powershell
cd D:\ISALAB; .\verify_and_test.ps1
```

### Ejecutar tests manualmente:

```powershell
cd D:\ISALAB
python -m pytest tests/ -v --tb=short
```

---

## ⚠️ Solución de Problemas

### Error: "window_manager.py AÚN EXISTE"

**Causa:** La limpieza no se ejecutó o falló.

**Solución:**
```powershell
# Eliminar manualmente
Remove-Item -Path "gui_pyside\utils\window_manager.py" -Force
Remove-Item -Path "gui_pyside\views\boton_generar_reportes.py" -Force

# Verificar
Test-Path "gui_pyside\utils\window_manager.py"  # Debe retornar False
```

### Error: Tests fallan

**Causa:** Archivos muertos no eliminados o dependencias faltantes.

**Solución:**
```powershell
# 1. Ejecutar limpieza
.\cleanup_production.ps1

# 2. Instalar dependencias
pip install -r requirements-dev.txt

# 3. Ejecutar tests
.\run_tests.ps1
```

### Error: No se puede crear commit

**Causa:** No hay cambios pendientes o el repo está sucio.

**Solución:**
```powershell
# Verificar estado
git status

# Si hay cambios sin commit
git add -A
git commit -m "chore: Production readiness cleanup"

# Si no hay cambios
Write-Host "No hay cambios pendientes para commitear"
```

### Error: git push falla (autenticación)

**Causa:** Credenciales no configuradas.

**Solución:**
```powershell
# Configurar credenciales (una sola vez)
git config --global credential.helper store

# O usar token de GitHub
git remote set-url origin https://<TOKEN>@github.com/CORJAR-Computers/ISALAB.git
```

---

## 📊 Resumen de Cambios

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `.gitignore` | Modificado | `.coverage` → `.coverage*` |
| `cleanup_production.ps1` | Nuevo | Script de limpieza |
| `run_tests.ps1` | Nuevo | Script de tests |
| `verify_and_test.ps1` | Nuevo | Script combinado |
| `commit_production_readiness.ps1` | Nuevo | Script de commit |
| `PRODUCTION_READINESS.md` | Nuevo | Esta documentación |

---

## ✅ Checklist de Production Readiness

- [ ] `.gitignore` actualizado
- [ ] `cleanup_production.ps1` creado
- [ ] `run_tests.ps1` creado
- [ ] `verify_and_test.ps1` creado
- [ ] `commit_production_readiness.ps1` creado
- [ ] `PRODUCTION_READINESS.md` creado
- [ ] Archivos muertos eliminados
- [ ] Tests ejecutados y pasando
- [ ] Commit creado
- [ ] Push a repositorio remoto

---

## 📚 Recursos Adicionales

- **CHANGELOG.md** — Historial de cambios y fixes
- **README.md** — Información general del proyecto
- **ARCHITECTURE.md** — Arquitectura del sistema
- **SECURITY.md** — Políticas de seguridad

---

## 🤝 Soporte

Si tienes problemas con los scripts, revisa:

1. **Solución de Problemas** (arriba)
2. **CHANGELOG.md** para ver fixes recientes
3. **GitHub Issues** para reportar bugs

---

**Última actualización:** 21 de Julio, 2026  
**Versión:** 1.0.0  
**Estado:** Production Ready ✅
