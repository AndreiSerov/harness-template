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

`Responses` is model round trips, the number that drives time and cost; `calls` is tool calls, several of which can come in one response. The `turns` field of `claude -p` counts something closer to calls, so it is not used here.

| Date | Task | Variant | Hidden | Min | USD | Responses | Calls | Edit | Bash writes |
|---|---|---|---|---|---|---|---|---|---|
| history | vovchik-02 | first hand-back `b9a606d` | 8/10 | ~6 | — | — | — | — | — |
| 2026-11-15 | vovchik-02 | v1_0 | 9/10 | 1.1 | 0.27 | 6 | 6 | 0 | 4 |
| 2026-11-15 | vovchik-02 | v1_1 | 9/10 | 1.2 | 0.29 | 8 | 16 | 9 | 0 |
| 2026-11-15 | vovchik-02 | v1_1, batched edits | 8/10 | 1.3 | 0.26 | 8 | 17 | 10 | 1 (new file) |
| history | vovchik-07 | first hand-back `6d8bc4f` (Codex) | 8/12 | — | — | — | — | — | — |
| 2026-11-15 | vovchik-07 | v1_0 | 12/12 | 3.9 | 0.71 | 15 | 17 | 0 | 7 |
| 2026-11-15 | vovchik-07 | v1_1 | 12/12 | 7.6 | 1.31 | 31 | 59 | 31 | 2 (new files) |
| history | vovchik-12 | first hand-back `499ff2f` | 20/22 | 7 | — | — | — | — | — |
| 2026-11-15 | vovchik-12 | v1_0 | 20/22 | 5.0 | 0.84 | 20 | 21 | 1 | 8 |
| 2026-11-15 | vovchik-12 | v1_1, in-place hook only | 21/22 | 7.2 | 1.20 | 33 | 35 | 3 | 13 |

### With review (`--review-rounds 3`, reviewer on Opus)

| Date | Task | Variant | Returns | Hidden by round | Final | Min | USD (impl + review) |
|---|---|---|---|---|---|---|---|
| history | vovchik-12 | — | 2 | 20 → … → 22 | 22/22 | ~95 | — |
| 2026-11-15 | vovchik-12 | v1_0 | 2 | 21 → 21 → 22 | 22/22 | 20.2 | 5.48 (2.63 + 2.85) |
| 2026-11-15 | vovchik-12 | v1_1 | 1 | 19 → 19 | 19/22 | 17.3 | 4.48 (2.00 + 2.48) |
| 2026-11-15 | vovchik-12 | v1_2, run 1 | 3 (1 void) | 22 → 22 → 22 → 22 | 22/22 | 28.7 | 6.82 (3.05 + 3.77) |
| 2026-11-15 | vovchik-12 | v1_2, run 2 | 2 (1 void) | 20 → 20 → 22 | 22/22 | 19.8 | 4.99 (2.55 + 2.43) |
| 2026-11-15 | vovchik-12 | v1_2, run 3 | 2 | 22 → 22 → 22 | 22/22 | 30.7 | 5.91 (2.66 + 3.25) |
| 2026-11-15 | vovchik-12 | v1_2, run 4 | 1 | 22 → 22 | 22/22 | 16.1 | 4.00 (2.32 + 1.68) |
| 2026-11-15 | vovchik-12 | v1_2, run 5 | 1 | 22 → 22 | 22/22 | 22.1 | 4.58 (2.53 + 2.05) |

v1_2, runs 4 and 5, two in parallel under `caffeinate -i`, as a baseline before v1.3. Both first hand-backs passed all hidden tests, and each went back once. Run 4 went back for fractional kerf and trim rounded down, so a part comes out 0.5 mm short, the same defect as in run 1. Run 5's fix commit names textured parts that come out turned when a rotatable part shares the layout; the start of its report is cut off in `results.jsonl`, so the blocking finding itself isn't recorded. Neither re-review found a blocking defect. The cost and the minutes are below runs 1–3, mostly from a cheaper review (1.7–2.1 USD against 2.4–3.8). Five runs of one ticket are still too few to call that a change.

v1_2, three runs in parallel. All three ended at 22/22, and no reviewer passed a change the hidden tests fail. Two first hand-backs were already 22/22, against 19–21 for v1_0 and v1_1; the acceptance checks in the ticket name the same class of defect as the hidden tests, so this measures checks written into the ticket, not a more careful model. In run 2 the first hand-back was left uncommitted with `scripts/check` red; the reviewer returned it, along with three crashes on valid orders, and a fresh implementer brought it to 22/22. Real returns were 1–2 per run, each for a defect a probe confirmed and the hidden tests don't check: a non-guillotine `EngineError` on valid rectpack layouts (fuzz, 10 of 2,000 sets), fractional kerf, trim and sheet sizes rounded silently against `DECISIONS.md`, and `kitchen cut` and `kitchen parts` disagreeing on countertop sheets at a fractional kerf. No return was for style. The cost is the review: 2.4–3.8 USD of Opus a run, against 2.5–3.1 for the implementer.

"Void" is a return that wasn't one: in runs 1 and 2 the first review call hit the account's usage limit, the runner read the missing verdict as FAIL and sent the limit message back as findings. `bench/run` now stops a run on a failed call (verdict `ERROR`, field `aborted`) and hands a re-review the earlier reports, as a coordinator would; before that, one re-reviewer said it could not check the earlier findings were closed.

v1_0 went back twice and ended correct; its second review found the strip thinner than the kerf, the defect the historical review found. v1_1 went back once and the reviewer passed it with three sheet formats still failing (a non-guillotine layout ends in an engine error); its fixes were real but outside what the hidden tests check, and one of its two blocking findings came from `CODING_STANDARDS.md` naming a function the base does not have yet. Fewer returns here meant a weaker result, not a better harness. One run each.

Contamination to fix before the next runs: `CODING_STANDARDS.md` and `self-check.md` in the v1_1 overlay come from a later state of the project and name things the base lacks (`checks.part_fit_findings`, `scripts/petrov-sandbox`).

**vovchik-12 (cutting).** The first task where the hidden tests separate the runs. v1_0 failed on two sheet formats: it picked a layout that cannot be cut guillotine-wise and stopped with an engine error, the same class of defect the historical review sent back. v1_1 cut every format correctly and checked the sheet trim against the saw's maximum, but placed a textured HDF part 2096 mm long along a 2070 mm grain by rotating it instead of naming it. One run each, so this is a signal, not a result. The narrowed hook let v1_1 write through scripts (13 Bash writes) and cost 33 responses against 20.

Two fixes to the hidden tests before grading: the replayer now accepts a cut list that includes the perimeter trim, which the contract leaves open, and the trim test uses a 2060 mm maximum, which only the sheet trim exceeds, and accepts any `KitchenError`. Both are checked on history: 20/22 on the first hand-back, 22/22 on the fix.

**Batched edits (vovchik-02).** The instruction to send independent edits together changed nothing here: this ticket was already 8 responses, with up to 8 Edits in one. v1_1 on ticket 02 costs the same as v1_0. The second v1_1 run scored 8/10 against 9/10 for the first, missing doctor's report of a real folder in the way: run-to-run noise of the size this table cannot resolve.

**vovchik-07.** Both variants passed every hidden test, so on this ticket today's Sonnet does not miss what the historical hand-back missed, harness or not. v1_1 cost twice as much: 31 responses against 15. It already batched (12 responses held several calls), so the gap comes from smaller edits than v1_0's multi-place heredoc scripts, from reading the self-check and claiming the ticket, and from running the self-check (malformed widths, thresholds, a search for duplicate rules), which added 23 more tests of its own (301 against 278 in the suite). Its self-check also named `scripts/petrov-sandbox`, which does not exist at the task's base: overlaying project files from a later ref leaks references the base cannot satisfy. Its two Bash writes were new untracked files, which the hook allows.

**vovchik-02.** Both runs found the major case the historical hand-back missed (a link to a removed skill) and both missed the re-review's minor one (an own link pointing at the wrong skill). The coordinator's prompt already names dangling links, which the original ticket did not stress as much. v1_1 changed tool use as intended: every file change went through Edit, and the hook stopped one Bash write.
