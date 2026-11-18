# Changelog

Each release records what changed in the harness, what agent behaviour it is meant to change, and the metric that shows whether it did. `scripts/session-stats` in a generated project gives the numbers. Fill **Observed** once a project has finished a stage on the release, and compare it with the baseline of the release before.

## Design pass — unreleased, on top of v1.2.0

From the retro of `test-proj-mccbasis`, a test task built on v1.0 (one spec, 7 tickets and 6 hardening tickets). An outside reviewer of the finished service found four design faults, and every one of them traces back to the harness:

- The spec asked for a repository layer in one line of Implementation Decisions. No ticket repeated it, the tests are black-box by design, and the reviewer checked against the ticket, so queries, locks and transactions ended up in the router, the handler and the Relay.
- The spec itself told the handler to run the 2–5 s Emulator inside a `SELECT … FOR UPDATE` transaction, and accepted a repeated Webhook on every redelivery. Grilling settles what the user wants, and no step asked what a design holds while it waits or what a second run does.
- Hardening tickets added SSRF pinning, URL masking and NUL checks (about 240 of 1,400 lines). The reviewer called it too much for a test task. The spec never said who the reader was or how much of their time the result gets.
- `skill-scout` never ran, because nothing in the workflow starts it. `codebase-design` was installed but never loaded, because only `tdd` points to it, and only when an implementer questions an interface's shape.

### Changes

- Workflow: a Design step between Spec and Tickets. The main session takes the spec through the new `docs/agents/design-review.md`: module shape with `codebase-design`, what is held while waiting, what grows with load, what a second run does, the failure path, and the reader's budget. The spec changes, and the user confirms the changes. Each decision leaves with a carrier (a check in `scripts/check`, an acceptance check, or a line in every ticket it touches), and `/to-tickets` keeps it.
- Reviewer: checks against the ticket and the spec it comes from, including Implementation Decisions. It used to say "spec or ticket", which let a ticket-only review pass code that broke the spec's layout.
- `skill-scout`: runs once when the project starts and again when a spec brings in a new stack or kind of system. It also searches by the kind of system and its failure modes, not by stack and domain alone.
- `skill-scout`: proposes nothing only after at least five differently worded searches and a look at the known collections, and lists its searches. A first pass on `test-proj-mccbasis` concluded "nothing fits" after two searches.
- `docs/agents/carriers.md`: the carriers for the project's stack, cheapest first: language or build, the linter already in `scripts/check`, a boundary tool, an `ast-grep` rule, a test. The design pass picks the first one that catches the break and writes boundary contracts once the spec names its modules. On `test-proj-mccbasis`, ruff `TID251` with `per-file-ignores` caught the same 9 imports as an `import-linter` contract, with no new tool.
- Design pass: its own budget. Each question gets the simplest change that fixes it, and anything heavier is offered to the user. A blind run on `test-proj-mccbasis` added a lease column, a timeout and a requeue path where a compare-and-set was enough.
- Design pass names the skills for each kind of question. `DEEPENING.md` in `codebase-design` sorts each module's dependencies, which decides the seam and the tests. `research` covers a library's real behaviour, `prototype` a race that can't be settled on paper, `DESIGN-IT-TWICE.md` one unclear central module within the budget, and `domain-modeling` new terms and lasting decisions. Before, only `codebase-design` was named, and in the build session of `test-proj-mccbasis` none of these ran.
- `improve-codebase-architecture` moves from the optional skills to the core set. The user runs it at Ship when a stage built several tickets. On `test-proj-mccbasis` it found a missing timeout that no review had caught.
- Stacks `node-pnpm` and `rust-cargo`, next to `python-uv` and `generic`: `scripts/check`, CI setup, `.gitignore`, the lint-suppression rule in `agreements.md` and a carriers table each. The TypeScript and Rust tables come from the tools' documentation and have not run on a project yet.

### Expected

- No spec reaches `/to-tickets` with a slow call inside a transaction or lock, or with an external side effect that has no record of having happened.
- Every layering decision in a spec has a check in `scripts/check` from the first ticket.
- Fewer late findings from outside review on structure and resource use. Measure them as findings per stage that trace back to the spec rather than the code.

### Observed

`test-proj-mccbasis`, one run each in a clean Claude Code session on Opus, before the budget rule and `carriers.md`:

- Design pass on the original spec, with no code yet ($0.75, 3 min). It found the Emulator inside `FOR UPDATE`, the pool tied to the concurrency, the missing layering check and the reader's budget. It saw the repeated Webhook but put it under Out of Scope as a question for the user. It over-built the fix (a lease).
- `/improve-codebase-architecture` on the finished code, for comparison ($1.50, 5 min). It found none of the outside reviewer's points except, partly, the logic in the route. It did find a likely bug the reviewer missed: the retry republish has no timeout.
- Caveat: `design-review.md` was written after the outside review, so its questions name those faults. A project with different faults is the real test.

## v1.2.0 — unreleased

v1.1 measured on the bench (`bench/README.md`) and cut back to what held up. Ticket 12 with review, one run each: v1.0 went back twice and ended right (22/22); v1.1 went back once and the reviewer passed it with three sheet formats still wrong (19/22).

### Changes against v1.1

- Reviewer: a re-review is a full review again. In v1.1 it checked only the fix commits and passed a change that the hidden tests still failed; the v1.0 reviewer, reviewing fully, found a new blocking defect in round two.
- Reviewer: a judgement call on structure or style is reported but does not block. In v1.1 a `CODING_STANDARDS.md` rule produced a blocking finding that did not change any result and cost a round.
- Workflow: before review, the coordinator checks that the reported commit exists and `scripts/check` passes on it. On the bench one implementer handed back uncommitted with a red check, and the reviewer spent a round on it.
- `scripts/claim`: taking a ticket is one atomic step, so two agents starting together can't both get it. The coordinator releases the claim before handing a ticket to a fresh implementer; before, the fresh implementer's own first step would find the old claim and stop.
- Commit hook: checks the repository the commit goes to, following `cd dir` and `git -C dir`, not the session's folder. Before, a commit to another repository was blocked by this project's red check, and a commit into this project from elsewhere was not checked.
- Implementer: no prose self-check. It doubled the cost on ticket 07 and did not raise the hidden-test score anywhere. Instead the ticket lists the acceptance checks the reviewer will run, and the implementer turns them into tests; a check that recurs becomes a test or a tool in the project.

### Kept from v1.1

All findings in one report with pasteable reproductions; open decisions settled before the build; `scripts/claim`; the in-place edit hook with `sd` and `ast-grep`; the git pre-commit hook for other agents; `scripts/check` left to the commit hook; `scripts/session-stats`; a fresh implementer from the second return and building during review (not yet exercised by the bench).

### Observed on the bench

Ticket 12 with review, three runs: 22/22 in every run, against 22/22 for v1.0 and 19/22 for v1.1. 1–2 real returns per run, each for a defect the reviewer confirmed with a probe (a crash on a valid layout, silent rounding of fractional millimetres, two commands disagreeing), none for style. 20–31 min and 5.0–6.8 USD a run, about half of it the Opus review, against 20.2 min and 5.48 USD for v1.0. Two first hand-backs already passed all hidden tests, which credits the acceptance checks in the ticket. One implementer handed back without committing, with `scripts/check` red: the commit hook does not stop an agent from ending without a commit, so the coordinator checks the hash before review. Not yet observed on a real project stage.

## v1.1.0 — superseded by v1.2.0, never tagged

From a retro of `vovchik-furniture-kit`, stages 0–2, 15 tickets run by Claude Code subagents, Codex and opencode.

### Changes

- `workflow.md`: a Review rounds section. Open decisions are settled before the build; one review gives one report and one fix commit; a fresh implementer takes over from the second return; a second implementer builds the next independent ticket during review; hard tickets may run on a stronger model.
- `reviewer.md`: every finding in one report, each with a reproduction to paste as a failing test; a re-review checks only the fixes, and its new minor findings wait for the end of the stage; a mechanical finding names the check that would catch it.
- `implementer.md`: claims the ticket, follows the project's ambiguity rule, uses Edit for targeted changes and a script for bulk ones, runs targeted tests and leaves `scripts/check` to the commit hook, goes through `docs/agents/self-check.md` if present, fixes a whole review in one commit.
- `.claude/hooks/no-in-place-edit.sh`: blocks `sed -i` and `perl -i` on tracked files. A first version sent every Bash write of a tracked file to Edit; the bench showed it doubled responses on ticket 07 (31 against 15, $1.31 against $0.71) with the same hidden-test score, so it was narrowed.
- `agreements.md` Editing files, read by every agent: Edit for a targeted change, `sd` for a text pattern across files, `ast-grep` for a structural change, previewed first; the in-place hook points to them. `scripts/doctor` requires `git` and `python3` and names a missing `rg`, `sd` or `ast-grep`; the README lists the prerequisites.
- `.githooks/pre-commit`, turned on by `sync-skills` and checked by `doctor`: commits outside Claude Code run `scripts/check`.
- `scripts/claim`: one ticket, one agent, across worktrees.
- `scripts/session-stats`: the numbers below.
- Carried from before the retro: the commit hook fails closed when `scripts/check` is missing; a ticket goes back at most three times.

### Baseline (v1.0.0, `vovchik-furniture-kit`, tickets 10–13)

| Metric | Value | Source |
|---|---|---|
| First build, start to first commit | 4–8 min per ticket, 24 min in total | git |
| Review fixes, first commit to last fix | 15–88 min per ticket, about 210 min in total (~90% of ticket time) | git |
| Review returns into the same implementer context | 1–5 per ticket | session-stats `returns` |
| Implementer context at its peak | up to 247k tokens | session-stats `peak-context` |
| Responses cut off mid-stream | 4, about 36 min lost | session-stats `cut-offs` |
| File writes through Bash versus Edit | 9 of 13 implementers never used Edit | session-stats `bash-writes`, `edits` |
| Implementer idle while waiting for review | 10–24 min per ticket | transcripts |
| Duplicate work | ticket 05 built twice in parallel (opencode), 27 min lost | transcripts |

Across tickets 01–13, every ticket needed at least one review-fix commit. Findings were mostly edge cases the reviewer reproduced (malformed input, concurrency, fuzzed layouts, the real fixture's PDF), then decisions made mid-ticket, then a separate round for minor findings.

### Expected

- Review-fix commits per ticket: at most 1 for most tickets, down from 1–3.
- Rework time: well under the first build's multiple of ~9×.
- `cut-offs`: 0, through a fresh implementer before the context passes ~150k.
- No ticket claimed twice.

### Observed

Pending: fill in after the first stage built on v1.1.0, with the same table.
