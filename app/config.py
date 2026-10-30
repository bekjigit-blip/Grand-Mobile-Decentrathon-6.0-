import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Data paths
DATA_DIR = BASE_DIR / "data"
RULES_PATH = DATA_DIR / "rules.json"
TAXONOMY_PATH = DATA_DIR / "taxonomy.json"
DB_PATH = BASE_DIR / "copilot_tickets.db"

# Index cache directory
CACHE_DIR = BASE_DIR / "index_cache"
RULES_INDEX_PATH = CACHE_DIR / "rules_index.joblib"
TAXONOMY_INDEX_PATH = CACHE_DIR / "taxonomy_index.joblib"
METADATA_CACHE_PATH = CACHE_DIR / "index_metadata.json"

# TF-IDF Configuration
TFIDF_CONFIG = {
    "version": "1.0.0",
    "word_ngram_range": (1, 2),
    "char_ngram_range": (3, 5),
    "analyzer": "char_wb",
    "min_df": 1,
    "sublinear_tf": True,
    "norm": "l2"
}

# Confidence & Thresholds
CONFIDENCE_THRESHOLD = 0.28
TOP2_MARGIN_THRESHOLD = 0.05
DUPLICATE_TIME_WINDOW_SECONDS = 3600  # 1 hour
DUPLICATE_SIMILARITY_THRESHOLD = 0.85

# Categories that strictly require human intervention
MANDATORY_HUMAN_CATEGORIES = {
    "donation_payment",
    "account_access",
    "appeal_punishment",
    "admin_complaint",
    "player_report_scam"
}
