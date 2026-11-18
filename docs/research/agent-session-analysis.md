# Agent session analysis: build or reuse?

Researched 2026-11-18. **Provenance:** every claim has a URL. Items marked *(summary)* were seen only as a search or WebFetch summary, not as raw text. Stars are given only where a repo page showed them.

## Answer first

- **Build a thin session-judge. Do not build the plumbing.** No existing tool does the core job: matching agent decisions to a post-review git state and computing reviewer and design-pass precision/recall. That part, the labelling and the metrics are ours to build.
- **Reuse Inspect Scout (MIT) as the engine if it fits.** It imports `~/.claude/projects` natively, runs LLM and grep "scanners" over transcripts, validates them against human-labelled sets (precision, recall, F1, balanced accuracy) and runs locally. Try it before writing a parser or judge runner.
- **Get deterministic events from the transcript JSONL plus Claude Code's own signals.** The OTel `tool_result` and `tool_decision` events, and hook events such as `PostToolUseFailure` and `PermissionDenied`, already name failure and denial sources.
- **Adopt the MAST taxonomy** (14 modes, human κ=0.88, o1 judge κ=0.77). Extend it with harness-specific codes such as "unspecified decision" and "design via review".
- **Validate the judge the MAST/EvalGen way:** a human-labelled set, κ compared against the human-human κ, a held-out split, and small-sample-safe intervals (not CLT).
- **Skip** Langfuse, Phoenix, LangSmith and Braintrust as primary stores. They give tracing UIs, not the reference-matching metrics.

## 1. Community tools that parse coding-agent session logs

| Tool | What it extracts | Beyond tokens/cost? | License / stars (as seen) |
|---|---|---|---|
| [ccusage](https://github.com/ryoppippi/ccusage) | Token and cost reports by day, session and 5h block; about 20 agents incl. Codex and OpenCode | No (models, cache, project grouping) | MIT, 19.5k |
| [claude-code-log](https://github.com/daaain/claude-code-log) | JSONL→HTML/TUI; tool results "with error handling", subagent branches, thinking, token usage | Viewer only, no classification | MIT, 1.3k |
| [cc-analyze](https://github.com/seankim-android/cc-analyze) | Context usage, tool breakdown, "Repeated failure patterns (same error 3+ times)", "Dead zones" | Yes: loop and stall heuristics | No license shown, 0 stars, 1 commit |
| [parse-cc](https://github.com/d1ll0n/parse-cc) | TS `Session` class: tool calls, subagents, metrics | Library only *(summary)* | not checked |
| [cc-transcript](https://pypi.org/project/cc-transcript/), [cctx-cli](https://pypi.org/project/cctx-cli/0.1.0/) | Python parser, grep and render; cctx claims "find what went wrong" and suggests CLAUDE.md patches | cctx: diagnosis *(summary)* | not checked |
| [claude-code-transcripts](https://pypi.org/project/claude-code-transcripts/) (simonw) | JSONL→paginated HTML | No *(summary)* | not checked |
| [claude-code-transcripts (Rust)](https://docs.rs/crate/claude-code-transcripts/0.1.8/source/README.md) | Typed parser with a schema-drift validator | Useful for format drift *(summary)* | not checked |
| Multi-agent viewers: [Klovi](https://awesome.ecosyste.ms/projects/github.com%2Fcookielab%2Fklovi), [claude-code-history-viewer](https://github.com/jhlee0409/claude-code-history-viewer), [tracebench](https://github.com/Skandesh/tracebench), [codex-trace](https://gh.hhj520.top/PixelPaw-Labs/codex-trace) | Viewing and search across Claude Code, Codex, Cursor and OpenCode | Mostly no; tracebench lists "behavior analytics" as planned *(summary)* | not checked |

**Takeaway:** the community tools are viewers and cost counters. Only cc-analyze does even heuristic failure detection, and it is a one-commit repo. None classifies behaviour against a spec.

## 2. Observability and eval frameworks

**Claude Code's own telemetry** ([monitoring docs](https://code.claude.com/docs/en/monitoring-usage); I read a WebFetch extraction of the first 100k characters):
- **Events:**
  - `claude_code.tool_result`: `tool_name`, `success`, `error_type`, `duration_ms`, `decision_source`; `error` and `tool_input` only with `OTEL_LOG_TOOL_DETAILS=1`.
  - `claude_code.tool_decision`: `decision` accept/reject; `source` is one of `config`, `hook`, `user_permanent`, `user_temporary`, `user_abort`, `user_reject`.
  - Also `api_error`, `user_prompt` (text redacted unless `OTEL_LOG_USER_PROMPTS=1`) and `assistant_response`.
- **Traces:** beta (`CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`). Spans: `claude_code.interaction`, `llm_request`, `tool` (with `blocked_on_user` and `execution` children), and `hook`.
- **Metric:** `claude_code.code_edit_tool.decision`.
- **Fit:** these give hook blocks and permission denials as structured fields, which is better than regex over JSONL. They are live-only, though: you cannot backfill old sessions from them.

**Hooks** ([hooks docs](https://code.claude.com/docs/en/hooks)): events include `PostToolUseFailure`, `PermissionDenied`, `PermissionRequest`, `SubagentStart`, `SubagentStop`, `StopFailure` and `TaskCompleted`. Hooks receive `transcript_path`. The JSONL schema is **not documented** on that page, and the docs warn that the file "may lag".

| Framework | Ingests Claude Code? | LLM judge over trajectories | Local / self-host |
|---|---|---|---|
| [Inspect Scout](https://meridianlabs-ai.github.io/inspect_scout/) | **Native.** `scout import claude_code` reads `~/.claude/projects`, splits on `/clear` and merges plan-mode files ([sources ref](https://meridianlabs-ai.github.io/inspect_scout/reference/sources.html), added in 0.4.23 per the [changelog](https://meridianlabs-ai.github.io/inspect_scout/CHANGELOG.html) *(summary)*). Also imports Phoenix, LangSmith, Logfire, MLflow and Weave. | `llm_scanner()` (bool, number, classification, JSON answers), `grep_scanner()`, custom scanners; [validation sets](https://meridianlabs-ai.github.io/inspect_scout/validation.html) with dev/test splits and P/R/F1 (no kappa) | Yes: local `./scans` dir and a local viewer. [MIT, 91 stars](https://github.com/meridianlabs-ai/inspect_scout) |
| [Docent](https://docs.transluce.org/) (Transluce) | Via SDK *(summary)* | Rubric judges, clustering, labelling, a Q&A agent over runs *(summary)* | Not verified |
| [Langfuse](https://langfuse.com/integrations/developer-tools/claude-code) | Stop hook converts transcript messages into traces; `Tool: X` spans. Errors and subagents not mentioned. | LLM-as-judge and annotation queues; core [MIT since 2025-06](https://langfuse.com/blog/2025-06-04-open-sourcing-langfuse-product) *(summary)* | Self-host via `LANGFUSE_BASE_URL` |
| [Arize Phoenix](https://arize.com/docs/phoenix/integrations/coding-agents/claude-code) | Plugin `coding-harness-tracing` built on hooks; OpenInference spans *(summary)* | Phoenix evals | Local, default `localhost:6006` *(summary)* |
| [DeepEval](https://deepeval.com/docs/evaluation-trajectory-based-llm-evals) | Requires its own tracing; no Claude Code importer seen | Task Completion, Tool Correctness, Plan Adherence *(summary)* | Local library |
| [OTel GenAI semconv](https://github.com/open-telemetry/semantic-conventions-genai) | Moved to its own repo; stability status not shown on the page | n/a | n/a |
| LangSmith, Braintrust, promptfoo | Not investigated in depth; no native Claude Code importer found | — | — |

## 3. Research on trajectory analysis and failure taxonomies

| Paper | Method / taxonomy | Validation | Reusable |
|---|---|---|---|
| [MAST: Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657) (NeurIPS'25 D&B *(summary)*) | Grounded theory on 150 traces. 14 modes in 3 categories: **System design** (1.1 disobey task spec, 1.2 disobey role spec, 1.3 step repetition, 1.4 loss of history, 1.5 unaware of termination), **Inter-agent misalignment** (2.1 conversation reset, 2.2 fail to ask for clarification, 2.3 task derailment, 2.4 information withholding, 2.5 ignored other agent's input, 2.6 reasoning-action mismatch), **Task verification** (3.1 premature termination, 3.2 no/incomplete verification, 3.3 incorrect verification) ([html](https://arxiv.org/html/2503.13657v3)) | Three experts, 15 traces over three rounds, κ=0.88. o1 few-shot judge: accuracy 0.94, κ=0.77 | Taxonomy, 1600+ annotated traces (MAST-Data), LLM annotator ([GitHub](https://github.com/multi-agent-systems-failure-taxonomy/MAST) *(summary)*) |
| [TRAIL](https://arxiv.org/abs/2505.08638) (Patronus) | 148 traces, 1987 OTel spans; Reasoning / Planning & Coordination / System Execution | Best model (gemini-2.5-pro) scored about 11% at localising errors *(summary)* | MIT dataset on HF *(summary)*; evidence that long-trace localisation is hard for judges |
| [Agent-as-a-Judge](https://arxiv.org/abs/2410.10934) (ICML'25) | An agent judge with tools inspects the workspace; DevAI has 55 tasks and 365 hierarchical requirements | Reported 90% vs 70% (LLM-judge) agreement with human consensus *(summary)* | [Code](https://github.com/metauto-ai/agent-as-a-judge) *(summary)*; supports a judge that can read the repo, not just the log |
| [Bouzenia & Pradel](https://arxiv.org/abs/2506.18824) | Unified 120 trajectories from 3 agents into one format; action categories, sequence mining, open coding of thought-action-result coherence | Not checked | Dataset and annotation framework released *(summary)*; closest analogue to our parser |
| [Understanding Code Agent Behaviour](https://arxiv.org/html/2511.00197v1) | Success vs failure trajectories (OpenHands, SWE-agent, Prometheus) | Not checked | Failed runs are longer and more variable *(summary)* |
| [Empirical Study on Failures in Automated Issue Solving](https://www.themoonlight.io/review/an-empirical-study-on-failures-in-automated-issue-solving) | 9 categories, 25 subcategories | Not checked | Seen only via a secondary review *(summary)* |
| [Graphectory](https://arxiv.org/html/2512.02393v2), [Coherence Collapse](https://www.alphaxiv.org/abs/2603.24631) | 4000 and 16,758 trajectories; agents rarely run regression tests; 60–69% of failures edit the right functions | Not checked | *(summary)* |

## 4. Validating LLM judges

- **[Zheng et al., MT-Bench](https://arxiv.org/abs/2306.05685).** Identifies position, verbosity and self-enhancement bias. GPT-4's agreement with humans was above 80%, the same level as human-human agreement. The paper also proposes reference-guided grading for math and reasoning *(summary; reference-guided detail from memory of the paper, not re-read)*.
- **[Panickssery et al.](https://arxiv.org/abs/2404.13076).** Self-preference correlates linearly with the judge's ability to recognise its own output. This matters for a Claude judge grading Claude transcripts.
- **[Judging the Judges](https://arxiv.org/abs/2406.12624).** Percent agreement hides judge differences; use κ or Scott's π. Even good judges trailed human-human agreement, and judges tended to be lenient *(summary)*.
- **[EvalGen / Who Validates the Validators?](https://arxiv.org/abs/2404.12272).** Criteria drift: criteria cannot be fully fixed before graders see outputs. Iterate the rubric on a dev set, then freeze it *(summary)*.
- **Sample size and intervals.**
  - [Miller, Adding Error Bars to Evals](https://arxiv.org/abs/2411.00640): report standard errors and use paired, item-level comparisons *(summary)*.
  - [Bowyer et al.](https://arxiv.org/abs/2503.01747): CLT intervals underestimate uncertainty below "a few hundred datapoints"; use the Bayesian or exact methods it describes instead.
  - Prediction-powered inference (e.g. [ARES](https://arxiv.org/pdf/2311.09476)): uses a small human set to bias-correct judge estimates over a large unlabelled set *(summary)*.
  - I found no peer-reviewed rule for labelled-set size. Blog figures of about 50–200 pairs conflict ([example](https://dev.to/maya_andersson_dev/your-llm-as-judge-eval-set-is-too-small-here-is-the-math-2iac)).

## 5. Matching decisions to the final reviewed state; reviewer precision/recall

- **[Cihan et al., Automated Code Review in Practice](https://arxiv.org/abs/2412.18531)** (ICSE-SEIP'25). A Qodo PR-Agent deployment: 73.8% of bot comments were marked "resolved" by developers, and PR closure time rose *(summary)*. It is a precedent for "acceptance" as a reviewer-precision proxy.
- **[RevMate (Mozilla/Ubisoft)](https://www.mozillafoundation.org/en/research/library/impact-of-llm-based-review-comment-generation-in-practice-a-mixed-open-closed-source-user-study/).** About 8% and 7% of generated comments were accepted. Accepted comments led to later revisions about as often as human comments (74% vs 73%) *(summary)*.
- **Vendor benchmarks** ([Qodo](https://qodo.ai/ai-code-review-benchmark/), [Augment](https://www.augmentcode.com/blog/we-benchmarked-7-ai-code-review-tools-on-real-world-prs-here-are-the-results)). They score reviewer comments against gold or injected bugs with P/R/F1. The methods differ and the authors sell review tools *(summary)*.
- **No tool found** that aligns an agent's in-session decisions with a post-review git tag. That is the novel part.

## What this means for session-judge

1. **Event schema.** Derive events from the JSONL, keeping `session_id`, `agent_id`/subagent file, `parent_uuid`, `tool_use_id`, timestamps and `git_sha`. Event kinds:
   - `tool_call`, `tool_error` (`is_error`, validation error)
   - `hook_block`, `permission_denied`
   - `loop` (N identical failing calls)
   - `user_question` (AskUserQuestion), `review_finding`, `fix_commit`
   - Name fields after OTel `tool_result`/`tool_decision` (`success`, `error_type`, `decision`, `source`) so live telemetry can replace the parser later. Pin the JSONL schema with a drift check, since it is undocumented.
2. **Deterministic first.** Errors, denials, loops, questions and review→fix cycles are parseable. Use the LLM judge only for "unspecified decision", "design via reviewer" and MAST codes.
3. **Taxonomy.** Use MAST IDs where they fit: 1.1 (task spec), 1.2 (role, e.g. implementer doing design), 1.3 (repetition), 2.2 (fail to ask), 3.2/3.3 (verification). Add harness codes: `UNSPEC_DECISION`, `DESIGN_VIA_REVIEW`, `HOOK_FRICTION`.
4. **Judge.**
   - Per-event classification with evidence quotes, not whole-session scores. TRAIL shows long-trace localisation is weak.
   - Give the judge the ticket, the spec and the post-review diff as the reference, and let it read the repo (Agent-as-a-Judge).
   - Use a non-Claude or different-family judge for a bias check, given self-preference.
   - Randomise order in any pairwise prompt.
5. **Validation protocol.**
   - Two humans label the same items, and human-human κ sets the ceiling (MAST did this).
   - Iterate the rubric on a dev split, then freeze it and report κ on a held-out test split (Scout supports splits).
   - Report κ plus per-class P/R with small-sample intervals (Bowyer).
   - Re-validate on any change to the model or prompt.
6. **Labelled-set size.** Start with about 100–200 labelled events stratified by class (my judgement, not a sourced rule), and widen it if the κ interval is too wide.
7. **Do not build:** a transcript viewer (use claude-code-log), a cost tracker (use ccusage), a trace UI, or a judge runner and validation harness. Try Inspect Scout first; fall back to `claude -p` only if Scout's import misses subagent files.

## Open questions / not verified

- Whether Scout's `claude_code` source includes `subagents/*.jsonl` and hook or permission records. I did not read its source. Test it on one real session.
- The second half of the Claude Code monitoring page was not read; `tool_decision` attributes may be incomplete.
- The MAST GitHub repo, the judge-prompt licence, TRAIL's licence and the Agent-as-a-Judge numbers are from summaries only.
- Docent's licence and whether it can run locally; LangSmith, Braintrust and promptfoo were not examined.
- No commit dates were visible on any repo page.
- No fetched content contained instructions aimed at the agent.

## Searches run

1. claude code session transcript jsonl analyzer github
2. Why Do Multi-Agent LLM Systems Fail MAST taxonomy arXiv
3. Agent-as-a-Judge evaluate agents with agents DevAI arXiv
4. Langfuse Claude Code integration tracing
5. Arize Phoenix Claude Code tracing OpenInference
6. empirical study failure trajectories SWE-agent OpenHands coding agents arXiv taxonomy
7. claude-code-log transcript viewer HTML github
8. Docent Transluce agent transcript analysis tool
9. Who Validates the Validators aligning LLM-assisted evaluation human preferences criteria drift
10. inspect_scout Claude Code transcripts import source
11. Judging LLM-as-a-Judge MT-Bench Chatbot Arena position bias self-enhancement bias agreement
12. empirical study LLM automated code review comments resolved acceptance rate industry
13. Cihan automated code review in practice LLM industry study comments resolved Beko
14. LLM judge reliability Cohen's kappa human agreement sample size bootstrap confidence interval evaluation guidance
15. LLM evaluators recognize and favor their own generations self-preference arXiv
16. TRAIL trace reasoning issue localization agentic traces taxonomy benchmark arXiv
17. Judging the Judges evaluating alignment vulnerabilities LLMs-as-judges Cohen's kappa percent agreement
18. prediction-powered inference LLM judge small human labeled set confidence intervals evaluation
19. benchmark AI code review tools precision recall real-world pull requests bug detection 2025
20. Bouzenia Pradel understanding software engineering agents thought-action-result trajectories
21. Langfuse self-hosted open source license MIT enterprise features LLM-as-a-judge evaluators
22. Adding error bars to evals statistical approach language model evaluations arXiv
23. DeepEval agent trajectory metrics tool correctness task completion tracing
24. Codex CLI opencode session logs analyzer viewer open source tool errors
