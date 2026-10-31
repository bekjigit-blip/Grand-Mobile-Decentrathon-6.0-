import argparse
import json
import os
import sys
import time
from typing import Dict, Any

from app.triage_service import get_triage_service

LEAK_FIELDS = {
    'verdict', 'punishment', 'violation', 'status', 'admin_reply',
    'admin_messages', 'moderator', 'resolution', 'label', 'ground_truth'
}

def sanitize_input_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Scrubs any potential ground-truth or admin leak fields from ticket before prediction."""
    clean = {k: v for k, v in record.items() if k not in LEAK_FIELDS}
    if "messages" in clean and isinstance(clean["messages"], list):
        clean["messages"] = [
            m for m in clean["messages"]
            if isinstance(m, dict) and str(m.get("role", "")).lower() not in {"admin", "system", "moderator"}
        ]
    return clean

sanitize_input_ticket = sanitize_input_record

def run_batch_prediction(input_path: str, output_path: str) -> Dict[str, Any]:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    triage_service = get_triage_service()
    total_count = 0
    success_count = 0
    error_count = 0

    start_time = time.time()

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(input_path, "r", encoding="utf-8") as in_f, \
         open(output_path, "w", encoding="utf-8") as out_f:

        for line_num, line in enumerate(in_f, 1):
            total_count += 1
            line = line.strip()
            if not line:
                fallback_record = {
                    "lang": "ru",
                    "category": "question.help",
                    "priority": "p3",
                    "is_spam_or_duplicate": False,
                    "extracted": {"nickname": None, "rule_refs": [], "has_evidence": False, "server": None},
                    "draft_reply": {"lang": "ru", "text": "Здравствуйте! Чем мы можем вам помочь?", "cited": []},
                    "needs_human": False,
                    "confidence": 0.0,
                    "reasons": ["Пустая строка во входном файле"]
                }
                out_f.write(json.dumps(fallback_record, ensure_ascii=False) + "\n")
                continue

            try:
                raw_record = json.loads(line)
                clean_record = sanitize_input_record(raw_record)
                result = triage_service.triage_ticket(clean_record)

                out_record = {
                    "lang": result["lang"],
                    "category": result["category"],
                    "priority": result["priority"],
                    "is_spam_or_duplicate": result["is_spam_or_duplicate"],
                    "extracted": result["extracted"],
                    "draft_reply": result["draft_reply"],
                    "needs_human": result["needs_human"],
                    "confidence": result["confidence"],
                    "reasons": result["reasons"]
                }
                if "ticket_id" in clean_record:
                    out_record["ticket_id"] = clean_record["ticket_id"]

                out_f.write(json.dumps(out_record, ensure_ascii=False) + "\n")
                success_count += 1
            except Exception as e:
                error_count += 1
                fallback_record = {
                    "lang": "ru",
                    "category": "feedback.other",
                    "priority": "p3",
                    "is_spam_or_duplicate": False,
                    "extracted": {"nickname": None, "rule_refs": [], "has_evidence": False, "server": None},
                    "draft_reply": {"lang": "ru", "text": "Здравствуйте! Ваше обращение принято к рассмотрению.", "cited": []},
                    "needs_human": True,
                    "confidence": 0.0,
                    "reasons": [f"Ошибка парсинга строки #{line_num}: {str(e)}"]
                }
                out_f.write(json.dumps(fallback_record, ensure_ascii=False) + "\n")

    elapsed = time.time() - start_time
    throughput = (total_count / elapsed) if elapsed > 0 else total_count

    stats = {
        "total": total_count,
        "success": success_count,
        "errors": error_count,
        "elapsed_seconds": round(elapsed, 4),
        "tickets_per_sec": round(throughput, 1)
    }

    print(f"Batch prediction complete: {success_count}/{total_count} processed in {elapsed:.3f}s ({throughput:.1f} tickets/sec)")
    return stats

def main():
    parser = argparse.ArgumentParser(description="Grand Mobile Support Copilot Batch Prediction")
    parser.add_argument("--input", "-i", type=str, default="data/valid.jsonl", help="Input tickets JSONL file path")
    parser.add_argument("--output", "-o", type=str, default="pred.jsonl", help="Output predictions JSONL file path")
    args = parser.parse_args()

    run_batch_prediction(args.input, args.output)

if __name__ == "__main__":
    main()
