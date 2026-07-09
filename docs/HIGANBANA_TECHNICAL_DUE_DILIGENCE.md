# Higanbana Technical Due Diligence

- **Role assumed**: Principal Engineer inheriting this project for a 10-year horizon
- **Date**: 2026-07-09, repo @ main (`advance hypothesis-led research tracks`)
- **Method**: full clone with history; structural census (181 scripts / 51.6k LOC, 159 test files / 16.4k LOC, 549 md, 752 json); executed the full test suite on a clean Linux machine; measured duplication, import graph, and growth velocity; read the control plane and the new hypothesis-registry layer.
- **Scope**: architecture, AI engineering loop, repository evolution, long-term maintainability, silent failure modes. Not a code review; not a redesign.

---

## 0. Design Intent As I Understand It (steelman first)

Before critiquing, the architecture deserves to be stated in its own terms, because most of its unusual choices are coherent once you see what it is:

**This repo is not primarily a software system. It is a protocol for governing LLM agents doing quantitative research, with a human as the approval authority.** Under that reading:

1. **Zero third-party dependencies** (the import census shows pure stdlib: `typing`, `pathlib`, `json`, `argparse`, `statistics`; `databento` only at the download boundary). Intent: nothing rots. A 2036 Python can still run 2026 scripts. For a 10-year horizon this is a genuinely strong call that most teams get wrong in the other direction.
2. **One standalone script per experiment, near-zero shared code** (169 separate `def main`, 98 copies of `_load_json`, 96 of `_relative`). Intent: experiments are frozen artifacts; changing shared infrastructure can never silently change a past result.
3. **Tests as behavioral guardrails on agents, not just logic checks.** A large fraction of tests assert things like `test_current_preregistration_passes`, `test_rejects_paid_data_permission`, `test_rejects_paper_trading_or_strategy_pnl_claim`. Intent: an agent cannot advance state, spend money, or overstate evidence without a red suite. The test suite is the enforcement arm of PROJECT_BRAIN.
4. **Markdown control plane as inter-agent memory** (PROJECT_BRAIN 839 lines, 63 docs, handoff files). Intent: any agent, any session, can boot from documents alone.
5. **Append-only machine-readable evidence** (690 report JSONs, hashes, search logs, preregistration JSONs). Intent: anti-overstatement and auditability.

This is a real architecture with a real point of view, and the governance layer is ahead of most professional quant research teams I would benchmark it against. The problems below are not "this style is wrong." They are places where the implementation of the intent undermines the intent itself over a 10-year horizon.

---

## 1. Finding #1 (Critical): The repository cannot verify itself off one laptop

I ran the suite on a clean clone: **675 tests, 37 failures + 35 errors (~11% red)** — on a machine that is not `D:\Fogust`. Root causes, measured:

1. **Tests read the gitignored `data/` tree.** The majority of failures are `FileNotFoundError: data/normalized/spy_0dte/vix_vxv/vix_vxv.jsonl` and siblings. Dozens of "unit tests" are actually assertions about the author's local dataset.
2. **25 files hardcode `D:/Fogust/...` paths** — including preregistration validators whose *evidence basis* is files in a local "LLM Wiki" outside this repo (`wiki_basis_missing:D:/Fogust/Workspace/LLM Wiki/...`).
3. **Windows path-separator assertions** (`assertIn("data\\raw\\spy_0dte\\macro_calendar", ...)`) fail on POSIX.
4. **Undeclared dependency**: `import databento` with no `requirements.txt`, no `pyproject.toml`, no Python version pin anywhere in the repo.
5. **`run_fixture_pipeline.py` hardcodes a sibling project's Windows venv**: `PROJECT_ROOT.parent / "Yuehua Investment Lab" / ".venv" / "Scripts" / "python.exe"`.

Why this is the top risk rather than a portability nitpick: the project's entire safety model is "the suite tells you whether the state is sound." That property currently exists **on exactly one machine**. The GitHub push creates an *illusion* of durability — the code is backed up, but the ability to verify anything is not, and the data is explicitly excluded. Over 10 years the probability that this specific laptop, folder layout, and sibling-directory arrangement survives is approximately zero. The failure is silent: nothing will announce the day the project became unverifiable; you will discover it during a disaster, which is the one time you cannot afford to.

**Recommendation (preserves design intent):**
- Split the suite into two explicitly named tiers: **hermetic** (fixtures committed in `tests/fixtures`, must pass on any clean clone — this is what CI runs) and **state-audit** (requires local `data/`; auto-skip with a loud `skipUnless(DATA_ROOT.exists())` marker rather than erroring). The state-audit tier is a legitimate, intentional part of your design — it just needs to be declared as such instead of failing as if broken.
- Introduce one environment manifest (env vars or a single untracked `machine.json`): `HIGANBANA_DATA_ROOT`, `HIGANBANA_WIKI_ROOT`, `HIGANBANA_IBKR_PYTHON`. Replace the 25 hardcoded `D:/` references. This is mechanical work Codex can do in one pass with a test that greps for the forbidden pattern afterward.
- Add `requirements-optional.txt` (databento, pinned) and a `python_requires` statement; record the exact interpreter version in every report JSON (some already record environment details — make it uniform).
- Turn on GitHub Actions running the hermetic tier on every push. This single change makes the repo self-verifying for as long as GitHub exists, at zero cost, and gives every future agent an oracle that is not the author's laptop.
- Write `docs/BACKUP_AND_RESTORE.md`: enumerate the four stores that jointly constitute the project (this repo, the nested `research_log` repo, the gitignored `data/` tree, the LLM Wiki), verify that data checksums in the dataset registry actually cover everything paid-for, and **perform one rehearsed restore onto a second machine**. A backup that has never been restored is a hypothesis, and this project of all projects should not run untested hypotheses.

---

## 2. Finding #2 (High): Code accretion is super-linear in hypotheses, and the copying mechanism propagates defects

Measured growth: 181 scripts, 51,577 LOC. **H-A2 alone has spawned 76 scripts**, including 21 `validate_*_preregistration` scripts, in roughly six days of agent work. Duplication census: 98 near-identical `_load_json`, 96 `_relative`, 20 `write_reports`, 16 `_validate_guardrails`, 15 `_write_search_log`, plus hand-rolled render/report code in nearly every runner.

The frozen-experiment intent justifies freezing *strategy logic*. It does not require freezing *infrastructure* — loaders, timestamp discipline, guardrail validation, report writing, and the statistics kernel are not part of any hypothesis, yet they are copy-pasted into every script. Two compounding consequences:

- **Defect propagation by the generator itself.** Codex writes new scripts by imitating existing ones (visible in the near-identical function bodies). If any copy of `_load_jsonl`, the ET-timestamp handling, or the PnL basis has a subtle bug, the agent will faithfully replicate it into every future script, and no fix can be applied in one place. This is a silent failure mode with a built-in amplifier.
- **The freeze is already inconsistent.** Several H-A2 scripts *import* from `run_m5_regime_filter_sensitivity.py` (`load_vix_vxv`) — so an "archived" M5 experiment script is now live infrastructure for active H-A2 work. That is the worst of both worlds: past results are mutable through a dependency nobody declared, while the codebase still pays the full duplication tax.

At the current velocity (~76 scripts per active hypothesis-month), year 3 of this project is a 1,000+ script repo where no human — and increasingly no context-window — can hold the inventory. The research governance will still be pristine; the substrate under it will be unmaintainable.

**Recommendation (two-zone rule, no redesign of existing files):**
- Create `lib/` (or `higanbana/`) containing exactly the infrastructure that is hypothesis-independent: JSON/JSONL IO, timestamp discipline, guardrail validation, search-log writer, report renderer, and the statistics kernel. New scripts import it; **existing scripts are left untouched** — their frozen status is preserved by never editing them, which git already guarantees.
- Reconcile freezing with a shared lib the way you already reconcile it for data: provenance. Every report JSON records the git commit hash (several already do); reproduction of an old result is `git checkout <hash>`, not "the script file was never edited." Make that rule explicit in PROJECT_BRAIN so agents stop copy-pasting defensively.
- Add a drift audit: a script that fingerprints the duplicated function bodies across `scripts/` and reports any copy that has silently diverged from the majority version. Cheap to build, and it converts the current unknown ("have the 98 copies drifted?") into a measured fact.
- Grandfathering metric for the readiness audit: count of new scripts that bypass `lib/` should trend to zero.

---

## 3. Finding #3 (High): Hand-rolled quantitative statistics with no reference anchors

Stdlib-only means PSR, MinTRL, skewness/kurtosis adjustments, Black–Scholes bracketing, and ES95 are all hand-implemented. I independently reproduced the MinTRL=285 figure from the audit inputs, which is a good sign — but that was one spot-check by one reviewer. Nothing in the repo pins these implementations to published reference values, and every accept/kill decision for the next decade flows through them.

The concrete nightmare scenario: a convention slip — raw vs. excess kurtosis in the PSR variance term, sample vs. population skew, per-trade vs. annualized Sharpe in a null comparison — produces numbers that are plausible, internally consistent, wrong, and load-bearing. No gate would catch it, because the gates consume these numbers as ground truth. This is precisely the class of error that survives ten years unnoticed.

**Recommendation:** a single `tests/test_statistics_golden.py` in the hermetic tier: known inputs → outputs cross-checked once against published worked examples (Bailey & López de Prado for PSR/MinTRL/DSR) and against a reference library run *once, offline* (scipy on any machine — the dependency is for generating the fixture, not for runtime). Commit the golden numbers. From then on, the zero-dependency property is preserved and the numerics are anchored. Also centralize the statistics kernel into `lib/` per Finding #2 — duplicated statistics code is where convention slips breed.

---

## 4. Finding #4 (High): The AI engineering loop has one structural conflict — the guarded agent maintains the guardrails

The loop (user → Fable planning → handoff → Codex implementation → tests/validators as enforcement → markdown brain as memory) is genuinely strong: model diversity between planner and implementer, preregistration before execution, anti-overstatement validators, decision records, cost gates. Most of what I would normally recommend to a team adopting agentic engineering, you already have.

The structural weakness: **Codex writes the experiment, writes the preregistration validator, writes the test that asserts the validator passes, and edits all three in the same commit.** The test pattern `test_current_preregistration_passes` asserts only that the validator approves the current JSON — so an agent optimizing for a green suite can (without malice, purely as instrumental behavior under "make the checks pass") weaken a validator and its fixture together, and the suite goes green while the gate goes decorative. Today your own review is the backstop; over ten years and thousands of commits, per-commit human review of validator diffs will not survive.

**Recommendations:**
- **Gate immutability for locked decisions.** Once a preregistration is locked, its validator file and decision JSON get their SHA-256 recorded in an append-only manifest (`experiments/locked_gates.jsonl`), and a hermetic meta-test verifies hashes. Changing a locked gate then requires a new manifest entry with a human-approval field — the same pattern you already use for policy v1/v2 in gamma, generalized to code.
- **Separate the reviewer from the author at the gate layer.** You already run a two-model loop; formalize it: validator diffs for locked hypotheses are reviewed by the *other* model (or the human) before merge. Cheap to state in AGENTS.md; agents follow written contracts well.
- **Add an adversarial pass to the loop.** Nothing in the current loop has refutation as its only job. Before any result is promoted to E2, one session (either model) is tasked purely with breaking it — data leakage hunting, alternative nulls, implementation-bug hypotheses. Budget it like you budget data.
- **Version the agents.** Model name/version is recorded for LLM *experiments* but not for the *engineering sessions that build the gates*. Add a commit-trailer or session field. When a model upgrade changes agent behavior — and it will, repeatedly, over a decade — you want the boundary visible in history.
- **Watch control-plane saturation.** PROJECT_BRAIN is 839 lines and growing; the boot sequence keeps lengthening. Agents degrade gracefully but silently when context saturates: they skim. Keep moving state out of prose into machine-readable registries (the hypothesis registry and `report_project_state` were exactly the right moves) and keep the BRAIN as pointers plus invariants, not as a chronicle. The chronicle belongs in reports and git.

---

## 5. Finding #5 (Medium): Repository evolution — artifact bloat, split evidence, and a history that starts at the migration

- **Reports are append-only in git: 690 JSON + 474 md, 33 MB, growing with every diagnostic.** At H-A2's current cadence this is thousands of machine-generated files within a couple of years. Git handles the bytes; humans and agents don't — meaningful diffs drown, clones slow, and `reports/` becomes write-only memory. Recommend a retention tier: acceptance-grade and decision-record artifacts stay in git forever; bulk diagnostics move on a schedule to an archive area (branch, LFS, or external store) with the audit index remaining the source of truth. The audits already read indices, so this is low-friction.
- **The evidence trail spans four stores with different durability**: this repo (GitHub), the nested `research_log` repo (separate flow), gitignored `data/` (one disk), and the LLM Wiki (one disk, referenced by absolute path from validators). A successor cannot reconstruct "what happened and why" from any single store. Beyond the restore rehearsal in Finding #1: **hash the cited wiki artifacts into the preregistration JSONs.** Today a validator checks that `minimum-track-record-length.md` *exists* at a `D:/` path; if the wiki page is edited later, the recorded basis of past decisions silently changes. Content hashes make the basis immutable evidence instead of a mutable pointer.
- **History starts at the migration** (15 commits; the entire pre-GitHub evolution is squashed into the initial import). Not recoverable, but going forward: tag decision points (`gamma-policy-v2`, `h-a1-falsified`, plan archives) so future engineers can diff between governance epochs instead of archaeology through Backup_IMPLEMENT_PLAN filenames.
- **Provider-coupling at the boundary**: the failing `test_probe_databento_opra_statistics` on a clean machine shows stat-type mapping degrades to raw enum strings without the vendored lib. Databento schema/enum evolution over a decade is certain. The boundary scripts should validate against your committed `schemas/` on ingest (you have a schemas dir — extend it to the OPRA statistics shape) so provider drift fails loudly at import, never silently in analysis.

---

## 6. Silent Failure Catalogue (ranked by expected 10-year damage)

| # | Failure mode | Mechanism | Current detection | Fix ref |
|--:|:--|:--|:--|:--|
| 1 | Laptop/environment loss makes project unverifiable | data, wiki, venv, paths all machine-coupled; suite red off-machine | none | §1 |
| 2 | Convention error in hand-rolled statistics distorts every accept/kill | no golden-number anchors | none | §3 |
| 3 | Defect replicated across ~180 script copies by the code-generating agent | copy-paste architecture + imitation | none | §2 |
| 4 | Gate erosion: agent weakens validator + fixture together, suite stays green | author == gatekeeper | human review only | §4 |
| 5 | Wiki-basis drift: cited methodology pages edited after decisions locked | existence check, no content hash | none | §5 |
| 6 | "Edit the test to match reality" habit: state-assertion tests require editing on every legitimate state change, normalizing test edits as routine | tests encode live state | culture only | §1 (tier split makes state tests explicit) |
| 7 | Provider schema/enum drift silently misparses OI/quotes | boundary lacks ingest-time schema validation | partial | §5 |
| 8 | Bit rot / partial corruption in the paid `data/` tree | single disk, unclear checksum coverage | registry (verify) | §1 |
| 9 | Control-plane saturation: agents skim a growing BRAIN and drift from policy | prose growth | none | §4 |

---

## 7. Verdict

**Can this architecture, workflow, and AI ecosystem reach the goal?** The research-governance layer — preregistration, evidence tiers, falsification-first budgeting, anti-overstatement validators, the two-model plan/implement split — is the strongest part of the project and is *better* than what most funded quant teams operate. On governance alone, yes: this process can honestly find an edge or honestly conclude there isn't one, which is the actual goal.

The binding constraint is underneath: the software substrate is currently a **single-machine artifact with a super-linear growth model**. Unattended, the failure sequence over ten years is predictable: (a) the environment coupling turns any hardware or life event into project loss-of-verifiability; (b) script accretion makes the repo illegible to its own agents around year 2–3; (c) one un-anchored statistics convention or one eroded gate quietly corrupts the decision record that everything else exists to protect.

None of this needs a redesign, and none of it contradicts the design intent — every fix above strengthens the intent (frozen evidence, agent governance, decade-scale reproducibility) rather than replacing it. In priority order: **(1)** hermetic/state test split + CI + environment manifest + restore rehearsal; **(2)** golden-number statistics anchors; **(3)** the two-zone `lib/` rule for all *new* code + drift audit; **(4)** locked-gate hashing + cross-model gate review; **(5)** report retention and wiki-content hashing. Items 1, 2 and 4 are days of Codex work each; item 3 is a standing rule, not a migration. I would not start any new data purchase or hypothesis expansion until item 1 exists, because every dollar and every result acquired before then is stored in a system that cannot yet survive its owner.
