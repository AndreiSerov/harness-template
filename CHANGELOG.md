# Changelog

Each release records what changed in the harness, what agent behaviour it is meant to change, and the metric that shows whether it did. `scripts/session-stats` in a generated project gives the numbers. Fill **Observed** once a project has finished a stage on the release, and compare it with the baseline of the release before.

## v1.1.0 — unreleased

From a retro of `vovchik-furniture-kit`, stages 0–2, 15 tickets run by Claude Code subagents, Codex and opencode.

### Changes

- `workflow.md`: a Review rounds section. Open decisions are settled before the build; one review gives one report and one fix commit; a fresh implementer takes over from the second return; a second implementer builds the next independent ticket during review; hard tickets may run on a stronger model.
- `reviewer.md`: every finding in one report, each with a reproduction to paste as a failing test; a re-review checks only the fixes, and its new minor findings wait for the end of the stage; a mechanical finding names the check that would catch it.
- `implementer.md`: claims the ticket, follows the project's ambiguity rule, uses Edit for targeted changes and a script for bulk ones, runs targeted tests and leaves `scripts/check` to the commit hook, goes through `docs/agents/self-check.md` if present, fixes a whole review in one commit.
- `.claude/hooks/no-in-place-edit.sh`: blocks `sed -i` and `perl -i` on tracked files. A first version sent every Bash write of a tracked file to Edit; the bench showed it doubled responses on ticket 07 (31 against 15, $1.31 against $0.71) with the same hidden-test score, so it was narrowed.
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
