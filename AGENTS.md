# AGENTS.md

Behavioral guidelines to reduce common LLM coding mistakes in Codex. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" -> "Write tests for invalid inputs, then make them pass"
- "Fix the bug" -> "Write a test that reproduces it, then make it pass"
- "Refactor X" -> "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## 5. Active Project Scope

The active project is now **SPY 0DTE - Higanbana**.

- BTC/Bybit runtime files were removed from this project folder. Do not recreate them unless the user explicitly asks.
- Do not implement IBKR order transmission until research acceptance gates pass.
- Use the local LLM Wiki at `D:\Fogust\Workspace\LLM Wiki\LLM Wiki\wiki` as the primary knowledge source for 0DTE research rationale and report citations.
- IBKR options permission is pending, so paper trading may be used as an operational bridge. It is not evidence of edge and must not replace backtest validation.
- DeepSeek is the planned LLM provider for this project. Do not assume Claude unless the user explicitly changes this.
- Supported Databento credential envs are `DATABENTO_API_KEY`, `DATABENTO_SPY0DTE_API`, `DATABENTO_API_MO`, and `DATABENTO_API_AI`. Do not store key values. `DATABENTO_API_MO` and `DATABENTO_API_AI` form one approved $200 research pool, each individual key remains capped at $100, and the selected key env must be logged before paid Databento actions.
- Entry market orders are prohibited. Unfilled entry limits should skip according to the tested protocol.
- When unsure whether a change belongs to the active SPY 0DTE scope, do not guess; surface the blocker and evidence before editing code.

## 6. Proceed-By-Default Project Workflow

- Default project behavior is **proceed by default** for normal in-plan SPY-only Higanbana work, without approval prompts. Do not ask for approval. State the intended change, affected files, and verification path, then continue.
- This includes multi-file edits, experiment scaffolds, local scripts/tests/audits, no-paid data processing, existing approved providers inside the active cost guard, coherent project-control document updates, requested git status/commit/push work, research-log maintenance, and verification-loop runs.
- Do not pause only because a task changes more than 3 files, creates or updates experiment artifacts, updates `PROJECT_BRAIN.md` / `IMPLEMENT_PLAN.md` / `AGENTS.md`, writes a research log, pushes a requested git update, or runs tests/audits.
- Ask a question only when required information is missing and cannot be inferred safely.
- Hard-stop boundaries remain only for: new paid provider, paid action that would breach the active cost guard, broker/order transmission, real-money launch, destructive filesystem/git operation, or scope change beyond SPY. At these boundaries, stop and report the boundary clearly as out-of-plan instead of framing it as a routine approval request.

## 7. Runtime And Test Tiers

- Supported runtime: Python 3.12 through 3.14.
- The `hermetic` test tier must run from committed fixtures with the Python standard library only.
- The `state-audit` tier may use `HIGANBANA_DATA_ROOT`, `HIGANBANA_WIKI_ROOT`, the nested `research_log`, and optional provider packages. Missing state must skip with the missing root named; it must not raise `FileNotFoundError`.
- Run tiers with `python scripts/run_test_tier.py hermetic`, `python scripts/run_test_tier.py state-audit`, or `python scripts/run_test_tier.py all`.
- New report writers must include `python_executable`, `python_implementation`, and `python_version` from `lib.environment.interpreter_metadata()`.

## 8. Locked Gate Integrity

- Locked gate hashes are recorded in `experiments/locked_gates.jsonl` and verified by `scripts/validate_locked_gates.py`.
- Do not edit a locked preregistration artifact or its `scripts/validate_*_preregistration.py` validator silently. A change requires a new manifest entry with a human approval note and review by the user or Fable 5 before merge.
- Every engineering commit must identify the agent model/version in a commit trailer such as `Agent: Codex (GPT-5)`.
- GitHub Actions rejects a `main` push when its HEAD commit message lacks that trailer.
- New scripts should import hypothesis-independent helpers from `lib/` instead of copy-pasting `_load_json`, `_relative`, guardrail validation, search-log, report-writing, or statistics helpers. Existing frozen scripts are not migrated in place unless a separate remediation task explicitly allows it.

## 9. Session Closure

- Every session that modifies files must end by committing and pushing to `origin/main`.
- The session report must include the resulting `origin/main` commit hash as completion evidence. Do not claim work is complete unless it is visible at that hash.
