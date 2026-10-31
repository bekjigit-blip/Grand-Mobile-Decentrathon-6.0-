import json
import os
import re
from typing import Dict, Any, List, Optional
import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
import joblib

from app.config import (
    RULES_PATH, RULES_INDEX_PATH, TFIDF_CONFIG, CACHE_DIR,
    SEMANTIC_CITATION_THRESHOLD
)

class RuleIndexer:
    def __init__(self):
        self.vectorizer: Optional[FeatureUnion] = None
        self.rule_matrix: Optional[sparse.csr_matrix] = None
        self.rules_metadata: List[Dict[str, Any]] = []
        self.key_to_index: Dict[str, int] = {}
        self.ref_to_indices: Dict[str, List[int]] = {}
        self.config_version = TFIDF_CONFIG["version"]

    def build_index(self, rules_file_path: Optional[str] = None) -> Dict[str, Any]:
        """Builds combined Word + Char_wb sparse TF-IDF index from rules.json."""
        path = rules_file_path or str(RULES_PATH)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Rules file not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.rules_metadata = []
        self.key_to_index = {}
        self.ref_to_indices = {}
        corpus = []

        # Support both official rules[] and sections[]
        sections = data.get("rules") or data.get("sections") or []

        for sec in sections:
            sec_id = str(sec.get("id", ""))
            sec_name = sec.get("name") or sec.get("text") or f"Раздел {sec_id}"

            # 1. Index RP Definitions if present
            for rp in sec.get("rp_definitions", []):
                term = rp["term"]
                rp_text = rp["text"]
                internal_key = f"{sec_id}::RP_{term}"
                meta = {
                    "section_id": sec_id,
                    "section_name": sec_name,
                    "ref": term,
                    "is_rp_term": True,
                    "internal_key": internal_key,
                    "text": f"{term}: {rp_text}"
                }
                idx = len(self.rules_metadata)
                self.rules_metadata.append(meta)
                self.key_to_index[internal_key] = idx
                corpus.append(f"{sec_name} {term} {rp_text}")

            # 2. Index Points (unique key: section_id + "::" + ref)
            for pt in sec.get("points", []):
                ref = str(pt.get("ref", "")).strip()
                pt_text = pt.get("text", "")
                internal_key = f"{sec_id}::{ref}"

                meta = {
                    "section_id": sec_id,
                    "section_name": sec_name,
                    "ref": ref,
                    "is_rp_term": False,
                    "internal_key": internal_key,
                    "text": pt_text
                }
                idx = len(self.rules_metadata)
                self.rules_metadata.append(meta)
                self.key_to_index[internal_key] = idx

                if ref not in self.ref_to_indices:
                    self.ref_to_indices[ref] = []
                self.ref_to_indices[ref].append(idx)

                corpus.append(f"{sec_name} {ref} {pt_text}")

        # Combine Word n-gram and Char_wb n-gram with weights
        word_vec = TfidfVectorizer(
            analyzer='word',
            ngram_range=TFIDF_CONFIG["word_ngram_range"],
            sublinear_tf=TFIDF_CONFIG["sublinear_tf"],
            norm=TFIDF_CONFIG["norm"]
        )
        char_vec = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=TFIDF_CONFIG["char_ngram_range"],
            sublinear_tf=TFIDF_CONFIG["sublinear_tf"],
            norm=TFIDF_CONFIG["norm"]
        )

        self.vectorizer = FeatureUnion(
            transformer_list=[
                ('word', word_vec),
                ('char', char_vec)
            ],
            transformer_weights={
                'word': TFIDF_CONFIG["word_weight"],
                'char': TFIDF_CONFIG["char_weight"]
            }
        )

        self.rule_matrix = self.vectorizer.fit_transform(corpus)

        os.makedirs(CACHE_DIR, exist_ok=True)
        joblib.dump({
            "config_version": self.config_version,
            "vectorizer": self.vectorizer,
            "rule_matrix": self.rule_matrix,
            "rules_metadata": self.rules_metadata,
            "key_to_index": self.key_to_index,
            "ref_to_indices": self.ref_to_indices
        }, RULES_INDEX_PATH)

        return {
            "total_indexed": len(self.rules_metadata),
            "matrix_shape": self.rule_matrix.shape,
            "sections_count": len(sections)
        }

    def load_index(self) -> bool:
        """Loads cached index if available and version matches."""
        if not os.path.exists(RULES_INDEX_PATH):
            return False
        try:
            cached = joblib.load(RULES_INDEX_PATH)
            if cached.get("config_version") != self.config_version:
                return False
            self.vectorizer = cached["vectorizer"]
            self.rule_matrix = cached["rule_matrix"]
            self.rules_metadata = cached["rules_metadata"]
            self.key_to_index = cached["key_to_index"]
            self.ref_to_indices = cached["ref_to_indices"]
            return True
        except Exception:
            return False

    def search_rules(
        self,
        query_text: str,
        top_k: int = 3,
        rule_refs_raw: Optional[List[str]] = None,
        preferred_section_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Searches rules using combined sparse TF-IDF and validates citations.
        Enforces semantic relevance threshold so irrelevant forced citations are rejected.
        """
        if self.rule_matrix is None or self.vectorizer is None:
            if not self.load_index():
                self.build_index()

        if not query_text or not query_text.strip():
            return []

        q_vec = self.vectorizer.transform([query_text])
        # Sparse dot product
        raw_scores = (q_vec * self.rule_matrix.T).toarray()[0]
        scores = raw_scores.copy()

        # Check semantic relevance before applying player citation boost
        # Fixes issue where "zzzzzz" + rule_refs_raw=["8.1"] caused irrelevant 8.1 rule to be returned!
        if rule_refs_raw:
            for raw_ref in rule_refs_raw:
                cleaned_ref = str(raw_ref).strip()
                is_gz = "gz" in cleaned_ref.lower() or "зз" in cleaned_ref.lower()
                is_zhb = "жб" in cleaned_ref.lower()
                clean_num = re.sub(r'[^0-9\.]', '', cleaned_ref)

                matched_indices = []
                if is_gz:
                    for key, idx in self.key_to_index.items():
                        if "sec_greenzone" in key or key.startswith("3::"):
                            if not clean_num or clean_num in key:
                                matched_indices.append(idx)
                elif is_zhb:
                    for key, idx in self.key_to_index.items():
                        if "sec_appeals" in key or key.startswith("10::"):
                            if not clean_num or clean_num in key:
                                matched_indices.append(idx)
                elif clean_num in self.ref_to_indices:
                    matched_indices.extend(self.ref_to_indices[clean_num])

                for idx in matched_indices:
                    # ONLY apply citation boost if raw semantic similarity is non-trivial!
                    if raw_scores[idx] >= SEMANTIC_CITATION_THRESHOLD:
                        scores[idx] += 0.35

        # Only consider results that exceed the semantic threshold
        valid_indices = [i for i, s in enumerate(scores) if s >= SEMANTIC_CITATION_THRESHOLD]
        if not valid_indices:
            return []

        sorted_valid = sorted(valid_indices, key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in sorted_valid:
            meta = self.rules_metadata[idx]
            # Exclude pure RP definitions from numeric citation list
            results.append({
                "section_id": meta["section_id"],
                "section_name": meta["section_name"],
                "ref": meta["ref"],
                "is_rp_term": meta.get("is_rp_term", False),
                "internal_key": meta["internal_key"],
                "text": meta["text"],
                "score": round(float(scores[idx]), 4)
            })

        return results
