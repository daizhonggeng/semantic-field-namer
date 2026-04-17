# Contributing

## Scope

This project is a field naming tool for schema import, semantic reuse, and LLM fallback. Good contributions usually improve one of these areas:

- Import quality and SQL/JSON parsing
- Mapping pool accuracy and explainability
- SQL export and database dialect handling
- Developer experience, docs, tests, and packaging

## Before you open a PR

1. Open or reference an issue for non-trivial work
2. Keep the change focused; avoid bundling unrelated refactors
3. Add or update tests when behavior changes
4. Update docs when user-facing behavior changes

## Local development

### Backend

```powershell
cd backend
Copy-Item .env.example .env
python -m pip install -r requirements.txt
python -m pytest -q
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run build
npm run dev
```

### Optional Qdrant

```powershell
docker compose up -d
```

## Pull request checklist

- The change is scoped and documented
- Tests pass locally
- Build passes locally
- New config or env vars are added to `.env.example`
- Breaking behavior is called out explicitly in the PR description
