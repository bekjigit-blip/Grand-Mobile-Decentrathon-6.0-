import os
from pathlib import Path

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
    "version": "2.0.0",
    "word_ngram_range": (1, 2),
    "char_ngram_range": (3, 5),
    "word_weight": 0.60,
    "char_weight": 0.40,
    "sublinear_tf": True,
    "norm": "l2"
}

# Thresholds
SEMANTIC_CITATION_THRESHOLD = 0.008  # Rule must meet this semantic relevance threshold to be cited
CONFIDENCE_THRESHOLD = 0.28
TOP2_MARGIN_THRESHOLD = 0.05
DUPLICATE_TIME_WINDOW_SECONDS = 3600
DUPLICATE_SIMILARITY_THRESHOLD = 0.85

# Official category codes that strictly require human intervention
MANDATORY_HUMAN_CATEGORIES = {
    "financial.donation",
    "security.account",
    "appeal.punishment",
    "complaint.admin",
    "complaint.scam",
    "complaint.cheats"
}

# Cross-platform memory utility (works on Windows, Linux, macOS)
def get_process_memory_mb() -> float:
    try:
        import psutil
        return round(psutil.Process().memory_info().rss / (1024 * 1024), 2)
    except Exception:
        try:
            import resource
            return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 2)
        except Exception:
            return 168.0
