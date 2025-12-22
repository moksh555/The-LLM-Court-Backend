# LLM Court

## Link: https://www.llm-court.com/

LLM Court is a FastAPI backend that runs a single user-provided case through a staged courtroom-style workflow powered by multiple LLMs via OpenRouter. Instead of returning one opaque response, it produces a complete stage-by-stage transcript including opening statements, structured arguments, closing statements, jury deliberations and voting, and a final judge decision that summarizes the majority verdict and the most common reasons cited by jurors.

A “case” in this project is a proposition style claim a single statement that can be argued for or against. It can target ethics, public policy, technology, society, or even a new research idea (e.g., “LLMs should be allowed to author academic papers,” or “We should regulate model training data like we regulate food ingredients.”).

## Motivation
Modern LLMs are powerful, but they’re also confident storytellers. A single model can hallucinate facts, ignore counterarguments, or get stuck in one narrative and never self-correct.

The motivation for this project comes from the general LLM Council idea: don’t rely on one model’s “final answer,” instead run multiple independent thinkers, then add an explicit evaluation layer. The key move is introducing a Jury separate models whose job is not to argue, but to judge the arguments: identify gaps, call out unsupported claims, weigh which side was more convincing, and explain why.

Finally, a Judge (the aggregator) takes the jury deliberations and produces the final output:

* extracts each juror’s verdict and reasoning
* determines the majority decision
* summarizes the most common reasons cited by the jury for the winning side
* highlights the strongest criticisms the jury raised about both sides
* delivers a clear, readable ruling that’s grounded in the jury’s actual evaluations (not new invented reasoning)

This structure reduces hallucination risk by forcing the system to pass through multiple perspectives + explicit critique + majority-based consolidation, rather than trusting a single model to be both the debater and the referee.

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
   Both sides generate closings using the original case and Stage 1 and Stage 2 arguments.

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

---


## Next Big Update
* Per-role model selection: Add a configurable model picker for each courtroom role (Plaintiff, Defense, Jury, Judge) so users can mix-and-match OpenRouter models per stage and compare outcomes.
* Google OAuth authentication: Implement Google login and registration (OAuth 2.0) to support secure sign-in, session management, and user accounts without password handling.
