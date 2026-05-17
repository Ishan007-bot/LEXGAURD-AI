/**
 * Typed fetch wrapper for the LexGuard API.
 * Attaches a Firebase ID token (when available) and normalises the error envelope
 * returned by `app/exceptions.py`.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export interface ApiErrorBody {
  error: { code: string; message: string; requestId?: string; details?: unknown };
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId?: string;
  readonly details?: unknown;

  constructor(status: number, body: ApiErrorBody) {
    super(body.error?.message ?? `Request failed with status ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.code = body.error?.code ?? 'unknown';
    this.requestId = body.error?.requestId;
    this.details = body.error?.details;
  }
}

export interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  token?: string | null;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { token, body, headers, ...rest } = options;
  const init: RequestInit = {
    ...rest,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(headers ?? {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  };

  const response = await fetch(`${API_BASE}${path}`, init);
  const contentType = response.headers.get('content-type') ?? '';
  const payload = contentType.includes('application/json') ? await response.json() : null;

  if (!response.ok) {
    throw new ApiError(
      response.status,
      (payload as ApiErrorBody) ?? { error: { code: 'http', message: response.statusText } },
    );
  }
  return payload as T;
}

// ---------- types ------------------------------------------------------------

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';

export type DocumentStatus = 'pending' | 'processing' | 'ready' | 'failed';
export type AnalysisStatus = 'pending' | 'running' | 'ready' | 'failed';
export type DocumentSource = 'upload' | 'pasted_text' | 'url';

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

export type DocumentType =
  | 'contract'
  | 'offer_letter'
  | 'quotation'
  | 'ticket_terms'
  | 'privacy_policy'
  | 'terms_of_service'
  | 'other';

export type AgentName = 'extractor' | 'prosecutor' | 'defender' | 'judge' | 'negotiator';

export interface ClauseDTO {
  id: string;
  index: number;
  text: string;
  category: ClauseCategory;
  start_offset: number;
  end_offset: number;
}

export interface DocumentDTO {
  id: string;
  user_id: string;
  source: DocumentSource;
  status: DocumentStatus;
  document_type: DocumentType;
  filename: string | null;
  content_type: string | null;
  size_bytes: number | null;
  source_url: string | null;
  clause_count: number;
  failure_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentWithClausesDTO extends DocumentDTO {
  clauses: ClauseDTO[];
}

export interface AgentTurnDTO {
  agent: AgentName;
  argument: string;
  citations: string[];
}

export interface ClauseAnalysisDTO {
  clause_id: string;
  severity: Severity;
  risk_score: number;
  plain_english: string;
  debate: AgentTurnDTO[];
  suggested_redline: string | null;
  citations: string[];
}

export interface DocumentAnalysisDTO {
  id: string;
  document_id: string;
  user_id: string;
  status: AnalysisStatus;
  overall_risk_score: number;
  summary: string;
  clauses: ClauseAnalysisDTO[];
  failure_reason: string | null;
  created_at: string;
  updated_at: string;
}

// ---------- endpoints --------------------------------------------------------

export interface UploadInitResponse {
  document_id: string;
  upload_url: string;
  method: 'PUT';
  headers: Record<string, string>;
  expires_in_seconds: number;
  gcs_object: string;
}

export const api = {
  initUpload(
    payload: { filename: string; content_type: string; size_bytes: number },
    token: string,
  ): Promise<UploadInitResponse> {
    return request('/uploads/init', { method: 'POST', body: payload, token });
  },

  createFromUpload(
    payload: {
      document_id: string;
      gcs_object: string;
      filename: string;
      content_type: string;
      size_bytes: number;
    },
    token: string,
  ): Promise<DocumentWithClausesDTO> {
    return request('/documents/from-upload', { method: 'POST', body: payload, token });
  },

  createFromText(
    payload: { text: string; document_type?: DocumentType; title?: string },
    token: string,
  ): Promise<DocumentWithClausesDTO> {
    return request('/documents/from-text', { method: 'POST', body: payload, token });
  },

  createFromUrl(
    payload: { url: string; document_type?: DocumentType },
    token: string,
  ): Promise<DocumentWithClausesDTO> {
    return request('/documents/from-url', { method: 'POST', body: payload, token });
  },

  getDocument(id: string, token: string): Promise<DocumentWithClausesDTO> {
    return request(`/documents/${encodeURIComponent(id)}`, { token });
  },

  listDocuments(token: string): Promise<{ items: DocumentDTO[]; next_cursor: string | null }> {
    return request('/documents', { token });
  },

  createAnalysis(documentId: string, token: string): Promise<DocumentAnalysisDTO> {
    return request(`/documents/${encodeURIComponent(documentId)}/analyses`, {
      method: 'POST',
      token,
    });
  },

  getAnalysis(id: string, token: string): Promise<DocumentAnalysisDTO> {
    return request(`/analyses/${encodeURIComponent(id)}`, { token });
  },

  simulate(
    analysisId: string,
    scenario: string,
    token: string,
  ): Promise<SimulateResponse> {
    return request(`/analyses/${encodeURIComponent(analysisId)}/simulate`, {
      method: 'POST',
      body: { scenario },
      token,
    });
  },

  tts(analysisId: string, token: string): Promise<TtsResponse> {
    return request(`/analyses/${encodeURIComponent(analysisId)}/tts`, {
      method: 'POST',
      token,
    });
  },
};

export interface SimulateResponse {
  headline: string;
  consequences: string[];
  severity: Severity;
  advice: string;
}

export interface TtsResponse {
  audio_base64: string;
  mime_type: string;
  voice: string;
  char_count: number;
}
