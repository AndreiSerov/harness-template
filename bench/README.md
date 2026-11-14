# Bench

Replays real tickets from projects built on this harness, to compare harness versions before a release. A task is the repo at the commit before a ticket, the coordinator's original prompt, and hidden tests written from the reviewer's findings on the historical first hand-back. The score is how many hidden tests the implementer's first hand-back passes: each one it misses was a round of review.

```sh
bench/run bench/tasks/<task> <variant> --repo <local checkout> [--keep]
```

Each run appends a line to `results.jsonl`: hidden tests passed, `scripts/check`, commits, minutes, cost, turns, Edit calls, file writes through Bash, edit-hook blocks.

## Adding a task

1. Pick a ticket whose review sent it back for a missed case.
2. `task.toml`: the repo, the base commit, the first hand-back and the final fix, and the harness variants as files laid over the base from a git ref.
3. `prompt.md`: the coordinator's prompt, with `{workdir}` for the clone.
4. `hidden_test.py`: black-box tests through the ticket's own interface, one per review finding. Check them on history before use: they must fail on the first hand-back and pass on the final fix.

## Reading results

One run per variant shows whether the pipeline works and how the harness changes tool use. It cannot show a difference in hidden tests: runs of one model on one ticket vary. Compare scores only over several runs and several tasks.

## Runs

| Date | Task | Variant | Hidden | Min | USD | Turns | Edit | Bash writes | Hook blocks |
|---|---|---|---|---|---|---|---|---|---|
| history | vovchik-02 | first hand-back `b9a606d` | 8/10 | ~6 | — | — | — | — | — |
| 2026-11-15 | vovchik-02 | v1_0 | 9/10 | 1.1 | 0.27 | 7 | 0 | 4 | 0 |
| 2026-11-15 | vovchik-02 | v1_1 | 9/10 | 1.2 | 0.29 | 17 | 9 | 0 | 1 |
| history | vovchik-07 | first hand-back `6d8bc4f` (Codex) | 8/12 | — | — | — | — | — | — |
| 2026-11-15 | vovchik-07 | v1_0 | 12/12 | 3.9 | 0.71 | 18 | 0 | 7 | 0 |
| 2026-11-15 | vovchik-07 | v1_1 | 12/12 | 7.6 | 1.31 | 60 | 31 | 2 | 1 |

**vovchik-07.** Both variants passed every hidden test, so on this ticket today's Sonnet does not miss what the historical hand-back missed, harness or not. v1_1 cost twice as much: 60 turns against 18, because each change is a separate Edit call and it ran the self-check (malformed widths, thresholds, a search for duplicate rules), which added 23 more tests of its own (301 against 278 in the suite). Its self-check also named `scripts/petrov-sandbox`, which does not exist at the task's base: overlaying project files from a later ref leaks references the base cannot satisfy. Its two Bash writes were new untracked files, which the hook allows.

**vovchik-02.** Both runs found the major case the historical hand-back missed (a link to a removed skill) and both missed the re-review's minor one (an own link pointing at the wrong skill). The coordinator's prompt already names dangling links, which the original ticket did not stress as much. v1_1 changed tool use as intended: every file change went through Edit, and the hook stopped one Bash write.
