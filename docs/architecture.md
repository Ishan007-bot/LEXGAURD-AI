# LexGuard Architecture

## High-level

```
User → Next.js (Cloud Run) → FastAPI (Cloud Run) → LangGraph orchestrator → Vertex AI Gemini
                                  │
                                  ├── Document AI (OCR / layout)
                                  ├── Cloud DLP (PII redaction)
                                  ├── Firestore (state + cache hits)
                                  └── Cloud Storage (uploads, reports)

Caching: in-process `cachetools.TTLCache` per Cloud Run instance, with Firestore
as the durable layer. Memorystore was intentionally dropped — see docs/budget.md.
```

## Agent graph (LangGraph)

```
        ┌─────────────┐
        │  Extractor  │  segments document → clauses
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │ per-clause  │  fan-out (asyncio.gather, bounded)
        └──────┬──────┘
               │
   ┌───────────┴───────────┐
   │                       │
┌──▼──────────┐     ┌──────▼──────┐
│ Prosecutor  │     │  Defender   │
└──────┬──────┘     └──────┬──────┘
       └──────────┬────────┘
                  │
            ┌─────▼─────┐
            │   Judge   │  risk score + severity
            └─────┬─────┘
                  │
           ┌──────▼──────┐
           │ Negotiator  │  redline + plain English
           └─────────────┘
```

## Data model (Firestore)

```
documents/{docId}
  - userId
  - filename
  - sizeBytes
  - mimeType
  - documentType
  - gcsPath
  - createdAt

analyses/{analysisId}
  - documentId
  - userId
  - overallRiskScore
  - summary
  - clauses: [
      { id, text, category, severity, riskScore, plainEnglish,
        debate: [{ agent, argument, citations }], suggestedRedline }
    ]
  - createdAt
```

## Why this stack

- **FastAPI** — first-class async, automatic OpenAPI, fits Pydantic-driven structured outputs.
- **LangGraph** — explicit state machine; debate flow is obvious; easy to inspect transitions.
- **Vertex AI Gemini 2.5** — long context, native structured outputs, Google Search grounding for legal citations.
- **Next.js 14 (standalone)** — small Docker image, RSC for fast pages, App Router for streaming UI.
- **Cloud Run** — scale-to-zero, no infrastructure to babysit, native to GitHub Actions deploys.
