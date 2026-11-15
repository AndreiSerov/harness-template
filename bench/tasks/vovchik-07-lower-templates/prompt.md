Implement **Тикет 07 — Нижние шаблоны (1.4)** in {workdir} on the already checked-out branch `bench`. Do not push, open a PR, or switch branches.

Read first: `AGENTS.md`, `docs/agents/agreements.md`, `GLOSSARY.md`, `PROGRESS.md`, `DECISIONS.md`, `MOCKS.md`, `docs/adr/0001…0004`, `docs/specs/stage-1-modules-to-parts.md` (section "Тикет 07" at the bottom, "1.2", "1.4" and the testing section), `docs/specs/00-source-brief.md` (the workshop data and Petrov's order), `workshop/construction.yaml`, `engine/kitchen/parts.py` (how `base_door` is built), the golden `tests/golden/base_door_600.json` and its tests.

What to build:
- Templates `base_drawers`, `base_sink`, `base_bottle`, `dishwasher_panel` producing parts, hardware, edging and facade area like `base_door`, through the same API (`api.parts_from_project`) and CLI.
- Rules missing from `construction.yaml` you choose yourself: add them as `# ДОБАВЛЕНО (МОК)` keys, list them in `MOCKS.md`, and record each in `DECISIONS.md` with «ПРОВЕРИТЬ МАСТЕРУ».
- A golden JSON per template (`<template>_<width>`: base_drawers_600, base_sink_750, base_bottle_150, dishwasher_panel_600), written by hand from the rules with the calculation in comments and «ПРОВЕРИТЬ МАСТЕРУ», independent of the engine's output. Golden tests green.
- Anything a template can't build correctly is a Russian error naming the module, never a silently wrong result.
- Mark 07 done in `PROGRESS.md` in the same commit. Commit message prefix `07: `, no Co-Authored-By. The pre-commit hook runs `scripts/check`; run ruff fixes in a separate Bash call before committing.

Report back concisely: what was built, files, tests count, `scripts/check` result, commit hash, decisions recorded, what's manual/not run.
