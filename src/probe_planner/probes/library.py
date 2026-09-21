from pathlib import Path

from probe_planner.storage import active_paths, bundled_probe_path


def probe_library_path():
    """GUI uses persistent standards; library-generation CLI uses its source copy."""
    paths = active_paths()
    return paths.standard_probes if paths is not None else bundled_probe_path()


def probe_import_path():
    """Let the GUI browse both standard and custom probes from one folder."""
    paths = active_paths()
    return paths.probes if paths is not None else probe_library_path()


def planning_path():
    """GUI plans use the selected data folder; non-GUI callers keep prior defaults."""
    paths = active_paths()
    if paths is not None:
        return paths.planning
    checkout = Path(__file__).resolve().parents[3]
    folder = (checkout if (checkout / "pyproject.toml").is_file()
              else Path.home() / "Documents" / "Atlaxis") / "planning"
    folder.mkdir(parents=True, exist_ok=True)
    return folder
