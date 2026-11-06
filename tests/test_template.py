"""Render the template the way a user would, then run what it generates."""

import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
GIT_ID = ["-c", "user.name=Test", "-c", "user.email=test@example.com"]


def run(*args, cwd=None, check=True, **kwargs):
    done = subprocess.run(args, check=False, cwd=cwd, capture_output=True, text=True, **kwargs)
    if check and done.returncode:
        raise AssertionError(f"{args} failed:\n{done.stdout}\n{done.stderr}")
    return done


def git(cwd, *args):
    return run("git", *GIT_ID, *args, cwd=cwd).stdout.strip()


def commit_all(cwd, message="change"):
    git(cwd, "add", "-A")
    git(cwd, "commit", "-q", "-m", message)


@pytest.fixture
def template(tmp_path):
    """A committed, tagged copy of the template, since Copier versions come from git tags."""
    path = tmp_path / "template"
    path.mkdir()
    shutil.copy(REPO / "copier.yml", path)
    shutil.copytree(REPO / "template", path / "template")
    git(path, "init", "-q", "-b", "main")
    commit_all(path)
    git(path, "tag", "v1.0.0")
    return path


def render(template, target, **answers):
    args = [sys.executable, "-m", "copier", "copy", "--defaults", "--vcs-ref=HEAD"]
    for key, value in answers.items():
        args += ["-d", f"{key}={json.dumps(value) if not isinstance(value, str) else value}"]
    run(*args, str(template), str(target))
    return target


@pytest.fixture
def upstream(tmp_path):
    """A local skills source with two skills, standing in for a real upstream."""
    path = tmp_path / "upstream"
    for name in ("alpha", "beta"):
        (path / "skills" / name).mkdir(parents=True)
        (path / "skills" / name / "SKILL.md").write_text(f"# {name}\n")
    git(path, "init", "-q", "-b", "main")
    commit_all(path)
    return path


def use_upstream(project, upstream, skills=("skills/alpha", "skills/beta")):
    commit = git(upstream, "rev-parse", "HEAD")
    listed = ", ".join(f'"{s}"' for s in skills)
    (project / ".claude/skills.toml").write_text(
        f'[[source]]\nname = "test"\nrepo = "{upstream}"\ncommit = "{commit}"\nskills = [{listed}]\n'
    )


@pytest.fixture
def project(template, upstream, tmp_path):
    path = render(template, tmp_path / "project", private_paths=["transcripts"])
    git(path, "init", "-q", "-b", "main")
    use_upstream(path, upstream)
    # The rendered workflow names real skills; these tests use a two-skill upstream.
    (path / "docs/agents/workflow.md").write_text("Run `/alpha`.\n")
    return path


def test_python_project_has_the_expected_files_and_executables(template, tmp_path):
    project = render(template, tmp_path / "p", private_paths=["transcripts"])
    for name in (
        "AGENTS.md",
        "CLAUDE.md",
        "GLOSSARY.md",
        ".gitignore",
        ".copier-answers.yml",
        "docs/agents/workflow.md",
        "docs/agents/agreements.md",
        "docs/agents/issue-tracker.md",
        ".claude/agents/implementer.md",
        ".claude/agents/reviewer.md",
        ".github/workflows/check.yml",
    ):
        assert (project / name).is_file(), name
    for name in (
        "scripts/check",
        "scripts/sync-skills",
        "scripts/doctor",
        ".claude/hooks/check-before-commit.sh",
    ):
        assert os.access(project / name, os.X_OK), name
    assert not (project / "opencode.json").exists()
    assert "uv run pytest" in (project / "scripts/check").read_text()


def test_settings_hide_attribution_and_deny_private_paths(template, tmp_path):
    project = render(template, tmp_path / "p", private_paths=["transcripts", "recordings"])
    settings = json.loads((project / ".claude/settings.json").read_text())
    assert settings["attribution"] == {"commit": "", "pr": "", "sessionUrl": False}
    deny = settings["permissions"]["deny"]
    assert "Read(./.env)" in deny
    assert "Read(./transcripts/**)" in deny
    assert "Read(./recordings/**)" in deny
    assert "transcripts/" in (project / ".gitignore").read_text()


def test_skills_manifest_is_valid_and_includes_chosen_optional_skills(template, tmp_path):
    project = render(template, tmp_path / "p", optional_skills=["skills/engineering/wayfinder"])
    source = tomllib.loads((project / ".claude/skills.toml").read_text())["source"][0]
    assert len(source["commit"]) == 40
    assert "skills/engineering/tdd" in source["skills"]
    assert "skills/engineering/wayfinder" in source["skills"]
    assert "skills/productivity/teach" not in source["skills"]


def test_generic_stack_check_fails_until_configured(template, tmp_path):
    project = render(template, tmp_path / "p", stack="generic")
    assert run("scripts/check", cwd=project, check=False).returncode == 1


def test_optional_files_follow_the_answers(template, tmp_path):
    project = render(
        template,
        tmp_path / "p",
        use_opencode=True,
        ci=False,
        issue_tracker="github",
        private_paths=["transcripts"],
    )
    config = json.loads((project / "opencode.json").read_text())
    assert config["permission"]["read"]["*transcripts/*"] == "deny"
    assert config["permission"]["external_directory"] == "deny"
    assert not (project / ".github").exists()
    assert "gh issue create" in (project / "docs/agents/issue-tracker.md").read_text()
    assert "opencode" in (project / "docs/agents/workflow.md").read_text()


def test_sync_installs_pinned_skills_and_records_them(project):
    run("scripts/sync-skills", cwd=project)
    assert (project / ".claude/skills/alpha/SKILL.md").is_file()
    assert (project / ".claude/skills/beta/SKILL.md").is_file()


def test_sync_stays_on_the_pin_and_update_moves_it(project, upstream):
    pin = git(upstream, "rev-parse", "HEAD")
    (upstream / "skills/alpha/SKILL.md").write_text("# newer\n")
    commit_all(upstream)
    newest = git(upstream, "rev-parse", "HEAD")

    run("scripts/sync-skills", cwd=project)
    assert (project / ".claude/skills/alpha/SKILL.md").read_text() == "# alpha\n"
    assert pin in (project / ".claude/skills.toml").read_text()

    output = run("scripts/sync-skills", "--update", cwd=project).stdout
    assert (project / ".claude/skills/alpha/SKILL.md").read_text() == "# newer\n"
    assert newest in (project / ".claude/skills.toml").read_text()
    assert "SKILL.md" in output


def test_sync_removes_a_dropped_skill_but_refuses_to_replace_a_foreign_one(project, upstream):
    run("scripts/sync-skills", cwd=project)
    use_upstream(project, upstream, ["skills/alpha"])
    run("scripts/sync-skills", cwd=project)
    assert not (project / ".claude/skills/beta").exists()

    (project / ".claude/skills/beta").symlink_to(upstream / "skills/beta")
    use_upstream(project, upstream)
    done = run("scripts/sync-skills", cwd=project, check=False)
    assert done.returncode != 0
    assert "did not install" in done.stderr
    assert (project / ".claude/skills/beta").is_symlink()


def test_sync_rejects_a_path_outside_the_source(project, upstream):
    use_upstream(project, upstream, ["../../escape"])
    done = run("scripts/sync-skills", cwd=project, check=False)
    assert done.returncode != 0
    assert "inside its source" in done.stderr


def test_doctor_passes_on_a_complete_project(project):
    run("scripts/sync-skills", cwd=project)
    assert "Harness OK" in run("scripts/doctor", cwd=project).stdout


def test_doctor_reports_each_kind_of_problem(project):
    (project / ".gitignore").write_text("")
    (project / "docs/agents/workflow.md").write_text("Run `/missing-skill`.\n")
    done = run("scripts/doctor", cwd=project, check=False)
    assert done.returncode == 1
    for expected in (
        "not gitignored: .claude/skills/",
        "skill not installed: alpha",
        "installed commit differs",
        "names /missing-skill",
        "denied to agents but not gitignored: transcripts",
    ):
        assert expected in done.stdout, expected


def test_doctor_notices_skills_behind_the_pin(project, upstream):
    run("scripts/sync-skills", cwd=project)
    (upstream / "skills/alpha/SKILL.md").write_text("# newer\n")
    commit_all(upstream)
    use_upstream(project, upstream)
    assert "installed commit differs" in run("scripts/doctor", cwd=project, check=False).stdout


def call_hook(project, cwd, command="git commit -m x"):
    payload = {"cwd": str(cwd), "tool_input": {"command": command}}
    return run(
        str(project / ".claude/hooks/check-before-commit.sh"),
        check=False,
        input=json.dumps(payload),
    )


@pytest.mark.parametrize(
    "command",
    [
        "git commit -m x",
        "git -C . commit -m x",
        "git -c user.name=A commit -m x",
        "git --no-pager commit -m x",
        'sh -c "git commit -m x"',
        "cd sub && git commit --amend",
        "git add -A\ngit commit -m x",
    ],
)
def test_hook_recognises_every_form_of_commit(project, command):
    (project / "scripts/check").write_text("#!/bin/sh\nexit 1\n")
    assert call_hook(project, project, command).returncode == 2


@pytest.mark.parametrize(
    "command",
    ["git status", "git log --grep commit", "git commit-tree abc", "ls commit", "git show commit"],
)
def test_hook_ignores_commands_that_do_not_commit(project, command):
    (project / "scripts/check").write_text("#!/bin/sh\nexit 1\n")
    assert call_hook(project, project, command).returncode == 0


def test_hook_blocks_a_commit_when_check_fails(project):
    (project / "scripts/check").write_text("#!/bin/sh\necho 'tests are red'\nexit 1\n")
    done = call_hook(project, project)
    assert done.returncode == 2
    assert "tests are red" in done.stderr


def test_hook_allows_a_commit_when_check_passes(project):
    (project / "scripts/check").write_text("#!/bin/sh\nexit 0\n")
    assert call_hook(project, project).returncode == 0


def test_hook_checks_the_worktree_it_runs_in(project, tmp_path):
    (project / "scripts/check").write_text("#!/bin/sh\nexit 0\n")
    commit_all(project)
    worktree = tmp_path / "wt"
    git(project, "worktree", "add", "-q", str(worktree))
    (worktree / "scripts/check").write_text("#!/bin/sh\nexit 1\n")
    assert call_hook(project, worktree).returncode == 2


def test_update_brings_template_changes_and_keeps_project_files(project, template):
    (project / "AGENTS.md").write_text("# Project notes\n")
    (project / "scripts/check").write_text("#!/bin/sh\necho custom\n")
    commit_all(project)

    workflow = template / "template/docs/agents/workflow.md.jinja"
    workflow.write_text(workflow.read_text() + "\nNew harness rule.\n")
    (template / "template/AGENTS.md.jinja").write_text("# overwritten\n")
    commit_all(template)
    git(template, "tag", "v1.1.0")

    run(sys.executable, "-m", "copier", "update", "--defaults", "--conflict=inline", cwd=project)
    assert (project / "AGENTS.md").read_text() == "# Project notes\n"
    assert "custom" in (project / "scripts/check").read_text()
    assert "New harness rule." in (project / "docs/agents/workflow.md").read_text()
