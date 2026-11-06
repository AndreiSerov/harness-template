# harness-template

A [Copier](https://copier.readthedocs.io) template for an agent harness: the workflow, settings, hooks, subagents and pinned skills for working in a repository with Claude Code. It was extracted from `rt-speech`.

## Use it

```sh
uvx copier copy <template> <project>
```

Then, in the project:

```sh
scripts/sync-skills   # install the pinned skills into .claude/skills/
scripts/doctor        # confirm that the harness is complete
```

Later, `uvx copier update` brings in template changes, and needs the project's work to be committed first. Copier versions come from this repository's git tags, so tag a release after changing the template.

## What the project gets

| Owned by the template, changed by `copier update` | Owned by the project, created once |
|---|---|
| `.claude/settings.json`, `.claude/hooks/`, `.claude/agents/` | `AGENTS.md`, `CLAUDE.md`, `GLOSSARY.md` |
| `docs/agents/` | `.claude/skills.toml` |
| `scripts/sync-skills`, `scripts/doctor` | `scripts/check`, `.gitignore` |
| `.github/workflows/check.yml`, `opencode.json` | |

## Skills

External skills aren't copied into git. `.claude/skills.toml` names each source and pins a commit, and `scripts/sync-skills` installs a private copy for that project in the gitignored `.claude/skills/`. `--update` pulls the newest commit, moves the pin and prints what changed. Skills are instructions your agent will follow, so read that output before committing the new pin.

Worktrees need no extra setup: Claude Code reads an ignored `.claude/skills` from the main checkout.

## Limits

- **Deny rules aren't a security boundary.** In a test session, `Read` and `cat` on a denied folder were both refused, but Claude Code documents that a Bash rule matches the command text Claude writes, not every way to run a program. For a hard guarantee, turn on its [sandbox](https://code.claude.com/docs/en/sandboxing.md), which the template leaves off because it can break projects that need hardware or wider file access.
- **The commit hook recognises commands by their text.** It handles `git -C . commit`, `git -c a=b commit` and `sh -c "git commit"`, but a commit hidden behind a script or alias gets past it, and `git -C other-repo commit` runs the checks of the current repo. CI remains the final check.
- **`opencode.json` patterns** follow opencode's documented syntax, but the template's tests only check that the file renders.

## Develop

```sh
uv run pytest && uv run ruff check && uv run ruff format --check
```

The tests render the template into a temporary folder and run the generated scripts against a local skills source, without network access.
