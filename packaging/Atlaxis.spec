"""Native one-folder build; run PyInstaller on the target operating system."""

from pathlib import Path
import sys
import tomllib

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

root = Path(SPECPATH).parent
version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
datas = [
    (str(root / "probes"), "probe_planner/data/probes"),
    (str(root / "logo/Atlaxis.png"), "probe_planner/data"),
]
datas += collect_data_files("brainglobe_atlasapi")
datas += collect_data_files("pyvista")
datas += copy_metadata("brainglobe-atlasapi", recursive=True)
datas += copy_metadata("neurocarto", recursive=True)

a = Analysis(
    [str(root / "src/probe_planner/__main__.py")],
    pathex=[str(root / "src")],
    datas=datas,
    hiddenimports=collect_submodules("neurocarto.probe_npx") + collect_submodules("vtkmodules"),
    excludes=["PyQt5", "PyQt6", "PySide2"],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Atlaxis",
          icon=str(root / "logo/Atlaxis.ico") if sys.platform == "win32" else None,
          console=False, debug=False, strip=False, upx=False)
collection = COLLECT(exe, a.binaries, a.datas, name="Atlaxis", strip=False, upx=False)
if sys.platform == "darwin":
    app = BUNDLE(collection, name="Atlaxis.app", bundle_identifier="org.atlaxis.desktop",
                 icon=str(root / "logo/Atlaxis.icns"),
                 info_plist={"CFBundleShortVersionString": version,
                             "NSHighResolutionCapable": True})
