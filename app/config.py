import os
import hashlib
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent

# Data paths
DATA_DIR = BASE_DIR / "data"
RULES_PATH = DATA_DIR / "rules.json"
TAXONOMY_PATH = DATA_DIR / "taxonomy.json"
PROTOTYPES_PATH = DATA_DIR / "multilingual_prototypes.json"
DB_PATH = BASE_DIR / "copilot_tickets.db"

# Index cache directory
CACHE_DIR = BASE_DIR / "index_cache"
RULES_INDEX_PATH = CACHE_DIR / "rules_index.joblib"
TAXONOMY_INDEX_PATH = CACHE_DIR / "taxonomy_index.joblib"
METADATA_CACHE_PATH = CACHE_DIR / "index_metadata.json"

# TF-IDF Configuration
TFIDF_CONFIG = {
    "version": "2.1.0",
    "word_ngram_range": (1, 2),
    "char_ngram_range": (3, 5),
    "word_weight": 0.60,
    "char_weight": 0.40,
    "sublinear_tf": True,
    "norm": "l2"
}

# Thresholds
SEMANTIC_CITATION_THRESHOLD = 0.035  # Rule must meet this semantic relevance threshold to be cited
CONFIDENCE_THRESHOLD = 0.28
TOP2_MARGIN_THRESHOLD = 0.05
DUPLICATE_TIME_WINDOW_SECONDS = 3600
DUPLICATE_SIMILARITY_THRESHOLD = 0.85

# Official category codes that strictly require human intervention
MANDATORY_HUMAN_CATEGORIES = {
    "report.account",
    "report.payment",
    "complaint.cheat",
    "complaint.scam",
    "complaint.rmt_ads",
    "complaint.admin"
}

def compute_source_data_hash() -> str:
    """Computes a combined SHA-256 fingerprint of source data and TF-IDF config to validate index cache."""
    h = hashlib.sha256()
    for p in [RULES_PATH, TAXONOMY_PATH, PROTOTYPES_PATH]:
        if os.path.exists(p):
            with open(p, "rb") as f:
                h.update(f.read())
    h.update(str(TFIDF_CONFIG).encode("utf-8"))
    return h.hexdigest()[:16]

# Cross-platform memory utility (works on Windows, Linux, macOS)
def get_process_memory_mb() -> Optional[float]:
    """Returns actual process RAM in MB via psutil or resource; returns None if unavailable (no fake numbers)."""
    try:
        import psutil
        return round(psutil.Process().memory_info().rss / (1024 * 1024), 2)
    except Exception:
        try:
            import resource
            return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 2)
        except Exception:
            return None
