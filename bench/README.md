# Bench

Replays real tickets from projects built on this harness, to compare harness versions before a release. A task is the repo at the commit before a ticket, the coordinator's original prompt, a reviewer's prompt, and hidden tests written from the findings of the historical reviews. Every run goes through review, as a real ticket does: the implementer builds, the reviewer (Opus) checks, and a failed review goes back to the implementer, up to three times. Each hand-back is graded with the hidden tests.

```sh
caffeinate -i bench/run bench/tasks/<task> <variant> --repo <local checkout> [--keep]
```

Each run appends a line to `results.jsonl`: hidden tests and `scripts/check` per round, the full review reports, returns, commits, minutes, cost, model responses, Edit calls, file writes through Bash, edit-hook blocks. A failed call (usage limit, budget) stops the run with verdict `ERROR` and the field `aborted`; such a run is not a result.

## Variants

A variant lays harness files over the task's base commit: `paths` from the project at `ref`, then `template_paths` from this repository's `template/` at the commit `template`, for a version the project hasn't got yet. Only plain files can come from the template, not `.jinja` ones. `workflow.md` matters little here, since the runner plays the coordinator.

## Adding a task

1. Pick a ticket whose review sent it back for a missed case.
2. `task.toml`: the repo, the base commit, the first hand-back and the final fix, and the variants.
3. `prompt.md`: the coordinator's prompt, with `{workdir}` for the clone. `acceptance.md`, if a variant appends it: the acceptance checks the ticket lists.
4. `review.md`: the reviewer's prompt, with `{base}`, ending in a `VERDICT: PASS` or `VERDICT: FAIL` line.
5. `hidden_test.py`: black-box tests through the ticket's own interface, one per review finding. Check them on history before use: they must fail on the first hand-back and pass on the final fix.

## Reading results

`Responses` counts the implementer's model round trips, which drive time and cost. Runs of one model on one ticket vary, so compare over several runs, and a single task cannot show a difference in hidden tests the size of one or two.

## vovchik-12 (cutting)

Historically the costliest ticket: 7 min of build, then 88 min of review fixes, for parts coming out larger than nominal next to a gap of 1..kerf, an unchecked sheet trim length and a textured sheet crash. The hidden tests replay the cut list and accept one that includes the perimeter trim; the trim test uses a 2060 mm maximum, which only the sheet trim exceeds. Checked on history: 20/22 on the first hand-back, 22/22 on the fix.

| Date | Variant | Returns | Hidden by round | Final | Min | USD (impl + review) | Responses |
|---|---|---|---|---|---|---|---|
| history | — | 2 | 20 → … → 22 | 22/22 | ~95 | — | — |
| 2026-11-15 | v1_0 | 2 | 21 → 21 → 22 | 22/22 | 20.2 | 5.48 (2.63 + 2.85) | 36 |
| 2026-11-15 | v1_2, run 1 | 2 | 22 → 22 → 22 | 22/22 | 30.7 | 5.91 (2.66 + 3.25) | 48 |
| 2026-11-15 | v1_2, run 2 | 1 | 22 → 22 | 22/22 | 16.1 | 4.00 (2.32 + 1.68) | 36 |
| 2026-11-15 | v1_2, run 3 | 1 | 22 → 22 | 22/22 | 22.1 | 4.58 (2.53 + 2.05) | 38 |
| 2026-11-15 | v1_3, run 1 | 2 | 22 → 22 → 22 | 22/22 | 17.6 | 4.38 (2.42 + 1.96) | 40 |

**v1_0** went back twice and ended right; its second review found the strip thinner than the kerf, the defect the historical review found.

**v1_2.** Every first hand-back passed all hidden tests, against 21/22 for v1_0. The acceptance checks in the ticket name the same class of defect as the hidden tests, so this measures checks written into the ticket, not a more careful model. Every return was for a defect a probe confirmed and the hidden tests don't check: a non-guillotine `EngineError` on valid random part sets, then fractional millimetre fields accepted and rounded (run 1); fractional kerf and trim rounded down so that a part comes out 0.5 mm short (run 2); textured parts turned when a rotatable part shares the layout (run 3). No return was for style. Runs 2 and 3 cost less than run 1 mostly through one return instead of two.

**v1_3**, one run. The first hand-back passed all hidden tests again. Two returns, both blocking and confirmed: kerf and trim rounded silently and a countertop sheet written short side first giving 6 sheets instead of 1; then a sheet that one part fills entirely crashing the layout at trim 0. Each re-review put its new minor findings on the end-of-stage list instead of sending them back, as v1.3 asks. Within the v1_2 range on time and cost. On this ticket v1.3 can show little: its other changes (`claim --needs`, parallel tests, the keep-awake rule) act on worktrees, a large suite and long sessions, which the bench doesn't have.

Dropped: runs without review, which graded only the first hand-back; v1_1, whose overlay held project files from a later state and whose branch is gone (one run, 19/22, see `CHANGELOG.md`); two v1_2 runs voided by a usage limit; tasks 02 and 07, which had no reviewer's prompt and where every variant passed every hidden test.
