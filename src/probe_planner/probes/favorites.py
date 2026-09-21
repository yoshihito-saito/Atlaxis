"""User-level favorite probe templates, independent of saved implant plans."""

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from PySide6.QtCore import QSettings

from .importers import geometry_from_dict, load_geometry_json
from .library import probe_library_path
from .model import ChannelMap
from .neuropixels import is_neuropixels
from .wiring import headstage_map


def _geometry_digest(geometry):
    data = asdict(geometry)
    # Provenance and wiring updates do not make a new physical probe design.
    data.pop("metadata")
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


class FavoriteProbes:
    def __init__(self, settings=None):
        self.settings = settings if settings is not None else QSettings("Atlaxis", "ProbePlanner")
        self.entries = json.loads(self.settings.value("favorite_probes", "[]", type=str))

    def _identity(self, geometry):
        digest = _geometry_digest(geometry)
        relative = str(Path(geometry.metadata.get("manufacturer", "")) / f"{geometry.name}.json")
        path = probe_library_path() / relative
        if path.is_file():
            library_geometry, _ = load_geometry_json(path)
            if _geometry_digest(library_geometry) == digest:
                return "library:" + relative, relative
        return "custom:" + digest, None

    def contains(self, geometry):
        key, _ = self._identity(geometry)
        return any(entry["key"] == key for entry in self.entries)

    def toggle(self, geometry, mapping):
        key, relative = self._identity(geometry)
        entries = [entry for entry in self.entries if entry["key"] != key]
        added = len(entries) == len(self.entries)
        if added:
            entry = {"key": key, "name": geometry.name, "library_file": relative,
                     "headstage_id": mapping.headstage_id}
            if relative is None:
                template_map = ChannelMap(n_channels=mapping.n_channels) if is_neuropixels(geometry) else mapping
                entry.update(geometry=asdict(geometry), channel_map=asdict(template_map))
            entries.append(entry)
        self.settings.setValue("favorite_probes", json.dumps(entries, ensure_ascii=False))
        self.settings.sync()
        if self.settings.status() != QSettings.NoError:
            raise OSError("Unable to save favorite probes.")
        self.entries = entries
        return added

    def load(self, key):
        entry = deepcopy(next(entry for entry in self.entries if entry["key"] == key))
        if entry["library_file"]:
            geometry, mapping = load_geometry_json(probe_library_path() / entry["library_file"])
            if entry.get("headstage_id"):
                mapping = headstage_map(geometry, entry["headstage_id"])
            return geometry, mapping
        geometry = geometry_from_dict(entry["geometry"])
        mapping = ChannelMap(**entry["channel_map"])
        mapping.validate(geometry)
        return geometry, mapping
