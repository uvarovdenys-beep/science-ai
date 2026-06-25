"""
UA Test v8.0 — Model management (load/unload/switch via LM Studio API).
"""
import json
import sys
import time
import urllib.request

from . import config
from .http_client import http_get, http_post
from .memory_guard import total_ram_gb, free_ram_gb, model_disk_size_gb


def get_all_models():
    """Return list of all model IDs available in LM Studio (minus skipped)."""
    data = http_get(config.MODELS_ENDPOINT)
    return [m["id"] for m in data["data"] if m["id"] not in config.SKIP_MODELS]


def get_loaded_models():
    """Return list of currently loaded model IDs."""
    try:
        data = http_get(f"{config.LM_BASE}/api/v0/models")
        return [m["id"] for m in data.get("data", [])
                if m.get("state") == "loaded"]
    except Exception:
        return []


def switch_model(model_id):
    """Unload others, load target model with memory guard. Returns True/False."""
    print(f"\n{'='*60}")
    print(f"[MODEL SWITCH] -> {model_id}")
    print(f"  Time: {time.strftime('%H:%M:%S')}")
    sys.stdout.flush()

    loaded = get_loaded_models()
    print(f"  Currently loaded: {loaded}")
    for mid in loaded:
        if mid != model_id:
            try:
                http_post(config.UNLOAD_ENDPOINT, {"identifier": mid}, timeout=60)
                print(f"  Unloaded: {mid}")
            except Exception as e:
                print(f"  Unload error for {mid}: {e}")
    time.sleep(2)

    # ── Memory guard: wait for freed RAM to be reclaimed, then gate ──────
    # Skip the guard if the target is already resident.
    if config.ENABLE_MEMORY_GUARD and model_id not in loaded:
        total = total_ram_gb()
        for _ in range(15):  # up to ~30s for the OS to reclaim unloaded pages
            if free_ram_gb() >= config.MIN_FREE_RAM_GB_TO_START:
                break
            time.sleep(2)
        free = free_ram_gb()
        disk = model_disk_size_gb(model_id)
        need = disk * config.MODEL_SIZE_SAFETY
        print(f"  [mem] total={total:.1f}GB free={free:.1f}GB "
              f"model_on_disk={disk:.1f}GB need~{need:.1f}GB resident")
        # Refuse a model that cannot fit.
        if need > 0 and need > (total - config.OS_RESERVE_GB):
            print(f"  SKIP (memory guard): needs ~{need:.1f}GB but only "
                  f"{total - config.OS_RESERVE_GB:.1f}GB usable on a "
                  f"{total:.0f}GB host")
            return False
        if free >= 0 and free < config.MIN_FREE_RAM_GB_TO_START:
            print(f"  SKIP (memory guard): only {free:.1f}GB free "
                  f"(need >= {config.MIN_FREE_RAM_GB_TO_START:.1f}GB to start "
                  f"safely)")
            return False

    try:
        http_post(config.LOAD_ENDPOINT, {"identifier": model_id}, timeout=60)
        print(f"  Load request sent for {model_id}")
    except Exception as e:
        print(f"  Load request result: {e}")
    time.sleep(5)

    print(f"  Waiting for model to be ready (max {config.MODEL_WAIT_SEC}s)...")
    sys.stdout.flush()
    deadline = time.time() + config.MODEL_WAIT_SEC
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        remaining = int(deadline - time.time())
        # Watchdog: abort load if it exhausts host memory.
        if config.ENABLE_MEMORY_GUARD and model_id not in loaded:
            fr = free_ram_gb()
            if 0 <= fr < config.HARD_FLOOR_RAM_GB:
                print(f"  ABORT (memory guard): free RAM {fr:.1f}GB < "
                      f"{config.HARD_FLOOR_RAM_GB}GB floor during load — "
                      f"unloading to protect host")
                try:
                    http_post(config.UNLOAD_ENDPOINT,
                              {"identifier": model_id}, timeout=60)
                except Exception:
                    pass
                return False
        try:
            req = urllib.request.Request(
                config.CHAT_ENDPOINT,
                data=json.dumps({
                    "model": model_id,
                    "messages": [{"role": "user", "content": "READY"}],
                    "max_tokens": 3,
                    "temperature": 0.1,
                }).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                json.loads(r.read().decode())
            print(f"  Model READY after {attempt} attempt(s) — "
                  f"{time.strftime('%H:%M:%S')}")
            sys.stdout.flush()
            return True
        except Exception as e:
            if attempt <= 3 or attempt % 5 == 0:
                print(f"  [{time.strftime('%H:%M:%S')}] attempt #{attempt}, "
                      f"{remaining}s left — {type(e).__name__}")
            sys.stdout.flush()
            time.sleep(5)
    print(f"  TIMEOUT — model did not respond within {config.MODEL_WAIT_SEC}s")
    return False
