export interface EventLink {
  url: string;
  title?: string;
  source_name?: string;
}

export interface CandidateProfile {
  candidate_id: string;
  hit_id: string;
  entity_name: string;
  risk_category: string;
  country: string;
  description: string;
  total_events: number;
  events: EventLink[];
}

export interface ScrapingStats {
  total_links: number;
  successful_scrapes: number;
  failed_scrapes: number;
}

export interface SummaryResponse {
  candidate_id: string;
  hit_id: string;
  entity_name: string;
  stats: ScrapingStats;
  summary_report: string;
  created_at: string;
}

