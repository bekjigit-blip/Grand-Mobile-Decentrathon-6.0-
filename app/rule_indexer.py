import json
import os
import re
from typing import Dict, Any, List, Optional, Set
import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
import joblib

from app.config import (
    RULES_PATH, RULES_INDEX_PATH, TFIDF_CONFIG, CACHE_DIR,
    SEMANTIC_CITATION_THRESHOLD, compute_source_data_hash
)

CATEGORY_TITLES = {
    "general": "1. Общие правила сервера",
    "combat": "2. Правила ведения боя и нанесения урона",
    "greenzone": "3. Правила Зеленых Зон (Green Zone / GZ)",
    "chat": "4. Правила игрового чата и голосовой связи",
    "roleplay": "5. Правила RolePlay процесса и отыгровки",
    "cheats": "6. Запрещенное ПО, читы и использование багов",
    "economy": "7. Экономика, торговля и мошенничество",
    "accounts": "8. Аккаунты, безопасность и донат",
    "admin": "9. Взаимодействие с администрацией",
    "appeals": "10. Подача жалоб и обжалование вердиктов (ЖБ)",
    "organizations": "11. Государственные и криминальные структуры"
}

# Relevant section mapping by ticket category (stops irrelevant rules for questions/offtopic/help)
CATEGORY_ALLOWED_SECTIONS: Dict[str, Set[str]] = {
    "complaint.dm": {"2"},                      # Combat (DM, DB)
    "complaint.insult": {"4"},                  # Chat
    "complaint.cheat": {"6"},                   # Cheats / soft
    "complaint.scam": {"7"},                    # Economy / scam
    "complaint.rmt_ads": {"4", "7"},            # Chat ads & economy RMT
    "complaint.admin": {"9", "10"},             # Admin & appeals
    "complaint.other": {"1", "2", "3", "5"},    # General, combat, GZ, roleplay
    "complaint.invalid": set(),
    "report.complaint": {"2", "4", "6"},        # Fast in-game reports
    "report.account": {"8"},                    # Accounts & security
    "report.payment": {"7", "8"},               # Economy & donation
    "report.question": set(),                   # Questions need NO penal citations
    "report.help": set(),                       # Help needs NO penal citations
    "report.offtopic": set()                    # Offtopic needs NO penal citations
}

class RuleIndexer:
    def __init__(self):
        self.vectorizer: Optional[FeatureUnion] = None
        self.rule_matrix: Optional[sparse.csr_matrix] = None
        self.rules_metadata: List[Dict[str, Any]] = []
        self.key_to_index: Dict[str, int] = {}
        self.ref_to_indices: Dict[str, List[int]] = {}
        self.config_version = TFIDF_CONFIG["version"]

    def build_index(self, rules_file_path: Optional[str] = None) -> Dict[str, Any]:
        """Builds combined Word + Char_wb sparse TF-IDF index from authentic rules.json."""
        path = rules_file_path or str(RULES_PATH)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Rules file not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.rules_metadata = []
        self.key_to_index = {}
        self.ref_to_indices = {}
        corpus = []

        sections = data.get("rules") or data.get("sections") or []

        for sec in sections:
            sec_id = str(sec.get("id", "")).strip()
            sec_cat = str(sec.get("category", "")).strip().lower()

            # Take section name strictly from category / clean name, NEVER the full description text
            sec_name = sec.get("name") or CATEGORY_TITLES.get(sec_cat, f"Раздел {sec_id}: {sec_cat}")

            # 1. Index RP Definitions if present
            for rp in sec.get("rp_definitions", []):
                term = str(rp.get("term", "")).strip()
                rp_text = str(rp.get("text", "")).strip()
                internal_key = f"{sec_id}::{term}"
                meta = {
                    "section_id": sec_id,
                    "section_category": sec_cat,
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
                pt_text = str(pt.get("text", "")).strip()
                internal_key = f"{sec_id}::{ref}"

                meta = {
                    "section_id": sec_id,
                    "section_category": sec_cat,
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
            "source_data_hash": compute_source_data_hash(),
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
        """Loads cached index if present, config matches, and source data hash matches."""
        if not os.path.exists(RULES_INDEX_PATH):
            return False
        try:
            cached = joblib.load(RULES_INDEX_PATH)
            if cached.get("config_version") != self.config_version:
                return False
            if cached.get("source_data_hash") != compute_source_data_hash():
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
        category: Optional[str] = None,
        top_k: int = 3,
        rule_refs_raw: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Searches rules with category candidate constraint and semantic relevance gate.
        - If query is for general question/help/offtopic and player did NOT ask for a rule, returns [] (Requirement 5).
        - Prevents irrelevant citations: only returns rules that match category candidates and pass semantic threshold.
        """
        if self.rule_matrix is None or self.vectorizer is None:
            if not self.load_index():
                self.build_index()

        if not query_text or not query_text.strip():
            return []

        # Questions, general in-game help, offtopic, or invalid complaints do not cite rules unless player asked
        if category in {"report.question", "report.help", "report.offtopic", "complaint.invalid"} and not rule_refs_raw:
            return []

        q_vec = self.vectorizer.transform([query_text])
        raw_scores = (q_vec * self.rule_matrix.T).toarray()[0]
        scores = raw_scores.copy()

        # Check semantic relevance before applying player citation boost
        if rule_refs_raw:
            for raw_ref in rule_refs_raw:
                cleaned_ref = str(raw_ref).strip()
                is_gz = "gz" in cleaned_ref.lower() or "зз" in cleaned_ref.lower()
                is_zhb = "жб" in cleaned_ref.lower()
                clean_num = re.sub(r'[^0-9\.]', '', cleaned_ref)

                matched_indices = []
                if is_gz:
                    # Section 3 is Green Zone
                    for key, idx in self.key_to_index.items():
                        if key.startswith("3::"):
                            if not clean_num or clean_num in key:
                                matched_indices.append(idx)
                elif is_zhb:
                    # Section 10 is Appeals / ЖБ
                    for key, idx in self.key_to_index.items():
                        if key.startswith("10::"):
                            if not clean_num or clean_num in key:
                                matched_indices.append(idx)
                elif clean_num in self.ref_to_indices:
                    matched_indices.extend(self.ref_to_indices[clean_num])

                for idx in matched_indices:
                    # ONLY apply citation boost if raw semantic similarity is non-trivial!
                    if raw_scores[idx] >= SEMANTIC_CITATION_THRESHOLD:
                        scores[idx] += 0.35

        # Constrain candidates by category if category has defined relevant sections
        allowed_sections = CATEGORY_ALLOWED_SECTIONS.get(category) if category else None

        valid_indices = []
        for i, s in enumerate(scores):
            meta = self.rules_metadata[i]
            # Disallow rules outside category-allowed sections (unless explicitly asked by player)
            if allowed_sections is not None and meta["section_id"] not in allowed_sections and not rule_refs_raw:
                continue
            if s >= SEMANTIC_CITATION_THRESHOLD:
                valid_indices.append(i)

        if not valid_indices:
            return []

        sorted_valid = sorted(valid_indices, key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in sorted_valid:
            meta = self.rules_metadata[idx]
            results.append({
                "section_id": meta["section_id"],
                "section_category": meta.get("section_category", ""),
                "section_name": meta["section_name"],
                "ref": meta["ref"],
                "is_rp_term": meta.get("is_rp_term", False),
                "internal_key": meta["internal_key"],
                "text": meta["text"],
                "score": round(float(scores[idx]), 4)
            })

        return results
