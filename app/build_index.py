import time
import os
import sys
import json
from app.rule_indexer import RuleIndexer
from app.taxonomy_classifier import TaxonomyClassifier
from app.config import CACHE_DIR, METADATA_CACHE_PATH, RULES_INDEX_PATH, TAXONOMY_INDEX_PATH

def main():
    print("=" * 60)
    print("Grand Mobile × Decentrathon 6.0: Building Offline TF-IDF Indexes")
    print("=" * 60)

    start_time = time.time()
    os.makedirs(CACHE_DIR, exist_ok=True)

    # 1. Build Rule Index
    print("[1/2] Building Rules TF-IDF Index...")
    rule_indexer = RuleIndexer()
    r_stats = rule_indexer.build_index()
    print(f"      Indexed {r_stats['total_indexed']} points/RP terms across {r_stats['sections_count']} sections.")
    print(f"      Rule Matrix Shape: {r_stats['matrix_shape']}")

    # 2. Build Taxonomy Classifier Index
    print("[2/2] Building Taxonomy TF-IDF Prototype Index...")
    tax_classifier = TaxonomyClassifier()
    t_stats = tax_classifier.build_index()
    print(f"      Indexed {t_stats['total_categories']} category prototypes.")
    print(f"      Taxonomy Matrix Shape: {t_stats['matrix_shape']}")

    elapsed = time.time() - start_time

    # Compute disk sizes
    rules_size_kb = os.path.getsize(RULES_INDEX_PATH) / 1024 if os.path.exists(RULES_INDEX_PATH) else 0
    tax_size_kb = os.path.getsize(TAXONOMY_INDEX_PATH) / 1024 if os.path.exists(TAXONOMY_INDEX_PATH) else 0

    meta = {
        "build_timestamp": time.time(),
        "build_duration_seconds": round(elapsed, 4),
        "rules_indexed_count": r_stats['total_indexed'],
        "rules_file_size_kb": round(rules_size_kb, 2),
        "taxonomy_categories_count": t_stats['total_categories'],
        "taxonomy_file_size_kb": round(tax_size_kb, 2),
        "status": "ready"
    }

    with open(METADATA_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("=" * 60)
    print(f"Indexes built successfully in {elapsed:.3f} seconds!")
    print(f"Rules Index Cache Size: {rules_size_kb:.1f} KB")
    print(f"Taxonomy Index Cache Size: {tax_size_kb:.1f} KB")
    print(f"Saved cache to: {CACHE_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
