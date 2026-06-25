"""
UA Test v8.0 — Memory guard helpers (macOS unified-memory protection).
"""
import re

from . import config


def total_ram_gb():
    """Total physical RAM in GB."""
    try:
        import subprocess
        out = subprocess.check_output(["sysctl", "-n", "hw.memsize"])
        return int(out) / 1024 ** 3
    except Exception:
        try:
            import psutil
            return psutil.virtual_memory().total / 1024 ** 3
        except Exception:
            return 0.0


def free_ram_gb():
    """Best-effort available (not just free) RAM in GB."""
    try:
        import psutil
        return psutil.virtual_memory().available / 1024 ** 3
    except Exception:
        pass
    # Fallback: parse vm_stat (macOS)
    try:
        import subprocess
        out = subprocess.check_output(["vm_stat"]).decode()
        page = 4096
        for line in out.splitlines():
            if "page size of" in line:
                page = int(re.search(r"(\d+)", line).group(1))
        free = inactive = 0
        for line in out.splitlines():
            if line.startswith("Pages free:"):
                free = int(re.search(r"(\d+)", line).group(1))
            elif line.startswith("Pages inactive:"):
                inactive = int(re.search(r"(\d+)", line).group(1))
        return (free + inactive) * page / 1024 ** 3
    except Exception:
        return -1.0  # unknown


def model_disk_size_gb(model_id):
    """Best-effort on-disk size of a model's weights, matched by id fragments.

    Returns 0.0 if the directory cannot be located (guard then falls back to
    the live free-RAM watchdog only).
    """
    if not config.LMSTUDIO_MODELS_ROOT.is_dir():
        return 0.0
    frag = (model_id.split("/")[-1].lower()
            .replace("-", "").replace("_", "").replace(".", ""))
    best = 0.0
    for d in config.LMSTUDIO_MODELS_ROOT.rglob("*"):
        if not d.is_dir():
            continue
        name = d.name.lower().replace("-", "").replace("_", "").replace(".", "")
        if frag and frag in name:
            size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            best = max(best, size / 1024 ** 3)
    return best
