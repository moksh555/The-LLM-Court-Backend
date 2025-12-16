# LLM Court

![llmcourt](header.jpg)

LLM Court is a transcript-first FastAPI backend that runs a single user-provided “case” through a staged courtroom-style workflow powered by multiple LLMs via OpenRouter. Instead of getting one opaque answer, you get a full timeline of intermediate outputs (openings, structured arguments, closings, jury review, and a final judge decision).

A “case” can be a real-world dispute (business, workplace, consumer, contracts, etc.) or a proposition-style claim (ethics, policy, technology, society).

---

## How It Works

When you submit a case, the backend executes a multi-stage pipeline and returns a transcript containing every stage’s output.

1. **Stage 1: Opening Statements**  
   The case is given to two models acting as opposing counsel.

   - Plaintiff (Affirmative) produces an opening statement.
   - Defense (Negative) produces an opening statement.  
     Both are generated in parallel using `asyncio.gather`.

2. **Stage 2: Argument Structuring**  
   Stage 1 outputs are parsed into reusable argument structure.

   - Extracts the main claims, assumptions, and reasoning from each side.
   - Produces structured arguments so later stages can respond consistently.

3. **Stage 3: Closing Statements**  
   Both sides generate closings using the original case and Stage 2 arguments.

   - Each side responds to the other’s strongest points.
   - Both closings run in parallel.

4. **Stage 4: Jury Review and Scoring**  
   A panel of jury models reviews the arguments.

   - Jurors score and justify which side is stronger.
   - Outputs include per-juror votes and brief reasoning.

5. **Stage 5: Judge Decision**  
   A judge model synthesizes the overall outcome.
   - Aggregates jury feedback.
   - Produces a final verdict and rationale.
