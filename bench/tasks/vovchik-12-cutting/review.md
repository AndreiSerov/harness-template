Review the commits on the current branch since `{base}`: they implement **Тикет 12 — Раскрой (2.1)** of `docs/specs/stage-2-cutting-edging-purchase.md`. You report and do not edit the repository; put any probe scripts in a temporary folder outside it.

Check it against the ticket, the "2.1" decisions of that spec, `AGENTS.md`, `docs/agents/agreements.md`, `GLOSSARY.md` and the ADRs. Run `scripts/check` yourself. Try to break it: other sheet formats, textured materials, parts that barely fit, the saw's maximum cut length, a replay of the cut list that checks every part comes out at its nominal size.

Give each finding with file and line, the concrete failure, whether you confirmed it, and whether it blocks.

End your report with exactly one line: `VERDICT: PASS` when nothing blocks, or `VERDICT: FAIL` when anything does.
