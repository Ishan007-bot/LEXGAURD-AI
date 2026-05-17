# Contributing to LexGuard

## Branch / commit

- Branch from `main`: `feature/<short-slug>`, `fix/<short-slug>`, `chore/<short-slug>`.
- Commit messages follow Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`.

## Before opening a PR

```bash
# from repo root
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
( cd apps/api && ruff check . && ruff format --check . && mypy app && bandit -r app -c pyproject.toml && pytest )
```

## Pre-commit

Install once:

```bash
pip install pre-commit
pre-commit install
```

It will auto-run Ruff, Bandit, Prettier, and Gitleaks on every commit.

## CI must be green

All checks in `.github/workflows/ci.yml` must pass before merge.
