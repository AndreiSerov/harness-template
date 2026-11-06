# harness-template

A Copier template that gives a repository an agent harness. `README.md` covers usage and which files the template or the project owns.

This file is for working on the template itself. `template/AGENTS.md.jinja` is what generated projects receive.

## Done means

`uv run pytest && uv run ruff check && uv run ruff format --check` all pass.

A change to `.claude/settings.json.jinja` or `.claude/hooks/` also needs real `claude -p` sessions in a rendered throwaway project, because only Claude Code can show whether a rule or hook fires. The hook tests call the script directly. Confirm each result from what happened, such as the commit count and the hook's message: a session that fails to start also adds zero commits. Report anything you could not run as not run.

- Put the prompt before the flags, because `--allowedTools` consumes the arguments after it.
- Unit tests missed `git -C . commit`, `git -c a=b commit` and `sh -c "git commit"` getting past the first hook. Real sessions found them.

## Changing the template

- Only files ending in `.jinja` are rendered. Files in `template/` keep their executable bit, so check it on new scripts.
- A file the project should own after creation goes in `_skip_if_exists` in `copier.yml`, and in the README's ownership table.
- A new skill goes in `.claude/skills.toml.jinja` along with the skills it refers to, so references resolve. A `/name` in `workflow.md` must be an installed skill, and `scripts/doctor` checks this.
- Everything here must suit any repository. Keep personal paths and project-specific rules out; they belong in the project's own `AGENTS.md`.
- Generated scripts use only the Python standard library, because they run before a project's dependencies are installed.

## Releasing

Copier takes versions from git tags, so `copier update` sees a change only after it is committed and tagged. Tests make their own committed and tagged copy, so they run on uncommitted work.

## Conventions

- Commit messages end at the body, with no `Co-Authored-By` line.
