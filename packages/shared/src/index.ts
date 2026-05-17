/**
 * Shared types used by both the LexGuard API and web client.
 * Keep these in sync with the Pydantic models in apps/api/app/schemas/.
 */

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';

export type DocumentType =
  | 'contract'
  | 'offer_letter'
  | 'quotation'
  | 'ticket_terms'
  | 'privacy_policy'
  | 'terms_of_service'
  | 'other';

export type ClauseCategory =
  | 'liability'
  | 'indemnity'
  | 'termination'
  | 'payment'
  | 'ip_assignment'
  | 'non_compete'
  | 'non_solicit'
  | 'arbitration'
  | 'jurisdiction'
  | 'data_privacy'
  | 'confidentiality'
  | 'auto_renewal'
  | 'limitation_of_liability'
  | 'force_majeure'
  | 'other';

export interface Clause {
  id: string;
  text: string;
  category: ClauseCategory;
  startOffset: number;
  endOffset: number;
}

export interface AgentTurn {
  agent: 'prosecutor' | 'defender' | 'judge' | 'negotiator';
  argument: string;
  citations?: string[];
}

export interface ClauseAnalysis {
  clauseId: string;
  severity: Severity;
  riskScore: number;
  plainEnglish: string;
  debate: AgentTurn[];
  suggestedRedline?: string;
  citations: string[];
}

export interface DocumentAnalysis {
  id: string;
  documentId: string;
  documentType: DocumentType;
  overallRiskScore: number;
  summary: string;
  clauses: ClauseAnalysis[];
  createdAt: string;
}
