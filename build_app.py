import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Single source of truth para la versión: ``config.__version__``.
# El manifiesto Windows usa formato de 4 partes (X.Y.Z.W), así que le
# añadimos un ``.0`` final al valor de ``__version__`` (que es PEP 440).
from config import __version__

# Versión Windows (4 partes): ``1.0.0`` -> ``1.0.0.0``
_WIN_VERSION = f"{__version__}.0" if __version__.count('.') < 3 else __version__

# El placeholder ``__VERSION__`` se reemplaza al escribir el manifiesto.
# NO usar ``{version}`` con ``.format()`` porque el XML contiene llaves en
# los GUIDs de ``supportedOS Id="{...}"``.
MANIFEST_CONTENT = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">

  <!-- Identidad de la aplicación: necesaria para que Windows la reconozca
       como app independiente y muestre el icono correcto en la barra de tareas.
       La versión se sincroniza con ``config.__version__`` (issue D-L2). -->
  <assemblyIdentity
      version="__VERSION__"
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


def build_manifest(manifest_file: Path) -> None:
    """Escribe ``isalab.manifest`` con la versión actual de ``config.__version__``.

    Reemplaza el placeholder ``__VERSION__`` por la versión de 4 partes
    que Windows espera (``X.Y.Z.W``).
    """
    content = MANIFEST_CONTENT.replace("__VERSION__", _WIN_VERSION)
    manifest_file.write_text(content, encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compila IsaLab a un ejecutable standalone con PyInstaller.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help=(
            "Build de diagnóstico: habilita la consola (``--console``) y usa "
            "``optimize=0`` en vez de ``optimize=2`` para preservar docstrings "
            "y asserts. Internamente setea ``ISALAB_DEBUG=1`` en el subprocess "
            "de PyInstaller, que ``IsaLab.spec`` lee para ambos ajustes."
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    debug = bool(args.debug)

    root_dir = Path(__file__).resolve().parent
    build_dir = root_dir / "build"
    dist_dir = root_dir / "dist"
    spec_file = root_dir / "IsaLab.spec"
    manifest_file = root_dir / "isalab.manifest"

    if debug:
        print_step("⚠️  MODO DEBUG activado: console=True, optimize=0 (no stripping)")
    else:
        print_step("Modo producción: console=False, optimize=2 (stripping docstrings/asserts)")

    # 0. Generar el manifiesto XML (siempre, para tenerlo actualizado)
    print_step("Generando manifiesto Windows (isalab.manifest)...")
    build_manifest(manifest_file)
    print(f"Manifiesto escrito en: {manifest_file} (version={_WIN_VERSION})")

    # 1. Limpiar construcciones anteriores
    print_step("Limpiando carpetas 'build' y 'dist' anteriores...")
    for d in [build_dir, dist_dir]:
        if d.exists():
            print(f"Eliminando {d.name}...")
            shutil.rmtree(d, ignore_errors=True)

    # 2. Instalar dependencias de compilación si faltan
    print_step("Verificando dependencias de compilación (PyInstaller)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 3. Compilar usando PyInstaller
    print_step("Compilando el proyecto (Modo Directorio)...")

    # Entorno para el subprocess: en modo debug, exportar ISALAB_DEBUG=1
    # para que ``IsaLab.spec`` lo lea y aplique console=True + optimize=0
    # (ver ``IsaLab.spec`` líneas ~120-140).
    child_env = os.environ.copy()
    if debug:
        child_env["ISALAB_DEBUG"] = "1"

    # Verificamos si existe el .spec original, si existe lo usamos
    if spec_file.exists():
        print("Usando configuración IsaLab.spec existente.")
        cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm"]
        # --console en CLI es defensivo: el .spec también lee ISALAB_DEBUG
        # para fijar ``console=`` (ver ``IsaLab.spec``), pero pasamos el flag
        # para que el log de PyInstaller lo refleje explícitamente.
        if debug:
            cmd.append("--console")
        cmd.append("IsaLab.spec")
    else:
        # Si no existe, construimos los argumentos directos
        print("Creando nueva compilación desde main.py...")
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm",
            "--onedir",           # Modo directorio (NO un solo archivo)
            "--windowed" if not debug else "--console",
            "--name", "IsaLab",
            "--icon", "assets/icono.ico",
            # ── Manifiesto: da identidad a la app en Windows ──
            "--manifest", str(manifest_file),
            "--add-data", f"assets{os.pathsep}assets",
            "--add-data", f"templates{os.pathsep}templates",
            "main.py"
        ]

    try:
        subprocess.check_call(cmd, env=child_env)
        print_step("✅ Compilación terminada exitosamente!")
        print(f"📁 Puedes encontrar tu aplicación compilada en:\n{dist_dir / 'IsaLab'}")
        print("\nPara probarla, simplemente ejecuta IsaLab.exe dentro de esa carpeta.")
        if debug:
            print("\n⚠️  Recuerda: este build incluye consola y NO está optimizado.")
            print("    NO distribuirlo a usuarios finales. Usa `python build_app.py`")
            print("    (sin --debug) para builds de producción.")
    except subprocess.CalledProcessError as e:
        print_step("❌ Error durante la compilación.")
        print(f"Código de error: {e.returncode}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
