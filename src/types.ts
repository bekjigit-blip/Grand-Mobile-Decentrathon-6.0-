export interface ExtractedData {
  nickname: string | null;
  rule_refs: string[];
  has_evidence: boolean;
  server: string | null;
}

export interface DraftReply {
  lang: string;
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
  lang: string;
  category: string;
  priority: 'p0' | 'p1' | 'p2' | 'p3';
  is_spam_or_duplicate: boolean;
  extracted: ExtractedData;
  draft_reply: DraftReply;
  needs_human: boolean;
  confidence: number;
  reasons: string[];
  ticket_id?: string;
  matched_rules?: MatchedRule[];
}

export interface TicketMessage {
  role: 'player' | 'reported_player' | 'admin' | 'system' | string;
  text: string;
  attachments?: number | any[];
}

export interface TicketItem {
  ticket_id: string;
  kind?: string;
  messages?: TicketMessage[];
  reporter_hash?: string;
  created_at?: string;
  server_lang?: string;
  lang?: string;
  text?: string;
  images_count?: number;
  rule_refs_raw?: string | string[];
  status?: 'pending' | 'approved' | 'escalated' | 'clarification' | 'rejected';
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
    gold_labels_available: boolean;
    note?: string;
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
    citation_relevance_percent: number;
    total_citations_analyzed: number;
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
