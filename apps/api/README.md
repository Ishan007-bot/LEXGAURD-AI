# LexGuard API

FastAPI backend hosting the adversarial multi-agent contract analysis pipeline.

## Local development

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

OpenAPI docs at http://localhost:8000/docs.

## Tests

```bash
pytest
```

Coverage gate: 80% (configured in `pyproject.toml`).

## Lint / format / types / security

```bash
ruff check .
ruff format .
mypy app
bandit -r app
```
