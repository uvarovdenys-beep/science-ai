"""
UA Test v8.0 — Configuration constants.
"""
import re
from pathlib import Path

# ─── LM STUDIO ENDPOINTS ──────────────────────────────────────────────────
LM_BASE = "http://localhost:1234"
CHAT_ENDPOINT = f"{LM_BASE}/v1/chat/completions"
MODELS_ENDPOINT = f"{LM_BASE}/v1/models"
LOAD_ENDPOINT = f"{LM_BASE}/api/v0/models/load"
UNLOAD_ENDPOINT = f"{LM_BASE}/api/v0/models/unload"

# olmo-3-32b-think is excluded here and run separately later (thinking model is
# far slower; keeping it out unblocks the rest of the batch).
SKIP_MODELS = {
    "text-embedding-nomic-embed-text-v1.5",
    "allenai/olmo-3-32b-think",
}

# ─── PATHS ─────────────────────────────────────────────────────────────────
# When run via the orchestrator (ua_v8_full.py), REPORT_DIR is set by main().
# Default: next to this package's parent (i.e. src/reports).
_SRC_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = _SRC_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)
PASSPORT_DIR = REPORT_DIR / "passports_v8"
PASSPORT_DIR.mkdir(exist_ok=True)

# ─── EVALUATION PARAMETERS ────────────────────────────────────────────────
# Reduced 11->6 grid for throughput (~2x faster). These 6 are a subset of the
# original 11, so prior 11-temp data (e.g. gemma) stays comparable at these points.
TEMPERATURES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
MAX_TOKENS = 4096
MODEL_WAIT_SEC = 240
REQUEST_TIMEOUT = 900

# ─── RETRY ─────────────────────────────────────────────────────────────────
# Transient LM Studio failures (HTTP 5xx / sporadic 400) caused permanent gaps
# in the first standard run (LEGAL_COMPLIANCE lost 17 rows). Retry with backoff.
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_SEC = 2.0

# ─── MEMORY GUARD ──────────────────────────────────────────────────────────
# On unified-memory Macs, loading a model larger than free RAM triggers swap
# thrash that can lock up the whole system.
LMSTUDIO_MODELS_ROOT = Path.home() / ".lmstudio" / "models"
OS_RESERVE_GB = 8.0
MIN_FREE_RAM_GB_TO_START = 6.0
HARD_FLOOR_RAM_GB = 2.5
MODEL_SIZE_SAFETY = 1.25
ENABLE_MEMORY_GUARD = True

# ─── TIERS ─────────────────────────────────────────────────────────────────
TIERS = {
    "screening":     {"mc_runs": 3,  "label": "Screening"},
    "standard":      {"mc_runs": 10, "label": "Standard"},
    "certification": {"mc_runs": 30, "label": "Certification"},
}

# ─── RESULT AUTO-COLLECT ───────────────────────────────────────────────────
AUTO_COLLECT_RESULTS = True
AUTO_COMMIT_RESULTS = True
AUTO_PUSH_RESULTS = True

# ─── CSV HEADER ────────────────────────────────────────────────────────────
CSV_HEADER = [
    "model", "domain", "scenario_id", "type", "temp", "mc_run",
    "ordering", "result", "raw_label", "secondpass", "response_length",
    "latency_s",
]
