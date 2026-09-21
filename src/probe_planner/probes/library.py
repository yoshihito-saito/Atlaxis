from pathlib import Path


def probe_library_path():
    """Use the editable checkout library, or the copy included in the wheel."""
    module = Path(__file__).resolve()
    checkout = module.parents[3] / "probes"
    return checkout if checkout.is_dir() else module.parents[1] / "data" / "probes"


def planning_path():
    """Keep checkout plans together; installed apps use a writable user folder."""
    checkout = Path(__file__).resolve().parents[3]
    folder = (checkout if (checkout / "pyproject.toml").is_file()
              else Path.home() / "Documents" / "Atlaxis") / "planning"
    folder.mkdir(parents=True, exist_ok=True)
    return folder
