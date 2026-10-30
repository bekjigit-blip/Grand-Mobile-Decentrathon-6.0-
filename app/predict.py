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

def sanitize_input_ticket(ticket: Dict[str, Any]) -> Dict[str, Any]:
    """Removes potential admin/status data leakage fields from the input ticket."""
    return {k: v for k, v in ticket.items() if k not in LEAK_FIELDS}

def run_batch_prediction(input_path: str, output_path: str) -> Dict[str, Any]:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    triage_service = get_triage_service()
    total_count = 0
    success_count = 0
    error_count = 0

    start_time = time.time()

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(input_path, "r", encoding="utf-8") as in_f, \
         open(output_path, "w", encoding="utf-8") as out_f:

        for line_num, line in enumerate(in_f, 1):
            total_count += 1
            line = line.strip()
            if not line:
                # Output fallback for empty line to maintain strict 1:1 row count
                fallback_record = {
                    "lang": "ru",
                    "category": "in_game_help",
                    "priority": "p3",
                    "is_spam_or_duplicate": False,
                    "extracted": {"nicknames": [], "rule_refs_raw": [], "ids": [], "has_attachments": False},
                    "draft_reply": {"text": "Здравствуйте! Чем мы можем вам помочь?", "cited": []},
                    "needs_human": False,
                    "confidence": 0.0,
                    "reasons": ["Пустая строка во входном файле"]
                }
                out_f.write(json.dumps(fallback_record, ensure_ascii=False) + "\n")
                continue

            try:
                ticket_data = json.loads(line)
                clean_ticket = sanitize_input_ticket(ticket_data)
                result = triage_service.triage_ticket(clean_ticket)

                # Format exact Decentrathon 6.0 output specification
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
                if "ticket_id" in clean_ticket:
                    out_record["ticket_id"] = clean_ticket["ticket_id"]

                out_f.write(json.dumps(out_record, ensure_ascii=False) + "\n")
                success_count += 1
            except Exception as e:
                error_count += 1
                # Fault tolerance: single malformed record must not crash the batch!
                fallback_record = {
                    "lang": "ru",
                    "category": "other_feedback",
                    "priority": "p3",
                    "is_spam_or_duplicate": False,
                    "extracted": {"nicknames": [], "rule_refs_raw": [], "ids": [], "has_attachments": False},
                    "draft_reply": {"text": "Здравствуйте! Ваше обращение принято к рассмотрению.", "cited": []},
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
