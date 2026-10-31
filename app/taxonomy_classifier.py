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
    TAXONOMY_PATH, PROTOTYPES_PATH, TAXONOMY_INDEX_PATH, TFIDF_CONFIG,
    CACHE_DIR, CONFIDENCE_THRESHOLD, TOP2_MARGIN_THRESHOLD
)

class TaxonomyClassifier:
    def __init__(self):
        self.categories: List[Dict[str, Any]] = []
        self.category_codes: List[str] = []
        self.category_by_code: Dict[str, Dict[str, Any]] = {}
        self.vectorizer: Optional[FeatureUnion] = None
        self.prototype_matrix: Optional[sparse.csr_matrix] = None
        self.config_version = TFIDF_CONFIG["version"]

    def build_index(self, taxonomy_file_path: Optional[str] = None) -> Dict[str, Any]:
        """Builds combined Word + Char_wb prototype index for the 14 official categories."""
        tax_path = taxonomy_file_path or str(TAXONOMY_PATH)
        if not os.path.exists(tax_path):
            raise FileNotFoundError(f"Taxonomy file not found at: {tax_path}")

        with open(tax_path, "r", encoding="utf-8") as f:
            tax_data = json.load(f)

        proto_data = {}
        if os.path.exists(PROTOTYPES_PATH):
            with open(PROTOTYPES_PATH, "r", encoding="utf-8") as f:
                proto_data = json.load(f).get("prototypes", {})

        raw_categories = tax_data.get("categories", [])
        self.categories = []
        self.category_codes = []
        self.category_by_code = {}

        corpus = []
        for cat in raw_categories:
            code = cat.get("code") or cat.get("id")
            if not code:
                continue

            self.categories.append(cat)
            self.category_codes.append(code)
            self.category_by_code[code] = cat

            proto = proto_data.get(code, {})
            keywords = proto.get("keywords", []) + cat.get("keywords", [])
            examples = proto.get("examples", []) + cat.get("examples", [])

            parts = [
                code,
                cat.get("kind", ""),
                cat.get("name", ""),
                cat.get("description", ""),
                " ".join(keywords),
                " ".join(examples)
            ]
            corpus.append(" ".join(parts))

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

        self.prototype_matrix = self.vectorizer.fit_transform(corpus)

        os.makedirs(CACHE_DIR, exist_ok=True)
        joblib.dump({
            "config_version": self.config_version,
            "vectorizer": self.vectorizer,
            "prototype_matrix": self.prototype_matrix,
            "categories": self.categories,
            "category_codes": self.category_codes,
            "category_by_code": self.category_by_code
        }, TAXONOMY_INDEX_PATH)

        return {
            "total_categories": len(self.category_codes),
            "matrix_shape": self.prototype_matrix.shape
        }

    def load_index(self) -> bool:
        """Loads cached taxonomy index if present and version matches."""
        if not os.path.exists(TAXONOMY_INDEX_PATH):
            return False
        try:
            cached = joblib.load(TAXONOMY_INDEX_PATH)
            if cached.get("config_version") != self.config_version:
                return False
            self.vectorizer = cached["vectorizer"]
            self.prototype_matrix = cached["prototype_matrix"]
            self.categories = cached["categories"]
            self.category_codes = cached["category_codes"]
            self.category_by_code = cached["category_by_code"]
            return True
        except Exception:
            return False

    def classify(
        self,
        text: str,
        extracted: Dict[str, Any],
        kind_constraint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Multilingual category classification strictly returning official dot-separated codes.
        Constrains candidates by ticket kind if provided.
        """
        if self.prototype_matrix is None or self.vectorizer is None:
            if not self.load_index():
                self.build_index()

        q_vec = self.vectorizer.transform([text])
        raw_scores = (q_vec * self.prototype_matrix.T).toarray()[0].astype(float)
        reasons = []
        text_lower = text.lower()

        # Load prototype keywords for signal boosting
        proto_data = {}
        if os.path.exists(PROTOTYPES_PATH):
            try:
                with open(PROTOTYPES_PATH, "r", encoding="utf-8") as f:
                    proto_data = json.load(f).get("prototypes", {})
            except Exception:
                pass

        # Keywords bonus & rule alignment
        for i, code in enumerate(self.category_codes):
            cat = self.category_by_code[code]
            proto = proto_data.get(code, {})
            keywords = proto.get("keywords", []) + cat.get("keywords", [])

            matched_kw = [kw for kw in keywords if kw in text_lower]
            if matched_kw:
                bonus = min(0.40, len(matched_kw) * 0.15)
                raw_scores[i] += bonus

            # Decisive domain signal boosts
            if code == "complaint.cheats":
                if any(w in text_lower for w in ["speedhack", "летает", "fly", "flying", "рванка", "аим", "софт", "читтер", "читер", "спидхак"]):
                    raw_scores[i] += 0.50
            elif code == "appeal.punishment":
                if any(w in text_lower for w in ["обжалован", "снять наказание", "ошибочный бан", "ошибочно посадил", "разбан", "снизить срок", "жазаны алып таста", "апелляци", "деморган ни за что"]):
                    raw_scores[i] += 0.50
            elif code == "security.account":
                if any(w in text_lower for w in ["аккаунт ұрлан", "паролін ауыстыр", "взломали аккаунт", "украли аккаунт", "сменили почту", "взлом", "аккаунтымды біреу"]):
                    raw_scores[i] += 0.50
            elif code == "financial.donation":
                if any(w in text_lower for w in ["донат", "каспи", "чек прикреп", "коинов нет", "grand coins", "деньги ушли", "төлем жасадым"]):
                    raw_scores[i] += 0.40

            # Rule reference alignment
            raw_rules = extracted.get("rule_refs", [])
            for r in raw_rules:
                for target_ref in cat.get("rule_refs", []):
                    clean_r = re.sub(r'[^0-9\.]', '', r)
                    clean_target = re.sub(r'[^0-9\.]', '', target_ref)
                    if clean_r and clean_r == clean_target:
                        raw_scores[i] += 0.30
                        reasons.append(f"Ереже сілтемесі ({r}) '{code}' санатымен сәйкес келеді")
                        break

        # Filter by kind constraint if specified
        valid_indices = list(range(len(self.category_codes)))
        if kind_constraint:
            clean_kind = kind_constraint.strip().lower()
            matching_indices = [
                i for i, code in enumerate(self.category_codes)
                if self.category_by_code[code].get("kind") == clean_kind or code.startswith(clean_kind + ".")
            ]
            if matching_indices:
                valid_indices = matching_indices

        # Sort valid indices by score
        sorted_indices = sorted(valid_indices, key=lambda i: raw_scores[i], reverse=True)
        top1_idx = sorted_indices[0]
        top2_idx = sorted_indices[1] if len(sorted_indices) > 1 else sorted_indices[0]

        top1_code = self.category_codes[top1_idx]
        top2_code = self.category_codes[top2_idx]

        top1_score = raw_scores[top1_idx]
        top2_score = raw_scores[top2_idx]
        margin = top1_score - top2_score

        confidence = round(float(min(1.0, max(0.0, top1_score))), 2)

        is_low_confidence = confidence < CONFIDENCE_THRESHOLD
        is_ambiguous = margin < TOP2_MARGIN_THRESHOLD and top1_score > 0.15

        if is_low_confidence:
            reasons.append(f"Төмен ұқсастық ұпайы ({confidence:.2f} < {CONFIDENCE_THRESHOLD})")
        if is_ambiguous:
            reasons.append(f"Екі санат арасындағы маржа аз ({top1_code} vs {top2_code}, маржа={margin:.3f})")

        cat_meta = self.category_by_code.get(top1_code, {})
        reasons.append(f"Санат анықталды: '{top1_code}' (ұқсастық={top1_score:.3f})")

        return {
            "category": top1_code,
            "kind": cat_meta.get("kind", "complaint"),
            "priority": cat_meta.get("priority", "p2"),
            "confidence": confidence,
            "margin": round(float(margin), 4),
            "is_low_confidence": is_low_confidence,
            "is_ambiguous": is_ambiguous,
            "top2_category": top2_code,
            "reasons": reasons
        }
