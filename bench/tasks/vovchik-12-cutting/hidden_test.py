"""Hidden tests for ticket 12 (cutting) of vovchik-furniture-kit.

From the reviews of the first hand-back (499ff2f): a part next to a gap no wider than the kerf
came out larger than its nominal size; the sheet's own trim cut was not checked against the
machine's maximum; a textured sheet material crashed the cut without naming the part. They use
the result contract given in the task prompt, and fail on 499ff2f and pass on 1ab4489.
"""

import json
from pathlib import Path

import pytest
from kitchen import api
from kitchen.errors import KitchenError, OrderError

FIXTURES = Path(__file__).resolve().parent / "fixtures"
KERF, TRIM = 4, 10
# Petrov's 2100 mm tall-unit sides need a sheet at least 2300 long; other sizes vary the layouts.
SHEETS = [(w, h) for w in (2300, 2500, 2800) for h in (900, 1200, 1400, 1600, 1800, 2070)]


def set_sheet(home, size):
    path = home / "workshop/materials.yaml"
    path.write_text(
        path.read_text(encoding="utf-8").replace("лист: [2800, 2070]", f"лист: {list(size)}")
    )


def petrov(home, mutate=lambda p: None):
    project = json.loads((FIXTURES / "petrov_project.json").read_text(encoding="utf-8"))
    mutate(project)
    path = home / "hidden-project.json"
    path.write_text(json.dumps(project, ensure_ascii=False), encoding="utf-8")
    return path


def replay(placements, cuts, size):
    """Plays the cuts; every part must end in a piece of exactly its size.

    The contract leaves open whether the perimeter trim is listed as cuts. If any cut starts on
    the sheet's own edge, the play starts from the whole sheet; otherwise from the working field.
    """
    whole = any(cut.start < TRIM or cut.position < TRIM for cut in cuts)
    pieces = [(0, 0, *size)] if whole else [(TRIM, TRIM, size[0] - TRIM, size[1] - TRIM)]
    for cut in cuts:
        for i, (x0, y0, x1, y1) in enumerate(pieces):
            if cut.direction == "vertical":
                hit = (
                    cut.position < x1
                    and cut.position + KERF > x0
                    and (cut.start, cut.end) == (y0, y1)
                )
            else:
                hit = (
                    cut.position < y1
                    and cut.position + KERF > y0
                    and (cut.start, cut.end) == (x0, x1)
                )
            if hit:
                break
        else:
            pytest.fail(f"cut {cut.number} does not run edge to edge across any piece")
        pieces.pop(i)
        if cut.direction == "vertical":
            halves = [
                (x0, y0, max(x0, cut.position), y1),
                (max(x0, min(cut.position + KERF, x1)), y0, x1, y1),
            ]
        else:
            halves = [
                (x0, y0, x1, max(y0, cut.position)),
                (x0, max(y0, min(cut.position + KERF, y1)), x1, y1),
            ]
        pieces += [h for h in halves if h[2] > h[0] and h[3] > h[1]]
    for pl in placements:
        inside = [
            p
            for p in pieces
            if p[0] <= pl.x and p[1] <= pl.y and pl.x + pl.w <= p[2] and pl.y + pl.h <= p[3]
        ]
        assert len(inside) == 1, pl.part
        piece = inside[0]
        assert (piece[2] - piece[0], piece[3] - piece[1]) == (pl.w, pl.h), (
            f"{pl.part}: piece {piece[2] - piece[0]}x{piece[3] - piece[1]}, part {pl.w}x{pl.h}"
        )


def test_petrov_parts_come_out_at_nominal_size(home):
    result = api.cut_from_project(petrov(home), home)
    for material in result.materials:
        for sheet in material.sheets:
            replay(sheet.placements, sheet.cuts, material.sheet_size)


@pytest.mark.parametrize("size", SHEETS, ids=[f"{w}x{h}" for w, h in SHEETS])
def test_parts_come_out_at_nominal_size_on_other_sheet_formats(home, size):
    """Review S1: with a gap of 1..kerf before a part, no trim cut was made, so the part kept a strip."""
    set_sheet(home, size)
    try:
        result = api.cut_from_project(petrov(home), home)
    except OrderError:
        pytest.skip("a part does not fit this sheet format")
    for material in result.materials:
        for sheet in material.sheets:
            replay(sheet.placements, sheet.cuts, material.sheet_size)


def test_sheet_trim_cut_is_checked_against_the_machine_maximum(home):
    """Review: trimming the sheet itself was not compared with the saw's maximum cut.

    With a 2060 mm maximum, every part-separating cut of Petrov's layout (at most 2050 on the
    2050 mm working field) still fits, but no cut across the whole 2800x2070 sheet does, in any
    order. Trimming the sheet is part of cutting it, so this must be an error. The contract names
    no error class for it, so any project error (`KitchenError`) naming the limit counts.
    """
    path = home / "workshop/equipment.yaml"
    text = path.read_text(encoding="utf-8")
    assert "макс_длина_реза: 3200" in text
    path.write_text(
        text.replace("макс_длина_реза: 3200", "макс_длина_реза: 2060"), encoding="utf-8"
    )
    with pytest.raises(KitchenError, match="2060"):
        api.cut_from_project(petrov(home), home)


def test_textured_sheet_material_names_the_part_that_does_not_fit(home):
    """Re-review N1: a textured HDF crashed the cut without the part's mark."""
    path = home / "workshop/materials.yaml"
    text = path.read_text(encoding="utf-8")
    assert "текстура: false, толщина: 3" in text
    path.write_text(
        text.replace("текстура: false, толщина: 3", "текстура: вдоль 2070, толщина: 3"),
        encoding="utf-8",
    )
    with pytest.raises(OrderError, match="П1-зад"):
        api.cut_from_project(petrov(home), home)


def test_result_is_deterministic(home):
    path = petrov(home)
    assert (
        api.cut_from_project(path, home).model_dump()
        == api.cut_from_project(path, home).model_dump()
    )
