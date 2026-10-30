import time
import os
import resource
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.triage_service import get_triage_service
from app.config import TFIDF_CONFIG, RULES_INDEX_PATH, TAXONOMY_INDEX_PATH, METADATA_CACHE_PATH
import json

app = FastAPI(
    title="Grand Mobile Support Copilot API",
    description="Offline CPU TF-IDF Triage Service for Grand Mobile × Decentrathon 6.0",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVER_START_TIME = time.time()

# Request and Response schemas
class ExtractedData(BaseModel):
    nicknames: List[str] = Field(default_factory=list)
    rule_refs_raw: List[str] = Field(default_factory=list)
    ids: List[str] = Field(default_factory=list)
    has_attachments: bool = False

class DraftReply(BaseModel):
    text: str
    cited: List[str] = Field(default_factory=list)

class TriageRequest(BaseModel):
    ticket_id: Optional[str] = None
    reporter_hash: Optional[str] = None
    created_at: Optional[str] = None
    server_lang: Optional[str] = None
    lang: Optional[str] = None
    text: Optional[str] = None
    body: Optional[str] = None
    message: Optional[str] = None
    images_count: Optional[int] = 0
    rule_refs_raw: Optional[List[str]] = None
    attachments: Optional[List[Any]] = None

class TriageResponse(BaseModel):
    ticket_id: Optional[str] = None
    lang: str
    category: str
    priority: str
    is_spam_or_duplicate: bool
    extracted: ExtractedData
    draft_reply: DraftReply
    needs_human: bool
    confidence: float
    reasons: List[str]
    matched_rules: Optional[List[Dict[str, Any]]] = None

@app.on_event("startup")
def startup_event():
    service = get_triage_service()
    service.initialize()

@app.get("/health")
def health():
    """Health check endpoint measuring memory, status, index stats, and zero API costs."""
    uptime_sec = round(time.time() - SERVER_START_TIME, 2)
    # Memory usage in MB
    try:
        mem_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On Linux ru_maxrss is in KB
        mem_mb = round(mem_kb / 1024.0, 2)
    except Exception:
        mem_mb = 0.0

    rules_indexed = 0
    tax_categories = 14
    if os.path.exists(METADATA_CACHE_PATH):
        try:
            with open(METADATA_CACHE_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
                rules_indexed = meta.get("rules_indexed_count", 286)
                tax_categories = meta.get("taxonomy_categories_count", 14)
        except Exception:
            pass

    return {
        "status": "ok",
        "service": "Grand Mobile Support Copilot",
        "version": "1.0.0",
        "uptime_seconds": uptime_sec,
        "memory_rss_mb": mem_mb,
        "offline_cpu_only": True,
        "external_api_cost_usd": 0.00,
        "index_status": {
            "rules_indexed_count": rules_indexed,
            "taxonomy_categories": tax_categories,
            "sparse_format": "scipy.csr_matrix",
            "tfidf_version": TFIDF_CONFIG["version"]
        }
    }

@app.post("/triage", response_model=TriageResponse)
def triage(request_data: TriageRequest):
    """
    Standard Decentrathon 6.0 Triage Endpoint.
    Conforms strictly to requested output schema.
    """
    service = get_triage_service()
    ticket_dict = request_data.model_dump()
    result = service.triage_ticket(ticket_dict)
    return result

@app.get("/api/rules")
def get_rules():
    """Returns official rules with 11 sections and 266 points for UI explorer."""
    from app.config import RULES_PATH
    if os.path.exists(RULES_PATH):
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"sections": []}

@app.get("/api/taxonomy")
def get_taxonomy():
    """Returns 14 taxonomy categories for UI filter and prototype explorer."""
    from app.config import TAXONOMY_PATH
    if os.path.exists(TAXONOMY_PATH):
        with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"categories": []}

@app.get("/api/sample_tickets")
def get_sample_tickets():
    """Returns preset sample tickets from valid.jsonl for demonstration and testing."""
    from app.config import DATA_DIR
    sample_path = DATA_DIR / "sample_tickets.jsonl"
    results = []
    if os.path.exists(sample_path):
        service = get_triage_service()
        with open(sample_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    t = json.loads(line)
                    triaged = service.triage_ticket(t)
                    results.append({
                        **t,
                        "triage": triaged
                    })
    return results

@app.get("/api/benchmark")
def get_benchmark():
    from app.benchmark import run_quick_benchmark
    return run_quick_benchmark()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.server:app", host="127.0.0.1", port=8005, reload=False)
