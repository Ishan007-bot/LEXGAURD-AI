# LexGuard

> **AI Rights Contract Intelligence System** — an adversarial multi-agent AI platform that analyzes contracts, offer letters, quotations, ticket terms, and online policies to detect exploitative clauses, hidden liabilities, legal ambiguities, and real-world risks **before users agree to them**.

[![CI](https://github.com/OWNER/lexguard/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/lexguard/actions/workflows/ci.yml)
[![Deploy](https://github.com/OWNER/lexguard/actions/workflows/deploy.yml/badge.svg)](https://github.com/OWNER/lexguard/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Why LexGuard

People sign contracts they don't understand every day — offer letters with unenforceable non-competes, SaaS terms that auto-renew, ticket conditions that waive liability, privacy policies that quietly sell their data. LexGuard reads the document, **argues both sides** through specialized agents, and hands the user a risk score, plain-English summary, and concrete redlines.

## Problem-statement alignment

| Problem statement requirement | How LexGuard satisfies it |
| --- | --- |
| **Adversarial multi-agent AI** | 5-agent LangGraph state machine: Extractor → Prosecutor ⇄ Defender → Judge → Negotiator. The Prosecutor and Defender literally argue opposing positions per clause. |
| **Analyze contracts, offer letters, quotations, ticket terms, online policies** | Unified pipeline accepts PDF, DOCX, plain text, or a URL (live T&C scraping). Document type is auto-classified. |
| **Exploitative clauses** | Prosecutor agent specifically hunts asymmetric obligations, hidden fees, unilateral powers, and predatory defaults. |
| **Hidden liabilities** | Clause classifier tags `liability`, `indemnity`, `limitation_of_liability`; severity scored by Judge. |
| **Legal ambiguities** | Vague-language detector + Gemini grounding flags undefined terms, "sole discretion" patterns, and conflicting clauses. |
| **Real-world risks** | "What-If" simulator runs scenarios (miss a payment, quit early, policy change) and explains consequences clause-by-clause. |
| **Before users agree** | Pre-signature workflow: upload → analyze → review → export annotated report. No post-signing audit framing. |

## Architecture

```
                        ┌──────────────────────────────────┐
                        │   Next.js 14 (Cloud Run)         │
                        │   + Firebase Auth                │
                        └──────────────┬───────────────────┘
                                       │ HTTPS / SSE
                        ┌──────────────▼───────────────────┐
                        │   FastAPI (Cloud Run)            │
                        │   - Upload / ingest              │
                        │   - DLP redaction                │
                        │   - LangGraph orchestrator       │
                        └──┬──────────┬──────────┬─────────┘
                           │          │          │
              ┌────────────▼──┐  ┌────▼─────┐  ┌─▼──────────┐
              │  Vertex AI    │  │ Firestore│  │ Document AI│
              │  Gemini 2.5   │  │          │  │            │
              └───────────────┘  └──────────┘  └────────────┘
                    │                    │
        ┌───────────▼─────────┐  ┌───────▼──────┐
        │ Cloud DLP (PII)     │  │ Cloud Storage│
        └─────────────────────┘  └──────────────┘
```

### Adversarial agent flow

1. **Extractor** — segments document into atomic clauses, classifies each by category.
2. **Prosecutor** — assumes the counterparty is hostile; flags exploitation, asymmetry, hidden cost.
3. **Defender** — argues the clause is standard; cites industry norms.
4. **Judge** — weighs both, assigns a 0–100 risk score and Critical/High/Medium/Low/Info severity.
5. **Negotiator** — produces concrete redline text + plain-English explanation.

## Google Cloud services used

| Service | Purpose |
| --- | --- |
| **Vertex AI (Gemini 2.5 Pro / Flash)** | Agent reasoning, structured outputs, Google Search grounding for legal citations |
| **Cloud Run** | Stateless hosting for both API and web |
| **Document AI** | OCR + layout extraction for PDFs and scans |
| **Cloud DLP** | PII redaction before any prompt leaves the VPC |
| **Firestore** | Document metadata, analyses, user history (also doubles as a persistent cache to keep costs down) |
| **Cloud Storage** | Original document uploads, generated PDF reports |
| **Firebase Authentication** | Google sign-in |
| **Secret Manager** | API keys, service account credentials |
| **Cloud Build + Artifact Registry** | CI/CD images |
| **Cloud Logging / Trace / Error Reporting** | Observability |
| **Cloud Text-to-Speech** | Voice walkthrough of every verdict (accessibility) |

## Repository layout

```
.
├── apps/
│   ├── api/                FastAPI + LangGraph (Python 3.12)
│   └── web/                Next.js 14 + Tailwind + shadcn primitives (TS)
├── packages/
│   └── shared/             Shared TypeScript types
├── infra/
│   ├── docker/             Reserved for additional images
│   └── gcp/                setup.sh / setup.ps1, cloudbuild.yaml
├── examples/               Sample contracts for the demo
├── docs/                   Architecture diagrams, agent prompts, ADRs
└── .github/workflows/      CI + deploy pipelines
```

## Local development

### Prerequisites

- Node 20+, pnpm 9+
- Python 3.12
- Docker (optional, for parity with prod)
- `gcloud` CLI authenticated to a project with billing

### One-time setup

```powershell
# Windows PowerShell
$env:PROJECT_ID = "your-gcp-project"
$env:REGION     = "asia-south1"
infra\gcp\setup.ps1
```

```bash
# bash
PROJECT_ID=your-gcp-project REGION=asia-south1 bash infra/gcp/setup.sh
```

Copy `.env.example` to `.env` and fill in values from the script's output.

### Run

```bash
# Backend
cd apps/api
python -m venv .venv && .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd apps/web
pnpm install
pnpm dev
```

Visit http://localhost:3000.

## Quality gates

| Gate | Tool | Threshold |
| --- | --- | --- |
| Python lint | Ruff | 0 errors |
| Python types | Mypy strict | 0 errors |
| Python SAST | Bandit | 0 high |
| Python coverage | Pytest + coverage | ≥ 80 % |
| TS lint | ESLint (+ jsx-a11y) | 0 errors / 0 warnings |
| TS types | `tsc --noEmit` | 0 errors |
| TS coverage | Vitest v8 | ≥ 70 % |
| Secrets | Gitleaks | 0 findings |
| Dependencies | Dependabot + dependency-review | no high-severity |
| Format | Prettier | clean |

All gates run on every push and pull request via [.github/workflows/ci.yml](.github/workflows/ci.yml).

## Accessibility

- Skip-to-content link, semantic landmarks, ARIA labels, visible focus rings.
- WCAG AA color contrast verified.
- `eslint-plugin-jsx-a11y` enforced in CI.
- `@axe-core/react` integrated in dev.
- Cloud Text-to-Speech generates an audio walkthrough of every analysis.

## Security

- All traffic HTTPS-only (Cloud Run default).
- HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Permissions-Policy set on every response.
- Non-root containers; least-privilege service account.
- Secrets via Secret Manager, never in source.
- DLP redacts PII before prompts hit Vertex AI.
- Bandit, Gitleaks, dependency-review in CI.

See [SECURITY.md](SECURITY.md) for the disclosure policy.

## License

MIT — see [LICENSE](LICENSE).

## Disclaimer

LexGuard provides informational analysis only. It is **not** legal advice and does not create an attorney-client relationship. For binding decisions, consult a qualified lawyer.
