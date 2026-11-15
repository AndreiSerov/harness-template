"""Hidden tests for ticket 33 (input guards), one per finding of the historical reviews that
changes behaviour. Black-box through the API and the CLI, on a copy of the workshop (`home`)."""

import re
from pathlib import Path

import pytest
from kitchen import api
from kitchen.cli import app
from typer.testing import CliRunner

runner = CliRunner()
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PETROV = FIXTURES / "petrov_project.json"
BANNER = "МОК-ДАННЫЕ — НЕ ДЛЯ КЛИЕНТА"


def edit(home, name, old, new):
    path = home / "workshop" / name
    text = path.read_text(encoding="utf-8")
    assert old in text, (name, old)
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def append(home, name, text):
    path = home / "workshop" / name
    path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")


def cli_fails_cleanly(args):
    r = runner.invoke(app, args)
    assert r.exit_code == 1 and isinstance(r.exception, SystemExit), (args, r.exit_code, repr(r.exception))
    assert "Traceback" not in r.output
    return r


# Review 1, Б1: an unhashable YAML key crashed every command with TypeError.
@pytest.mark.parametrize("line", ["[1, 2]: 3\n", "? {a: 1}\n: 3\n"])
def test_unhashable_yaml_key_is_a_load_error(home, line):
    append(home, "labor.yaml", line)
    r = api.check_workshop(home)
    assert not r.valid and any("labor.yaml" in e for e in r.errors)
    cli_fails_cleanly(["check-workshop"])
    cli_fails_cleanly(["cut", "--project", str(PETROV)])


# Review 1, Б2: a YAML merge key was refused as a syntax error.
@pytest.mark.parametrize("extra", ["", ", цена: 2"])
def test_yaml_merge_key_is_accepted(home, extra):
    item = "{<<: {id: zzz, название: x, упаковка: 1, цена: 1, магазин: m}" + extra + "}"
    append(home, "hardware.yaml", f"  - {item}\n")
    r = api.check_workshop(home)
    assert r.valid, r.errors


# Review 1, Б3: the back panel fastening step had no bound (0 divided by zero, -1 gave -30704 screws).
@pytest.mark.parametrize("step", ["0", "-1"])
def test_back_panel_fastening_step_must_be_positive(home, step):
    path = home / "workshop" / "construction.yaml"
    text = path.read_text(encoding="utf-8")
    changed = re.sub(r"крепёж_шаг: \d+", f"крепёж_шаг: {step}", text)
    assert changed != text
    path.write_text(changed, encoding="utf-8")
    r = api.check_workshop(home)
    assert not r.valid and any("construction.yaml" in e and "крепёж_шаг" in e for e in r.errors)
    cli_fails_cleanly(["parts", "--project", str(PETROV)])


# Review 1, Н1: a negative edge allowance gave negative edge metres and labour.
def test_negative_edge_allowance_is_a_load_error(home):
    edit(home, "equipment.yaml", "припуск_на_сторону: 30", "припуск_на_сторону: -100000")
    r = api.check_workshop(home)
    assert not r.valid and any("припуск_на_сторону" in e for e in r.errors)


# Review 1, Н2: negative hardware norms gave negative quantities.
@pytest.mark.parametrize(
    ("old", "new", "key"),
    [
        ("полкодержателей: 4", "полкодержателей: -1", "полкодержателей"),
        ("навесов: 2", "навесов: -1", "навесов"),
    ],
)
def test_negative_hardware_norm_is_a_load_error(home, old, new, key):
    edit(home, "construction.yaml", old, new)
    r = api.check_workshop(home)
    assert not r.valid and any(key in e for e in r.errors)


# Review 1, Н3: an order's output folder that is a file crashed with FileExistsError.
def test_output_folder_that_is_a_file_is_a_clean_error(home):
    api.brief_save("2026-047-petrov", FIXTURES / "petrov_brief.json")
    api.import_project("petrov", PETROV)
    out = home / "orders" / "2026-047-petrov" / "out"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("x", encoding="utf-8")
    cli_fails_cleanly(["cut", "petrov"])


# Review 1, Н6: the kerf warning lost digits of the declared value.
def test_kerf_warning_shows_the_declared_value(home):
    edit(home, "equipment.yaml", "пропил: 4", "пропил: 4.0000001")
    r = api.cut_from_project(PETROV, home)
    assert any("4.0000001" in w for w in r.warnings), r.warnings


# Review 1, Н7: the fractional kerf warning was missing from the estimate, whose sheet count uses it.
def test_kerf_warning_also_in_the_estimate(home):
    edit(home, "equipment.yaml", "пропил: 4", "пропил: 3.2")
    r = api.estimate_from_project(PETROV, home)
    assert any("пропил" in w for w in r.warnings), r.warnings
