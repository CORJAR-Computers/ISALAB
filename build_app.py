import os
import shutil
import subprocess
from pathlib import Path

MANIFEST_CONTENT = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">

  <!-- Identidad de la aplicación: necesaria para que Windows la reconozca
       como app independiente y muestre el icono correcto en la barra de tareas. -->
  <assemblyIdentity
      version="1.0.0.0"
      processorArchitecture="amd64"
      name="IsaLab.CentroDiagnosticoVeterinario"
      type="win32"
  />

  <description>IsaLab - Centro Diagnóstico Veterinario</description>

  <!-- Compatibilidad con versiones de Windows -->
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <!-- Windows 10 / 11 -->
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
      <!-- Windows 8.1 -->
      <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/>
      <!-- Windows 8 -->
      <supportedOS Id="{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}"/>
      <!-- Windows 7 -->
      <supportedOS Id="{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"/>
    </application>
  </compatibility>

  <!-- Conciencia de DPI: evita que Windows escale la app y distorsione el icono -->
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">
        true/PM
      </dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">
        PerMonitorV2
      </dpiAwareness>
    </windowsSettings>
  </application>

  <!-- Nivel de ejecución: no requiere elevación -->
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v2">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>

</assembly>
"""

def print_step(msg):
    print(f"\n{'='*50}")
    print(f"🚀 {msg}")
    print(f"{'='*50}")

def main():
    root_dir = Path(__file__).resolve().parent
    build_dir = root_dir / "build"
    dist_dir = root_dir / "dist"
    spec_file = root_dir / "IsaLab.spec"
    manifest_file = root_dir / "isalab.manifest"

    # 0. Generar el manifiesto XML (siempre, para tenerlo actualizado)
    print_step("Generando manifiesto Windows (isalab.manifest)...")
    manifest_file.write_text(MANIFEST_CONTENT, encoding="utf-8")
    print(f"Manifiesto escrito en: {manifest_file}")

    # 1. Limpiar construcciones anteriores
    print_step("Limpiando carpetas 'build' y 'dist' anteriores...")
    for d in [build_dir, dist_dir]:
        if d.exists():
            print(f"Eliminando {d.name}...")
            shutil.rmtree(d, ignore_errors=True)

    # 2. Instalar dependencias de compilación si faltan
    print_step("Verificando dependencias de compilación (PyInstaller)...")
    subprocess.check_call(["pip", "install", "pyinstaller"])

    # 3. Compilar usando PyInstaller
    print_step("Compilando el proyecto (Modo Directorio)...")

    # Verificamos si existe el .spec original, si existe lo usamos
    if spec_file.exists():
        print("Usando configuración IsaLab.spec existente.")
        cmd = ["pyinstaller", "--noconfirm", "IsaLab.spec"]
    else:
        # Si no existe, construimos los argumentos directos
        print("Creando nueva compilación desde main.py...")
        cmd = [
            "pyinstaller",
            "--noconfirm",
            "--onedir",           # Modo directorio (NO un solo archivo)
            "--windowed",         # Sin consola de comandos (fondo)
            "--name", "IsaLab",
            "--icon", "assets/icono.ico",
            # ── Manifiesto: da identidad a la app en Windows ──────────
            # Esto hace que la barra de tareas muestre el icono correcto
            # en lugar del icono genérico de python.exe
            "--manifest", str(manifest_file),
            "--add-data", f"assets{os.pathsep}assets",
            "--add-data", f"templates{os.pathsep}templates",
            "main.py"
        ]

    try:
        subprocess.check_call(cmd)
        print_step("✅ Compilación terminada exitosamente!")
        print(f"📁 Puedes encontrar tu aplicación compilada en:\n{dist_dir / 'IsaLab'}")
        print("\nPara probarla, simplemente ejecuta IsaLab.exe dentro de esa carpeta.")
    except subprocess.CalledProcessError as e:
        print_step("❌ Error durante la compilación.")
        print(f"Código de error: {e.returncode}")

if __name__ == "__main__":
    main()
