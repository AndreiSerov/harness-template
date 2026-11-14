Implement **Тикет 02 — `scripts/link-skills` (0.1)** in {workdir} on the already checked-out branch `bench`. Do not push, open a PR, or switch branches.

Read first: `AGENTS.md`, `docs/agents/agreements.md`, `docs/adr/0003-portable-skills.md`, `docs/specs/stage-0-foundation.md` (section "Тикет 02" at the bottom and "0.1" decisions), `PROGRESS.md`, existing `scripts/sync-skills`, `scripts/doctor`, `scripts/check`, `.gitignore`, `.claude/skills/.managed.json` (sync-skills' bookkeeping — understand how it manages `.claude/skills/` so link-skills doesn't fight it, e.g. sync-skills must not delete our symlinks and link-skills must not touch managed skills).

What to build:
- `scripts/link-skills`: for every `skills/kitchen-*/` dir with a `SKILL.md`, create relative symlinks in `.claude/skills/`, `.agents/skills/`, `.qwen/skills/` (create the dirs). Idempotent; replaces only its own stale symlinks; never touches other skills or real files (if a real dir/file with the same name exists — warn, skip, non-zero exit). Removes its own dangling links whose target skill was deleted.
- `--hermes`: same into `~/.hermes/skills/` (respect `$HOME`), with absolute link targets. This writes to the user's home dir — do NOT run it for real; test it with a fake HOME only.
- Add `.agents/` and `.qwen/` to `.gitignore`.
- `scripts/sync-skills` calls link-skills at the end (without `--hermes`); `scripts/doctor` reports missing or broken kitchen-* links.
- README: one line on `scripts/link-skills` and the manual `--hermes` step.
- Language: bash or python (match the existing scripts' style). Must work on macOS and Linux (CI is ubuntu).
- Tests (pytest) in a temp copy/tmp dir: creates links in all three places, rerun is a no-op, foreign skills/files untouched, real-dir conflict is reported, dangling own link removed, `--hermes` with fake HOME. The real `--hermes` run is `manual` — mention it as not run.
- Then actually run `scripts/link-skills` in the repo (without `--hermes`) so the existing `kitchen-brief` is linked, and confirm `scripts/check` passes.
- Mark 02 done in PROGRESS.md in the same commit. Commit message prefix `02: `, no Co-Authored-By. The pre-commit hook runs `scripts/check`; run ruff fixes in a separate Bash call before committing.

Report back concisely: what was built, files, tests count, `scripts/check` result, commit hashes, decisions recorded in DECISIONS.md, what's manual/not run.
