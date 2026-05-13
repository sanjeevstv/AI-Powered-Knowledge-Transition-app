export type UserPublic = {
  id: number;
  email: string;
  full_name: string;
  role: string;
};

/** GET /auth/me — includes UI access from data/role_config.json (API). */
export type Me = UserPublic & {
  config_role: string | null;
  ui_access: "full" | "limited";
};

export type DashboardSummary = {
  kt_completion_percent: number;
  pending_sessions: number;
  completed_sessions: number;
  total_sessions: number;
  assessment_avg_score: number;
  assessment_count: number;
  document_coverage_percent: number;
  documents_uploaded: number;
  expected_documents: number;
  question_resolution_rate_percent: number;
  readiness_score: number;
  open_risks_placeholder: string;
};

export type CriterionCheck = {
  name: string;
  met: boolean;
  detail: string;
};

export type ClosureReport = {
  dashboard: DashboardSummary;
  checklist: CriterionCheck[];
  narrative: string;
  all_criteria_met: boolean;
};

export type KTSession = {
  id: number;
  external_id: string;
  topic: string;
  owner_id: number | null;
  scheduled_date: string;
  status: string;
  transcript_text: string;
  summary_text: string;
  key_decisions: string;
  risks: string;
  missing_knowledge_notes: string;
};

export type ActionItem = { id: number; text: string; is_done: boolean };
export type FAQItem = { id: number; question: string; answer: string };

export type KTSessionDetail = KTSession & {
  action_items: ActionItem[];
  faq_items: FAQItem[];
};

export type DocumentRow = {
  id: number;
  filename: string;
  mime_type: string;
  tags: string;
  created_at: string;
};

export type SemanticHit = { snippet: string; metadata: Record<string, unknown> };
