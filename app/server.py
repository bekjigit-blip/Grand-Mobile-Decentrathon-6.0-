import time
import os
from typing import Dict, Any, List, Optional, Union
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.triage_service import get_triage_service
from app.config import (
    TFIDF_CONFIG, RULES_INDEX_PATH, TAXONOMY_INDEX_PATH, METADATA_CACHE_PATH,
    get_process_memory_mb, RULES_PATH, TAXONOMY_PATH, DATA_DIR
)
from app.deduplication import save_admin_action, get_admin_actions
import json

app = FastAPI(
    title="Grand Mobile Support Copilot API",
    description="Offline CPU TF-IDF Triage Service for Grand Mobile × Decentrathon 6.0",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVER_START_TIME = time.time()

# --- Official Decentrathon 6.0 Pydantic Schemas ---

class MessageItem(BaseModel):
    role: str = "player"
    text: Optional[str] = ""
    attachments: Optional[Union[int, List[Any]]] = 0

class ExtractedData(BaseModel):
    nickname: Optional[str] = None
    rule_refs: List[str] = Field(default_factory=list)
    has_evidence: bool = False
    server: Optional[str] = None

class DraftReply(BaseModel):
    lang: str = "ru"
    text: str
    cited: List[str] = Field(default_factory=list)

class TriageRequest(BaseModel):
    # Official contract format
    kind: Optional[str] = None
    messages: Optional[List[MessageItem]] = None
    
    # Flat / legacy format support
    ticket_id: Optional[str] = None
    reporter_hash: Optional[str] = None
    created_at: Optional[str] = None
    server_lang: Optional[str] = None
    lang: Optional[str] = None
    text: Optional[str] = None
    body: Optional[str] = None
    message: Optional[str] = None
    images_count: Optional[int] = 0
    rule_refs_raw: Optional[Union[str, List[str]]] = None
    attachments: Optional[Union[int, List[Any]]] = None
    server: Optional[str] = None

class TriageResponse(BaseModel):
    lang: str
    category: str
    priority: str
    is_spam_or_duplicate: bool
    extracted: ExtractedData
    draft_reply: DraftReply
    needs_human: bool
    confidence: float
    reasons: List[str]
    ticket_id: Optional[str] = None
    matched_rules: Optional[List[Dict[str, Any]]] = None

class AdminActionRequest(BaseModel):
    ticket_id: str
    status: str
    draft_text: Optional[str] = ""

# --- Endpoints ---

@app.on_event("startup")
def startup_event():
    service = get_triage_service()
    service.initialize()

@app.get("/health")
def health():
    """Cross-platform health check endpoint (Windows, Linux, macOS compatible)."""
    uptime_sec = round(time.time() - SERVER_START_TIME, 2)
    mem_mb = get_process_memory_mb()

    rules_indexed = 0
    tax_categories = 14
    if os.path.exists(METADATA_CACHE_PATH):
        try:
            with open(METADATA_CACHE_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
                rules_indexed = meta.get("rules_indexed_count", 266)
                tax_categories = meta.get("taxonomy_categories_count", 14)
        except Exception:
            pass

    return {
        "status": "ok",
        "service": "Grand Mobile Support Copilot",
        "version": "2.0.0",
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
    Strictly conforms to official schema.
    """
    service = get_triage_service()
    ticket_dict = request_data.model_dump()
    result = service.triage_ticket(ticket_dict)
    return result

@app.get("/api/rules")
def get_rules():
    """Returns official rules (11 sections, 266 points) for UI explorer."""
    if os.path.exists(RULES_PATH):
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"rules": []}

@app.get("/api/taxonomy")
def get_taxonomy():
    """Returns 14 taxonomy categories with official dot-separated codes."""
    if os.path.exists(TAXONOMY_PATH):
        with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"categories": []}

@app.get("/api/sample_tickets")
def get_sample_tickets():
    """Returns sample tickets merged with SQLite-persisted admin actions."""
    sample_path = DATA_DIR / "sample_tickets.jsonl"
    results = []
    admin_actions = get_admin_actions()

    if os.path.exists(sample_path):
        service = get_triage_service()
        with open(sample_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    t = json.loads(line)
                    triaged = service.triage_ticket(t)
                    t_id = t.get("ticket_id") or triaged.get("ticket_id")
                    
                    # Merge persisted admin actions if any
                    persisted = admin_actions.get(t_id, {})
                    status = persisted.get("status", "pending")
                    if persisted.get("draft_text"):
                        triaged["draft_reply"]["text"] = persisted["draft_text"]

                    results.append({
                        **t,
                        "status": status,
                        "triage": triaged
                    })
    return results

@app.post("/api/tickets/action")
def record_ticket_action(action: AdminActionRequest):
    """Persists admin moderation actions in SQLite so changes persist across page reloads."""
    save_admin_action(action.ticket_id, action.status, action.draft_text or "")
    return {
        "status": "success",
        "ticket_id": action.ticket_id,
        "action": action.status,
        "is_simulated": True,
        "message": "Action successfully recorded in local SQLite database (Simulation mode)."
    }

@app.get("/api/benchmark")
def get_benchmark():
    from app.benchmark import run_quick_benchmark
    return run_quick_benchmark()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT_BACKEND", 8005))
    uvicorn.run("app.server:app", host="127.0.0.1", port=port, reload=False)
