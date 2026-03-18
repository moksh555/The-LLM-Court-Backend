# ⚖️ The LLM Court — Backend

A multi-agent legal simulation engine that pits LLMs against each other in a structured courtroom proceeding. Given any case description, the backend orchestrates five sequential stages — opening statements, arguments, closing statements, jury deliberation, and a judge's final verdict — each powered by a different AI model via OpenRouter.

## How It Works

The courtroom unfolds in five pipeline stages:

1. **Stage 1 — Opening Statements**: Plaintiff (GPT model) and Defense (Grok model) present their opening arguments in parallel.
2. **Stage 2 — Arguments**: Each side responds to the other's opening with counterarguments, building on Stage 1 context.
3. **Stage 3 — Closing Statements**: Both sides deliver closing arguments informed by the full prior transcript.
4. **Stage 4 — Jury Deliberation**: Three independent LLMs (GPT-4o-mini, Gemini Flash, Mistral Devstral) deliberate in parallel and each return an independent verdict.
5. **Stage 5 — Judge's Verdict**: A final LLM (Grok) reviews the entire transcript plus jury opinions and delivers the authoritative ruling.

The system also supports a **real-time streaming endpoint** (`/court/case/stream`) via Server-Sent Events (SSE) so the frontend can display each stage as it completes.

## Key Features

- **5-stage courtroom pipeline** with distinct plaintiff, defense, jury, and judge roles
- **Multi-model parallelism** — jury deliberation queries three LLMs concurrently via `asyncio.gather`
- **SSE streaming** for live stage-by-stage updates to the client
- **JWT authentication** with httpOnly cookie sessions and Google OAuth support
- **Persistent chat history** stored in AWS DynamoDB with per-user access control
- **Dockerized deployment** with a GitHub Actions CI/CD workflow targeting AWS

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | FastAPI + Uvicorn |
| LLM Gateway | OpenRouter API (GPT, Grok, Gemini, Mistral) |
| HTTP Client | httpx (async) |
| Database | AWS DynamoDB |
| Auth | JWT (PyJWT) + Google OAuth 2.0 |
| Data Validation | Pydantic v2 + pydantic-settings |
| Packaging | uv + pyproject.toml |
| Container | Docker |
| CI/CD | GitHub Actions |

## Project Structure

```
src/app/
├── api/v1/routes/       # REST endpoints (court, auth, chats, user)
├── clients/             # OpenRouter async HTTP client
├── core/
│   ├── config.py        # Pydantic settings (env-driven)
│   └── prompts/         # Stage-specific system & user prompts (stage1–5)
├── schemas/court.py     # Pydantic request/response models
└── services/
    ├── court_service.py # 5-stage courtroom orchestration logic
    └── authentication/  # JWT + Google OAuth service layer
```

## Setup & Installation

**Prerequisites**: Python 3.12+, [uv](https://docs.astral.sh/uv/), AWS account with DynamoDB tables.

1. **Clone the repository**
   ```bash
   git clone https://github.com/moksh555/The-LLM-Court-Backend.git
   cd The-LLM-Court-Backend
   ```

2. **Install dependencies**
   ```bash
   uv sync --locked
   ```

3. **Configure environment** — create a `.env` file:
   ```env
   OPENROUTER_API_KEY=your_openrouter_key
   JWT_SECRET_KEY=your_jwt_secret
   JWT_ALGORITHM=HS256
   AWS_REGION=us-east-1
   USER_TABLE_NAME=LLM-COURT-USER
   CHAT_TABLE_NAME=LLM-COURT-USER-CHAT
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   GOOGLE_REDIRECT_URI=...
   GOOGLE_AUTH_URL=...
   GOOGLE_TOKEN_URL=...
   FRONTEND_URL=http://localhost:5173
   ```

4. **Run the server**
   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Or with Docker:
   ```bash
   docker build -t llm-court-backend .
   docker run -p 8000:8000 --env-file .env llm-court-backend
   ```

## API Endpoints

### Court
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/court/case` | Run a full 5-stage courtroom (returns complete transcript) |
| `POST` | `/api/v1/court/case/stream` | Run a courtroom with SSE streaming (stage-by-stage) |
| `GET` | `/api/v1/court/users/chat_history` | Get current user's case history list |
| `GET` | `/api/v1/court/chats/{chat_id}` | Get a saved case transcript by ID |
| `GET` | `/api/v1/court/user/information/me` | Get authenticated user's profile |

### Auth
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register with email + password |
| `POST` | `/api/v1/auth/login` | Login and receive httpOnly JWT cookie |
| `POST` | `/api/v1/auth/logout` | Clear session cookie |
| `GET` | `/api/v1/auth/google/login` | Initiate Google OAuth flow |
| `GET` | `/api/v1/auth/google/callback` | OAuth callback — sets session cookie |

### Example Request

```bash
curl -X POST http://localhost:8000/api/v1/court/case \
  -H "Content-Type: application/json" \
  -d '{"case": "A software company claims a former employee stole their source code."}'
```

The response includes `stage1` through `stage5` fields, each containing a `TranscriptMessage` with `role`, `model`, and the LLM-generated `content`.
