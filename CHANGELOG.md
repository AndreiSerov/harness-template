# Changelog

Each release records what changed in the harness, what agent behaviour it is meant to change, and the metric that shows whether it did. `scripts/session-stats` in a generated project gives the numbers. Fill **Observed** once a project has finished a stage on the release, and compare it with the baseline of the release before.

## v1.2.0 — unreleased

v1.1 measured on the bench (`bench/README.md`) and cut back to what held up. Ticket 12 with review, one run each: v1.0 went back twice and ended right (22/22); v1.1 went back once and the reviewer passed it with three sheet formats still wrong (19/22).

### Changes against v1.1

- Reviewer: a re-review is a full review again. In v1.1 it checked only the fix commits and passed a change that the hidden tests still failed; the v1.0 reviewer, reviewing fully, found a new blocking defect in round two.
- Reviewer: a judgement call on structure or style is reported but does not block. In v1.1 a `CODING_STANDARDS.md` rule produced a blocking finding that did not change any result and cost a round.
- Workflow: before review, the coordinator checks that the reported commit exists and `scripts/check` passes on it. On the bench one implementer handed back uncommitted with a red check, and the reviewer spent a round on it.
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
