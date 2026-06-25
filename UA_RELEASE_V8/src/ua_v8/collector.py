"""
UA Test v8.0 — Git auto-collector (copy CSV/log/passports → results/, commit, push).
"""
import time
from pathlib import Path

from . import config


def collect_results_to_git(tier_label, csv_path, log_path, note=""):
    """Copy run outputs into UA_RELEASE_V8/results/ and commit (optionally push).

    Args:
        tier_label: e.g. "Screening", "Standard"
        csv_path:   Path to the CSV results file
        log_path:   Path to the log file
        note:       optional suffix for the commit message (e.g. "model/domain")
    """
    if not config.AUTO_COLLECT_RESULTS:
        return
    import subprocess
    import shutil

    here = Path(__file__).resolve()
    try:
        repo = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(here.parent), stderr=subprocess.DEVNULL,
        ).decode().strip())
    except Exception:
        print("  [autocollect] not a git repository — skipped")
        return

    # <repo>/UA_RELEASE_V8/results
    # here = ua_v8/collector.py → parent = ua_v8/ → parent.parent = src/
    # → parent.parent.parent = UA_RELEASE_V8/
    results_dir = here.parents[2] / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    for src in (Path(csv_path), Path(log_path)):
        if src.exists():
            dst = results_dir / src.name
            shutil.copy2(src, dst)
            copied.append(dst)

    if config.PASSPORT_DIR.exists() and any(
            config.PASSPORT_DIR.glob("*.json")):
        pass_dst = results_dir / "passports_v8"
        pass_dst.mkdir(exist_ok=True)
        for p in config.PASSPORT_DIR.glob("*.json"):
            d = pass_dst / p.name
            shutil.copy2(p, d)
            copied.append(d)

    if not copied:
        print("  [autocollect] nothing to collect")
        return

    print(f"  [autocollect] copied {len(copied)} file(s) -> {results_dir}")
    if not config.AUTO_COMMIT_RESULTS:
        return

    try:
        rels = [str(c.relative_to(repo)) for c in copied]
        subprocess.run(["git", "add"] + rels, cwd=str(repo), check=True)
        # commit only if something actually changed
        if subprocess.run(["git", "diff", "--cached", "--quiet"],
                          cwd=str(repo)).returncode == 0:
            print("  [autocollect] no changes to commit")
            return
        suffix = f" ({note})" if note else ""
        msg = (f"Results: UA Test v8 {tier_label} run"
               f"{suffix} — {time.strftime('%Y-%m-%d %H:%M')}")
        subprocess.run(
            ["git", "-c", "user.name=Denys Uvarov",
             "-c", "user.email=uvarov.denys@gmail.com",
             "commit", "-q", "-m", msg],
            cwd=str(repo), check=True,
        )
        print(f"  [autocollect] committed: {msg}")
        if config.AUTO_PUSH_RESULTS:
            r = subprocess.run(["git", "push", "origin", "HEAD"],
                               cwd=str(repo), capture_output=True, text=True)
            if r.returncode == 0:
                print("  [autocollect] pushed to origin ✓")
            else:
                print(f"  [autocollect] push FAILED (commit kept locally): "
                      f"{r.stderr.strip()[:200]}")
    except Exception as e:
        print(f"  [autocollect] git step failed: {e}")
