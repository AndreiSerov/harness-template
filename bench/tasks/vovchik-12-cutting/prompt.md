Implement **Тикет 12 — Раскрой (2.1)** in {workdir} on the already checked-out branch `bench`. Do not push, open a PR, or switch branches. Stage 1 is closed.

Read first: `AGENTS.md`, `docs/agents/agreements.md`, `GLOSSARY.md`, `PROGRESS.md`, `DECISIONS.md`, `MOCKS.md`, `docs/adr/0001…0004`, `docs/specs/stage-2-cutting-edging-purchase.md` (the "2.1" decisions and "Тикет 12" at the bottom), the cutting parts of `docs/specs/00-source-brief.md`, `workshop/equipment.yaml`, `workshop/materials.yaml`, `engine/kitchen/api.py`, `engine/kitchen/parts.py`, `tests/fixtures/petrov_project.json`.

What to build: `kitchen cut <заказ>|--project <file> [--json]` and the API behind it lay out the sheet parts of the current project version by material, guillotine-only with kerf and perimeter trim, never rotating textured parts, with the order of cuts. Countertop is cut linearly and separately; facades are not cut. A layout that is not guillotine is an engine error. Every cut length is checked against the saw's maximum. Results carry the source version and the mock banner like other results.

Result contract (tests read these names):
- `api.cut_from_project(path, home) -> CutResult` and `api.cut_from_order(order, home) -> CutResult`; a part that does not fit is an `OrderError` naming its mark.
- `CutResult(Result)`: `order`, `source`, `kerf`, `trim`, `max_cut_length`, `materials: list[MaterialCut]`, `countertop` (or `None`), `warnings`.
- `MaterialCut`: `material`, `name`, `sheet_size: tuple[int, int]` (x along the grain), `texture: bool`, `sheet_count`, `parts_count`, `parts_area_m2`, `sheet_area_m2`, `utilization`, `waste_m2`, `algorithm`, `sheets: list[SheetCut]`.
- `SheetCut`: `number`, `placements: list[Placement]`, `cuts: list[CutCut]`, `parts_area_m2`, `utilization`.
- `Placement`: `part` (mark), `x`, `y` (mm from the sheet edge, trim included), `w`, `h` (size along the sheet's x and y), `rotated`.
- `CutCut`: `number` (from 1 per sheet, in cutting order), `direction` (`"vertical"` is the line `x = position`, `"horizontal"` is `y = position`), `position`, `start`, `end` (along the line), `length`, `kind` (`"separate"` or `"trim"`). The kerf occupies `position … position + kerf`. Each cut runs edge to edge across one piece of the working field.

Tests (pytest, through `kitchen.api`): no overlaps, inside the working field, kerf between parts, no rotation of textured parts, determinism. Record your decisions in `DECISIONS.md`, mark 12 done in `PROGRESS.md` in the same commit. Commit message prefix `12: `, no Co-Authored-By. The pre-commit hook runs `scripts/check`.

Report back concisely: what was built, files, tests count, `scripts/check` result, commit hash, decisions recorded, what's manual/not run.
