# Security Policy

## Supported versions

LexGuard is currently in active hackathon development; the `main` branch is the only supported version.

## Reporting a vulnerability

If you discover a security vulnerability, please **do not** open a public issue. Instead, email the maintainers at `security@lexguard.invalid` with:

- A description of the issue and its impact.
- Steps to reproduce.
- Affected component (API, web, infra).
- Any suggested mitigation.

We will acknowledge receipt within 72 hours and aim to provide a remediation timeline within 7 days.

## Security controls in place

- All traffic over HTTPS (TLS 1.2+).
- HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Permissions-Policy enforced.
- Non-root container users (`uid 1001`).
- Least-privilege GCP service account (`lexguard-runner`).
- Secrets via Google Secret Manager — never in source control.
- Cloud DLP redacts PII before any prompt is sent to Vertex AI.
- Static analysis: Ruff, Bandit, ESLint, gitleaks on every push.
- Dependency scanning: Dependabot + GitHub dependency-review.
- Coverage gates (≥80% backend, ≥70% frontend) enforced in CI.

## Out of scope

- Issues that require physical access to a user's device.
- Findings in third-party services we depend on (report to the upstream vendor).
- Self-XSS or social-engineering attacks.
