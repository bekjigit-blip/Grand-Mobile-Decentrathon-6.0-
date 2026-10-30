import json
import os
import re
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

from app.config import (
    TAXONOMY_PATH, TAXONOMY_INDEX_PATH, TFIDF_CONFIG,
    CACHE_DIR, CONFIDENCE_THRESHOLD, TOP2_MARGIN_THRESHOLD
)

class TaxonomyClassifier:
    def __init__(self):
        self.categories: List[Dict[str, Any]] = []
        self.category_ids: List[str] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.prototype_matrix: Optional[sparse.csr_matrix] = None
        self.category_by_id: Dict[str, Dict[str, Any]] = {}

    def build_index(self, taxonomy_file_path: Optional[str] = None) -> Dict[str, Any]:
        """Builds prototype index from taxonomy.json (14 categories)."""
        path = taxonomy_file_path or str(TAXONOMY_PATH)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Taxonomy file not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.categories = data.get("categories", [])
        self.category_ids = [cat["id"] for cat in self.categories]
        self.category_by_id = {cat["id"]: cat for cat in self.categories}

        corpus = []
        for cat in self.categories:
            parts = [
                cat.get("name", ""),
                cat.get("kind", ""),
                cat.get("description", ""),
                " ".join(cat.get("keywords", [])),
                " ".join(cat.get("examples", []))
            ]
            corpus.append(" ".join(parts))

        # TF-IDF combining word n-grams (1,2) with char n-grams (3,5)
        self.vectorizer = TfidfVectorizer(
            ngram_range=TFIDF_CONFIG["word_ngram_range"],
            sublinear_tf=TFIDF_CONFIG["sublinear_tf"],
            norm=TFIDF_CONFIG["norm"]
        )
        self.prototype_matrix = self.vectorizer.fit_transform(corpus)

        os.makedirs(CACHE_DIR, exist_ok=True)
        joblib.dump({
            "vectorizer": self.vectorizer,
            "prototype_matrix": self.prototype_matrix,
            "categories": self.categories,
            "category_ids": self.category_ids,
            "category_by_id": self.category_by_id
        }, TAXONOMY_INDEX_PATH)

        return {
            "total_categories": len(self.category_ids),
            "matrix_shape": self.prototype_matrix.shape
        }

    def load_index(self) -> bool:
        """Loads cached taxonomy index from disk if present."""
        if not os.path.exists(TAXONOMY_INDEX_PATH):
            return False
        cached = joblib.load(TAXONOMY_INDEX_PATH)
        self.vectorizer = cached["vectorizer"]
        self.prototype_matrix = cached["prototype_matrix"]
        self.categories = cached["categories"]
        self.category_ids = cached["category_ids"]
        self.category_by_id = cached["category_by_id"]
        return True

    def classify(self, text: str, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """
        Multilingual category classification based on:
        - TF-IDF prototype cosine similarity
        - Keyword signals
        - Extracted rule citations
        - Margin and confidence checks (explicitly NOT calibrated probability)
        """
        if self.prototype_matrix is None or self.vectorizer is None:
            if not self.load_index():
                self.build_index()

        q_vec = self.vectorizer.transform([text])
        # Raw cosine similarity scores
        raw_scores = (q_vec * self.prototype_matrix.T).toarray()[0].astype(float)

        reasons = []
        text_lower = text.lower()

        # Keyword matching and rule alignment signals
        for i, cat in enumerate(self.categories):
            cat_id = cat["id"]
            # 1. Keywords bonus
            matched_kw = [kw for kw in cat.get("keywords", []) if kw in text_lower]
            if matched_kw:
                bonus = min(0.35, len(matched_kw) * 0.12)
                raw_scores[i] += bonus

            # 2. Rule reference alignment
            raw_rules = extracted.get("rule_refs_raw", [])
            for r in raw_rules:
                for target_ref in cat.get("rule_refs", []):
                    clean_r = re.sub(r'[^\d\.]', '', r)
                    clean_target = re.sub(r'[^\d\.]', '', target_ref)
                    if clean_r and clean_r == clean_target:
                        raw_scores[i] += 0.25
                        reasons.append(f"Ереже сілтемесі ({r}) '{cat_id}' санатымен сәйкес келеді")
                        break

        # Get sorted ranking
        sorted_indices = np.argsort(raw_scores)[::-1]
        top1_idx = sorted_indices[0]
        top2_idx = sorted_indices[1] if len(sorted_indices) > 1 else sorted_indices[0]

        top1_cat_id = self.category_ids[top1_idx]
        top2_cat_id = self.category_ids[top2_idx]

        top1_score = raw_scores[top1_idx]
        top2_score = raw_scores[top2_idx]
        margin = top1_score - top2_score

        # Confidence metric (normalized similarity indicator, explicitly NOT probability)
        confidence = float(min(1.0, max(0.1, top1_score)))
        confidence = round(confidence, 2)

        is_low_confidence = confidence < CONFIDENCE_THRESHOLD
        is_ambiguous = margin < TOP2_MARGIN_THRESHOLD and top1_score > 0.15

        if is_low_confidence:
            reasons.append(f"Төмен ұқсастық ұпайы ({confidence:.2f} < {CONFIDENCE_THRESHOLD})")
        if is_ambiguous:
            reasons.append(f"Екі санат арасындағы айырмашылық тым аз ({top1_cat_id} vs {top2_cat_id}, маржа={margin:.3f})")

        cat_meta = self.category_by_id.get(top1_cat_id, {})
        reasons.append(f"Санат таңдалды: '{cat_meta.get('name', top1_cat_id)}' (ұқсастық={top1_score:.3f})")

        return {
            "category": top1_cat_id,
            "kind": cat_meta.get("kind", "complaint"),
            "confidence": confidence,
            "margin": round(float(margin), 4),
            "is_low_confidence": is_low_confidence,
            "is_ambiguous": is_ambiguous,
            "top2_category": top2_cat_id,
            "reasons": reasons,
            "all_scores": {self.category_ids[idx]: round(float(raw_scores[idx]), 3) for idx in sorted_indices[:5]}
        }
