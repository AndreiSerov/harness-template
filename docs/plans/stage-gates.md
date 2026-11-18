# Plan: stage gates, so an agent can't skip Grill, Spec or Tickets

Status: plan, not built. Comes after the Design pass is committed, because both edit `docs/agents/workflow.md`.

## What happened

On `media-transcribe` (2026-11-18), the main session applied v1.2 and then, asked to "do the refactor by all recommendations", wrote `spec.md` and three tickets by hand and sent them to implementers. It skipped `/grill-with-docs`, `/to-spec`, `/to-tickets` and the user's confirmation of test seams. Nothing stopped it: `workflow.md` says the user starts each `/` step, but a hand-written spec looks the same as one from `/to-spec`, and `implementer` takes any ticket.

The cost: the reviews of ticket 03 found the Codex tool timeout, retried calls stacking GPU runs, a concurrent-import race without Metal and `uv` missing from an app's PATH. These are design questions that grilling would have raised before the build.

## Principle

The proof that a stage happened must be an action only the user can take. A file the agent writes is not proof.

## Changes

1. **`UserPromptSubmit` hook** (`.claude/hooks/record-stage.sh`). When the user's prompt starts with `/grill-with-docs`, `/to-spec`, `/to-tickets` (or `/grill-me`, `/grilling`), it appends `<date> <stage> by user` to `.scratch/<feature>/stages.log`. The feature comes from a path in the prompt, or else from the newest `.scratch/<feature>/` directory; the hook prints which one it used, so a wrong guess is visible. The agent can't send a user prompt, so it can't produce these lines through the normal tools.
2. **`scripts/stage <feature> <stage> [reason]`** writes a line by hand: `design` after the user confirms the design review's spec changes, `seams` after the user confirms test seams, and `skip-<stage> "<reason>"` when the user decides to skip one. It is listed in `permissions.ask`, so every call by an agent asks the user.
3. **`stages.log` is read-only to the agent**: `Write(./.scratch/*/stages.log)` and `Edit(./.scratch/*/stages.log)` go in `permissions.deny`.
4. **Gates.**
   - `scripts/claim <feature>/<NN>` refuses unless `stages.log` has `grill`, `spec`, `design` and `seams` (or their `skip-`), plus `tickets` when the feature has more than one ticket. Codex and opencode call `claim` too, so the gate covers them.
   - A `PreToolUse` hook on `Agent` blocks `subagent_type: implementer` when the prompt names a `.scratch/<feature>/` that fails the same check. The message: "Stop. Ask the user to run `/<next stage>`."
   - A `PreToolUse` hook on `Write|Edit` blocks writing `.scratch/*/spec.md` before `grill`, and `.scratch/*/issues/*` before `spec`.
5. **Review and CI.** `scripts/check` fails when a branch changes code under a feature in `.scratch/` whose `stages.log` misses a stage. The reviewer quotes `stages.log` at the top of the review. `scripts/session-stats` counts features per stage and skips, for the retro.
6. **Stop points in `workflow.md`.** Before steps 1–3 (and after the Design step), the agent ends its turn with "Next step: `/<skill>`; please run it", and does nothing else for that feature until the stage appears in `stages.log`.

## Other agents

The gate logic lives once, in `scripts/hooks/stage-gate`. It reads a hook event as JSON on stdin and answers in Claude Code's format (`hookSpecificOutput`, `permissionDecision`). Each agent gets a thin adapter:

| Agent | Adapter | Events |
|---|---|---|
| Claude Code | `.claude/settings.json` | `UserPromptSubmit` records a stage; `PreToolUse` on `Agent`, `Write`, `Edit` blocks |
| Codex | `.codex/hooks.json`, loaded in a trusted project | the same wire format; `UserPromptSubmit`, `PreToolUse` on `Bash` |
| opencode | `.opencode/plugin/stage-gate.ts` | `tool.execute.before` runs the same script |

`scripts/stage` asks the user in every agent: `permissions.ask` for Claude Code, `prefix_rule(pattern=["scripts/stage"], decision="prompt")` in `.codex/rules/` for Codex, and `"bash": {"scripts/stage *": "ask"}` in `opencode.json`.

The hard gates don't depend on any agent: `scripts/claim`, the git `pre-commit` in `.githooks/` and CI. Hooks only catch a skip earlier, before the build.

To check before building:

- Codex 0.169's binary lists `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `SessionStart`, `SubagentStop` and a `codex_hooks` feature. Third-party guides say `PreToolUse` fires only for `Bash`, so a spec written through `apply_patch` would get past the hook and be caught by `claim`, `pre-commit` and CI.
- Whether Codex needs `features.codex_hooks = true` at this version, and whether the matcher is ignored for `UserPromptSubmit`.
- opencode's plugin event names at the version the template targets.

## Out of scope

Work without a feature folder: upkeep, `diagnosing-bugs`, `/ask-matt` routes, harness changes. The gates look only at `.scratch/<feature>/`.

## Limits

- Deny and ask rules match tool calls, not every shell command: `echo >> stages.log` in Bash gets past them. That is a deliberate forgery rather than a silent skip, and CI and the reviewer see the result in the PR. A hard guarantee needs Claude Code's sandbox with `.scratch/*/stages.log` outside the writable paths.
- Confirm on a test project that `permissions.ask` still asks in auto mode.
- With `issue_tracker: github`, the log becomes labels or a comment on the spec issue; design that when it's needed.

## Expected, and how to measure

- No implementer starts on a feature without `grill` and `spec` in its log; `skip-` lines carry a reason from the user.
- Fewer review findings that are design questions rather than code defects. Count them per stage in the retro, against `media-transcribe`'s deepening stage: 0 blocking, and 4 design questions out of 11 findings on ticket 03.
