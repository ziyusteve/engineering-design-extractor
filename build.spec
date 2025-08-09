# PyInstaller spec for Engineering Design Criteria Extractor
# Usage (Windows): pyinstaller build.spec

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# In spec execution, __file__ may be undefined. Use CWD as project root.
project_root = os.path.abspath(os.getcwd())
src_dir = os.path.join(project_root, "src")

# Bundle Jinja2 templates
templates_dir = os.path.join(src_dir, "webapp", "templates")
datas = []
if os.path.isdir(templates_dir):
    # Place inside the bundle under the same package path
    datas.append((templates_dir, "src/webapp/templates"))

# Hidden imports for Google Cloud client libraries and friends
hiddenimports = []
hiddenimports += collect_submodules("google.cloud")
hiddenimports += collect_submodules("google.api_core")
hiddenimports += collect_submodules("google.oauth2")
hiddenimports += collect_submodules("google.auth")
hiddenimports += collect_submodules("grpc")

# Ensure Flask and its ecosystem are bundled
hiddenimports += collect_submodules("flask")
hiddenimports += collect_submodules("werkzeug")
hiddenimports += collect_submodules("jinja2")
hiddenimports += collect_submodules("markupsafe")
hiddenimports += collect_submodules("itsdangerous")
hiddenimports += collect_submodules("click")

# Some packages require data files at runtime (templates, metadata)
datas += collect_data_files("jinja2")
datas += collect_data_files("flask")

# dotenv is optional at runtime; include if available so .env can be loaded
try:
    hiddenimports += ["dotenv"]
except Exception:
    pass

a = Analysis(
    [os.path.join(src_dir, "webapp", "run.py")],
    pathex=[src_dir, project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="EngineeringDesignExtractor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
)
