export interface ExtractedData {
  nicknames: string[];
  rule_refs_raw: string[];
  ids: string[];
  has_attachments: boolean;
}

export interface DraftReply {
  text: string;
  cited: string[];
}

export interface MatchedRule {
  section_id: string;
  section_name: string;
  ref: string;
  is_rp_term?: boolean;
  internal_key: string;
  text: string;
  score: number;
}

export interface TriageResult {
  ticket_id?: string;
  lang: string;
  category: string;
  priority: 'p0' | 'p1' | 'p2' | 'p3';
  is_spam_or_duplicate: boolean;
  extracted: ExtractedData;
  draft_reply: DraftReply;
  needs_human: boolean;
  confidence: number;
  reasons: string[];
  matched_rules?: MatchedRule[];
}

export interface TicketItem {
  ticket_id: string;
  reporter_hash?: string;
  created_at?: string;
  server_lang?: string;
  lang?: string;
  text: string;
  images_count?: number;
  rule_refs_raw?: string[];
  status?: 'pending' | 'approved' | 'escalated' | 'clarification' | 'rejected';
  admin_notes?: string;
  triage?: TriageResult;
}

export interface BenchmarkMetrics {
  status: string;
  benchmark_environment: {
    platform: string;
    cpu_only: boolean;
    external_api_calls: number;
    external_api_cost_usd: number;
    offline_mode: boolean;
  };
  index_metrics: {
    build_duration_seconds: number;
    rules_index_size_kb: number;
    taxonomy_index_size_kb: number;
    total_disk_footprint_kb: number;
    process_ram_mb: number;
  };
  latency_metrics: {
    mean_ms: number;
    p50_ms: number;
    p90_ms: number;
    p95_ms: number;
    p99_ms: number;
    target_threshold_p95_sec: number;
    meets_target: boolean;
  };
  operational_metrics: {
    total_sample_tickets: number;
    needs_human_escalation_rate_percent: number;
    citation_validity_percent: number;
  };
  multilingual_examples: {
    kazakh: Array<{
      ticket_text: string;
      category: string;
      priority: string;
      cited: string[];
      draft_reply: string;
    }>;
    uzbek: Array<{
      ticket_text: string;
      category: string;
      priority: string;
      cited: string[];
      draft_reply: string;
    }>;
  };
}
