import json
import os
import re
from typing import Dict, Any, List, Optional
import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

from app.config import RULES_PATH, RULES_INDEX_PATH, TFIDF_CONFIG, CACHE_DIR

class RuleIndexer:
    def __init__(self):
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.rule_matrix: Optional[sparse.csr_matrix] = None
        self.rules_metadata: List[Dict[str, Any]] = []
        # Key: section_id + "::" + ref -> metadata index
        self.key_to_index: Dict[str, int] = {}
        # Ref to list of metadata indices (to handle repeated refs across sections)
        self.ref_to_indices: Dict[str, List[int]] = {}

    def build_index(self, rules_file_path: Optional[str] = None) -> Dict[str, Any]:
        """Builds the rule TF-IDF sparse index from rules.json."""
        path = rules_file_path or str(RULES_PATH)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Rules file not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.rules_metadata = []
        self.key_to_index = {}
        self.ref_to_indices = {}
        corpus = []

        sections = data.get("sections", [])
        for sec in sections:
            sec_id = sec["id"]
            sec_name = sec["name"]

            # 1. Index RP Definitions (no fake point numbers assigned)
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
                ref = pt["ref"]
                pt_text = pt["text"]
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

        # Vectorizer combining word n-grams with sublinear TF scaling
        self.vectorizer = TfidfVectorizer(
            ngram_range=TFIDF_CONFIG["word_ngram_range"],
            sublinear_tf=TFIDF_CONFIG["sublinear_tf"],
            norm=TFIDF_CONFIG["norm"]
        )
        self.rule_matrix = self.vectorizer.fit_transform(corpus)

        # Save to disk cache
        os.makedirs(CACHE_DIR, exist_ok=True)
        joblib.dump({
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
        """Loads cached index from disk if available."""
        if not os.path.exists(RULES_INDEX_PATH):
            return False
        cached = joblib.load(RULES_INDEX_PATH)
        self.vectorizer = cached["vectorizer"]
        self.rule_matrix = cached["rule_matrix"]
        self.rules_metadata = cached["rules_metadata"]
        self.key_to_index = cached["key_to_index"]
        self.ref_to_indices = cached["ref_to_indices"]
        return True

    def search_rules(
        self,
        query_text: str,
        top_k: int = 5,
        rule_refs_raw: Optional[List[str]] = None,
        preferred_section_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Searches rules using sparse TF-IDF cosine similarity and validates citations.
        Returns list of matched rules with section_id, section_name, ref, text, score.
        """
        if self.rule_matrix is None or self.vectorizer is None:
            if not self.load_index():
                self.build_index()

        q_vec = self.vectorizer.transform([query_text])
        # Sparse dot product
        scores = (q_vec * self.rule_matrix.T).toarray()[0]

        # Process user-provided raw rule references safely (distinguish GZ vs ЖБ)
        if rule_refs_raw:
            for raw_ref in rule_refs_raw:
                cleaned_ref = raw_ref.strip()
                is_gz = "gz" in cleaned_ref.lower() or "зз" in cleaned_ref.lower()
                is_zhb = "жб" in cleaned_ref.lower()
                clean_num = re.sub(r'[^\d\.]', '', cleaned_ref)

                # Find potential indices
                matched_indices = []
                if is_gz:
                    # Target section 3 (sec_greenzone)
                    for key, idx in self.key_to_index.items():
                        if "sec_greenzone" in key and (clean_num in key or clean_num == ""):
                            matched_indices.append(idx)
                elif is_zhb:
                    # Target section 10 (sec_appeals)
                    for key, idx in self.key_to_index.items():
                        if "sec_appeals" in key and (clean_num in key or clean_num == ""):
                            matched_indices.append(idx)
                elif clean_num in self.ref_to_indices:
                    matched_indices.extend(self.ref_to_indices[clean_num])

                for idx in matched_indices:
                    # Apply boost for valid cited rule
                    scores[idx] += 0.35

        # Boost preferred section from category taxonomy if provided
        if preferred_section_id:
            for idx, meta in enumerate(self.rules_metadata):
                if meta["section_id"] == preferred_section_id:
                    scores[idx] += 0.12

        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score > 0.05:
                meta = self.rules_metadata[idx]
                results.append({
                    "section_id": meta["section_id"],
                    "section_name": meta["section_name"],
                    "ref": meta["ref"],
                    "is_rp_term": meta.get("is_rp_term", False),
                    "internal_key": meta["internal_key"],
                    "text": meta["text"],
                    "score": round(score, 4)
                })

        return results
