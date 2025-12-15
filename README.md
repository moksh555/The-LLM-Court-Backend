# LLM Court Backend

A FastAPI backend that runs a single user-provided “case” through a multi-stage LLM court workflow and returns a full transcript of intermediate outputs. The case can be a traditional dispute (business, workplace, consumer, etc.) or a proposition-style claim (policy, ethics, technology, society). The core goal is transparency: every stage emits its own structured output so you can inspect the reasoning trail, not just a final answer.

---

## Current Progress

This repository has progressed from an initial concept into a working, end-to-end staged pipeline with parallel LLM execution, consistent error handling, and a transcript-first response design.

### What’s working now

- Single-case execution per request: the API accepts one case per run and executes the complete workflow.
- Stage pipeline implemented: stages run in order and pass outputs forward as structured inputs for downstream reasoning.
- Parallel LLM calls: opposing sides are generated concurrently using `asyncio.gather` to reduce latency.
- Transcript-first design: each stage returns `TranscriptMessage` objects to expose all intermediate responses.
- OpenRouter integration: centralized `OpenRouterClient` using `httpx.AsyncClient` to call `/chat/completions`.
- Rate limit handling: automatic retries with exponential backoff and explicit `429` surfaced to the client.
- Configuration stabilized: Pydantic Settings + `.env` support for API keys, model selection, and service options.
- Clean project structure: separated modules for routes, services, schemas, clients, and config.

---

## Architecture Overview

### High-level flow

1. The user submits a case string.
2. The backend executes a staged workflow.
3. Each stage produces one or more transcript messages.
4. The final API response includes the full transcript so the client can render a timeline of reasoning.

### Key components

- **FastAPI**: request handling, validation, routing
- **Pydantic**: request/response schemas and settings management
- **OpenRouterClient**: OpenRouter API integration + retry/backoff
- **CourtService**: orchestration of stages + transcript creation
- **CaseStore** (in progress/being integrated): persistence layer for saving and replaying case runs

---

## Pipeline Stages

### Stage 1: Opening Statements (Plaintiff vs Defense)

- Generates the Plaintiff (Affirmative) opening statement based on the case.
- Generates the Defense (Negative) opening statement based on the same case.
- Runs both model calls in parallel and returns two transcript messages.

### Stage 2: Argument Extraction and Structuring

- Reads both Stage 1 opening statements.
- Extracts main claims, assumptions, and supporting reasoning for each side.
- Produces structured arguments that are easier to reuse reliably in downstream stages.

### Stage 3: Closing Statements (Plaintiff vs Defense)

- Uses the original case plus structured arguments from Stage 2.
- Produces closing statements that respond to the opponent’s strongest points.
- Runs both model calls in parallel and returns two transcript messages.

### Stage 4: Jury Review and Scoring

- Sends the case and prior-stage arguments to a panel of “jury” models.
- Each juror evaluates both sides for clarity, logical consistency, and persuasiveness.
- Returns per-juror scoring and short written justification (vote + reasoning).

### Stage 5: Judge Synthesis and Final Decision

- Aggregates jury feedback and identifies the strongest reasoning on each side.
- Produces a final decision and rationale.
- Outputs a final summary plus the key factors that drove the verdict.

---

## API

### Run a case

`POST /api/v1/case/run`

**Request body**

```json
{
  "case": "Artificial Intelligence is good for humanity."
}
```
