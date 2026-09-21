"""Collect notices from the interpreter and dependency wheels used for a build.

Run with the same Python environment as PyInstaller. This inventories available
notices; it does not certify the licenses or source availability of native code.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path, PurePosixPath
import platform
import re
import sys
import sysconfig
import tomllib
from urllib.parse import quote

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


ROOT = Path(__file__).resolve().parents[1]
NOTICE_NAME = re.compile(r"^(licen[sc]e|copying|copyright|notice|authors)([._-]|$)", re.I)
QT_PACKAGES = {"pyside6", "pyside6-addons", "pyside6-essentials", "shiboken6"}


def dependency_distributions(include_build_tool: bool) -> list:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    pending = [Requirement(value) for value in project["dependencies"]]
    if include_build_tool:
        pending.append(Requirement("pyinstaller==6.22.3"))
    distributions = {}
    visited = set()
    while pending:
        requirement = pending.pop()
        name = canonicalize_name(requirement.name)
        key = (name, tuple(sorted(requirement.extras)))
        if key in visited:
            continue
        visited.add(key)
        dist = metadata.distribution(name)
        if requirement.specifier and not requirement.specifier.contains(dist.version):
            raise RuntimeError(f"{name} {dist.version} does not satisfy {requirement}")
        distributions[name] = dist
        for value in dist.requires or []:
            child = Requirement(value)
            if child.marker is None or any(
                child.marker.evaluate({"extra": extra})
                for extra in ("", *requirement.extras)
            ):
                pending.append(child)
    return [distributions[name] for name in sorted(distributions)]


def copy_notice(source: Path, target: Path, output: Path) -> dict:
    data = source.read_bytes()
    if not data:
        raise RuntimeError(f"Empty notice: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    if target.read_bytes() != data:
        raise RuntimeError(f"Notice copy differs: {target}")
    return {"path": target.relative_to(output).as_posix(),
            "sha256": hashlib.sha256(data).hexdigest()}


def license_label(dist) -> str:
    expression = dist.metadata.get("License-Expression")
    if expression:
        return expression
    value = dist.metadata.get("License", "")
    if value and "\n" not in value and len(value) < 120:
        return value
    classifiers = [value.rsplit(" :: ", 1)[-1]
                   for value in dist.metadata.get_all("Classifier", [])
                   if value.startswith("License ::")]
    return "; ".join(classifiers) or "See original license texts"


def collect(output: Path, *, include_build_tool: bool = False) -> dict:
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"Use an empty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    locked = {canonicalize_name(p["name"]): p
              for p in tomllib.loads((ROOT / "uv.lock").read_text())["package"]}
    upstream_path = ROOT / "third_party/licenses/upstream/manifest.json"
    upstream = json.loads(upstream_path.read_text())
    for entry in upstream["files"]:
        data = (upstream_path.parent / entry["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise RuntimeError(f"Upstream notice has changed: {entry['path']}")

    packages = []
    for dist in dependency_distributions(include_build_tool):
        name = canonicalize_name(dist.metadata["Name"])
        lock = locked.get(name)
        if lock and lock["version"] != dist.version:
            raise RuntimeError(f"{name} {dist.version} differs from uv.lock")
        files = []
        for item in sorted(dist.files or [], key=str):
            path = PurePosixPath(str(item).replace("\\", "/"))
            if not (NOTICE_NAME.match(path.name) or
                    any(part.lower() in {"licenses", "licences"} for part in path.parts)):
                continue
            if path.suffix.lower() in {".py", ".pyc", ".so", ".pyd", ".dll"}:
                continue
            if path.is_absolute() or ".." in path.parts:
                raise RuntimeError(f"Unexpected notice path in {name}: {path}")
            source = Path(dist.locate_file(item))
            files.append(copy_notice(source, output / "packages" /
                                     f"{name}-{dist.version}" / path, output))
        supplemental = []
        if name in QT_PACKAGES:
            if dist.version != upstream["versions"]["qt"]:
                raise RuntimeError("Refresh the Qt/PySide upstream notices for " + dist.version)
            supplemental = ["../upstream/qtbase/", "../upstream/pyside-setup/"]
        if name in {"vtk", "pyinstaller"}:
            if dist.version != upstream["versions"][name]:
                raise RuntimeError(f"Refresh the {name} upstream notices for {dist.version}")
            supplemental.append(f"../upstream/{name}/")
        if not files and not supplemental:
            raise RuntimeError(f"No license text found for {name} {dist.version}")
        packages.append({
            "name": dist.metadata["Name"], "version": dist.version,
            "license_metadata": license_label(dist),
            "project_urls": dist.metadata.get_all("Project-URL", []),
            "homepage": dist.metadata.get("Home-page", ""),
            "source_distribution": (lock or {}).get("sdist"),
            "notices": files, "supplemental_notices": supplemental,
        })

    python_candidates = [Path(sysconfig.get_path("stdlib")) / "LICENSE.txt",
                         Path(sys.base_prefix) / "LICENSE.txt",
                         Path(sys.base_prefix) / "LICENSE"]
    python_license = next((p for p in python_candidates if p.is_file()), None)
    if python_license is None:
        raise RuntimeError("Cannot find the license shipped with this Python interpreter")
    python_notice = copy_notice(python_license, output / "python/LICENSE.txt", output)
    manifest = {
        "generator": "packaging/collect_licenses.py",
        "scope": "Installed runtime dependency closure and optional build-tool dependencies; "
                 "a superset of frozen imports, not a native binary compliance audit.",
        "python": {"version": platform.python_version(),
                   "implementation": platform.python_implementation(),
                   "notice": python_notice,
                   "source_url": "https://www.python.org/ftp/python/" +
                                 platform.python_version() + "/Python-" +
                                 platform.python_version() + ".tar.xz"},
        "platform": sys.platform, "architecture": platform.machine(),
        "includes_build_tool": include_build_tool, "packages": packages,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    lines = ["# Dependency notices", "",
             "Generated by `packaging/collect_licenses.py` from the build environment.",
             f"Platform: {sys.platform} / {platform.machine()}; "
             f"Python {platform.python_version()}.", "",
             "This is the installed dependency closure, including packages that may not",
             "be imported into the frozen app. Original files retain all upstream notices.",
             "It is not a complete inventory of native libraries. See",
             "[release requirements](../../../docs/licensing.md).", "",
             "[Python license](python/LICENSE.txt). Exact package versions, source archive",
             "URLs, upstream hashes and copied-notice hashes are in [manifest.json](manifest.json).", "",
             "| Package | Version | License metadata | Original notices |",
             "| --- | --- | --- | --- |"]
    for p in packages:
        notices = [f"[{PurePosixPath(n['path']).name}]({quote(n['path'], safe='/')})"
                   for n in p["notices"]]
        notices += [f"[Upstream notices]({n})" for n in p["supplemental_notices"]]
        label = p["license_metadata"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {p['name']} | {p['version']} | {label} | {'; '.join(notices)} |")
    (output / "INDEX.md").write_text("\n".join(lines) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="An empty directory for the collected notice bundle")
    parser.add_argument("--include-build-tool", action="store_true")
    args = parser.parse_args()
    result = collect(args.output, include_build_tool=args.include_build_tool)
    print(f"Collected {len(result['packages'])} distributions and Python notices in {args.output}")
