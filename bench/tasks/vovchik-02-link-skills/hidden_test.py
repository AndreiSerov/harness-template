"""Hidden tests for ticket 02 (`scripts/link-skills`) of vovchik-furniture-kit.

Written from the reviewer's findings on the first hand-back (b9a606d), through the ticket's own
interface: `scripts/link-skills`, `scripts/doctor` and the files they write. They fail on
b9a606d and pass on d969798, the ticket's final fix.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PLACES = (".claude/skills", ".agents/skills", ".qwen/skills")


@pytest.fixture
def repo(tmp_path):
    """A copy of the repo with its own git, so the scripts act on it and not on REPO."""
    copy = tmp_path / "repo"
    shutil.copytree(
        REPO, copy, symlinks=True, ignore=shutil.ignore_patterns(".git", ".venv", "*cache*")
    )
    subprocess.run(["git", "init", "-q"], cwd=copy, check=True)
    for place in PLACES:
        for link in (copy / place).glob("kitchen-*") if (copy / place).is_dir() else []:
            if link.is_symlink():
                link.unlink()
    return copy


def run(repo, *args, home=None):
    env = {**os.environ, "HOME": str(home or repo / "fake-home")}
    return subprocess.run(
        [sys.executable, *args], cwd=repo, env=env, capture_output=True, text=True, check=False
    )


def link_skills(repo, *args, home=None):
    return run(repo, "scripts/link-skills", *args, home=home)


def doctor(repo):
    done = run(repo, "scripts/doctor")
    return done.returncode, done.stdout + done.stderr


def test_links_appear_in_every_place_and_point_at_the_skill(repo):
    assert link_skills(repo).returncode == 0
    for place in PLACES:
        link = repo / place / "kitchen-brief"
        assert link.is_symlink(), place
        assert (link / "SKILL.md").is_file(), place
        assert not os.path.isabs(os.readlink(link)), place


def test_rerun_changes_nothing(repo):
    link_skills(repo)
    link = repo / ".claude/skills/kitchen-brief"
    before = (os.readlink(link), os.lstat(link).st_mtime_ns)
    assert link_skills(repo).returncode == 0
    assert (os.readlink(link), os.lstat(link).st_mtime_ns) == before


def test_agent_folders_are_gitignored(repo):
    for folder in (".agents/", ".qwen/"):
        done = subprocess.run(["git", "check-ignore", "-q", folder], cwd=repo, check=False)
        assert done.returncode == 0, folder


def test_real_folder_in_the_way_is_kept_and_reported(repo):
    blocker = repo / ".agents/skills/kitchen-brief"
    blocker.mkdir(parents=True, exist_ok=True)
    (blocker / "mine.txt").write_text("keep\n")
    assert link_skills(repo).returncode != 0
    assert (blocker / "mine.txt").read_text() == "keep\n"


def test_foreign_symlink_is_left_alone(repo, tmp_path):
    outside = tmp_path / "outside-skill"
    outside.mkdir()
    (outside / "SKILL.md").write_text("# other\n")
    place = repo / ".qwen/skills"
    place.mkdir(parents=True, exist_ok=True)
    (place / "kitchen-brief").symlink_to(outside)
    link_skills(repo)
    assert os.readlink(place / "kitchen-brief") == str(outside)


def test_own_link_to_a_removed_skill_is_cleaned_up(repo):
    link_skills(repo)
    dangling = repo / ".claude/skills/kitchen-old"
    dangling.symlink_to("../../skills/kitchen-old")
    assert link_skills(repo).returncode == 0
    assert not dangling.is_symlink()


def test_hermes_goes_to_the_fake_home_with_absolute_targets(repo, tmp_path):
    home = tmp_path / "home"
    assert link_skills(repo, "--hermes", home=home).returncode == 0
    link = home / ".hermes/skills/kitchen-brief"
    assert link.is_symlink()
    assert os.path.isabs(os.readlink(link))


def test_doctor_reports_a_link_to_a_removed_skill(repo):
    """Review finding (major): doctor said "Harness OK" for a link whose skill was removed."""
    link_skills(repo)
    _, clean = doctor(repo)
    assert "kitchen-old" not in clean
    for place in (".claude/skills", ".agents/skills"):
        (repo / place / "kitchen-old").symlink_to("../../skills/kitchen-old")
    code, out = doctor(repo)
    assert code != 0
    assert "kitchen-old" in out


def test_doctor_reports_a_real_folder_in_the_way(repo):
    """Review finding (minor): doctor missed, or misdescribed, a real folder at a link's place."""
    link_skills(repo)
    link = repo / ".agents/skills/kitchen-brief"
    link.unlink()
    link.mkdir()
    code, out = doctor(repo)
    assert code != 0
    assert "kitchen-brief" in out


def test_doctor_reports_own_link_to_the_wrong_skill(repo):
    """Re-review finding (minor): a link of ours pointing at another skill passed the check."""
    other = repo / "skills/kitchen-zz"
    other.mkdir()
    (other / "SKILL.md").write_text("# zz\n")
    link_skills(repo)
    link = repo / ".claude/skills/kitchen-brief"
    link.unlink()
    link.symlink_to("../../skills/kitchen-zz")
    code, out = doctor(repo)
    assert code != 0
    assert "kitchen-brief" in out
