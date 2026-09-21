"""Persistent user data, separate from the application and its bundled probes."""

from configparser import ConfigParser
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile


@dataclass(frozen=True)
class DataPaths:
    root: Path

    @property
    def atlases(self):
        return self.root / "atlases"

    @property
    def probes(self):
        return self.root / "probes"

    @property
    def standard_probes(self):
        return self.probes / "standard"

    @property
    def planning(self):
        return self.root / "planning"

    @property
    def config(self):
        return self.root / ".atlaxis"


_active_paths = None


def active_paths():
    return _active_paths


def bundled_probe_path():
    module = Path(__file__).resolve()
    packaged = module.parent / "data" / "probes"
    return packaged if packaged.is_dir() else module.parents[2] / "probes"


def storage_settings():
    from PySide6.QtCore import QSettings
    return QSettings("Atlaxis", "ProbePlanner")


def saved_paths():
    settings = storage_settings()
    value = settings.value("storage/paths", "", type=str)
    if not value:
        return None
    data = json.loads(value)
    return DataPaths(Path(data["root"]))


def default_paths():
    from PySide6.QtCore import QStandardPaths
    documents = Path(QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation))
    return DataPaths(documents / "Atlaxis")


def _write_bytes(path, data):
    descriptor, filename = tempfile.mkstemp(prefix=".atlaxis-", dir=path.parent)
    temporary = Path(filename)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def prepare_storage(paths):
    """Initialize folders/update unedited templates; do not activate or save settings."""
    source = bundled_probe_path().resolve()
    destination = paths.standard_probes.resolve()
    if not source.is_dir():
        raise FileNotFoundError("The application is missing its bundled probe library.")
    if destination.is_relative_to(source) or source.is_relative_to(destination):
        raise ValueError("Choose a data folder outside the bundled probe library.")
    for folder in (paths.standard_probes, paths.probes / "custom", paths.atlases,
                   paths.planning, paths.config / "brainglobe"):
        folder.mkdir(parents=True, exist_ok=True)
    manifest_path = paths.config / "standard-probes.json"
    previous = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    installed = dict(previous)
    preserved = []
    for source_file in sorted(source.rglob("*")):
        if not source_file.is_file():
            continue
        relative = source_file.relative_to(source)
        key = relative.as_posix()
        target = destination / relative
        data = source_file.read_bytes()
        incoming = hashlib.sha256(data).hexdigest()
        if target.exists():
            current = hashlib.sha256(target.read_bytes()).hexdigest()
            if current == incoming:
                installed[key] = incoming
                continue
            if current != previous.get(key):
                preserved.append(key)
                continue
        target.parent.mkdir(parents=True, exist_ok=True)
        _write_bytes(target, data)
        installed[key] = incoming
    _write_bytes(manifest_path, (json.dumps(installed, indent=2) + "\n").encode("utf-8"))
    return preserved


def save_paths(paths):
    from PySide6.QtCore import QSettings
    settings = storage_settings()
    settings.setValue("storage/paths", json.dumps({"root": str(paths.root)}))
    settings.sync()
    if settings.status() != QSettings.NoError:
        raise OSError("Unable to save data folder settings.")


def activate_storage(paths):
    """Call before importing MainWindow/BrainGlobe; later changes require restart."""
    global _active_paths
    from io import StringIO

    configuration = ConfigParser()
    configuration["default_dirs"] = {
        "brainglobe_dir": str(paths.atlases),
        "interm_download_dir": str(paths.atlases),
    }
    stream = StringIO()
    configuration.write(stream)
    _write_bytes(paths.config / "brainglobe" / "bg_config.conf", stream.getvalue().encode("utf-8"))
    os.environ["BRAINGLOBE_CONFIG_DIR"] = str(paths.config / "brainglobe")
    _active_paths = paths
