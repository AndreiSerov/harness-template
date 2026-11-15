"""Hidden tests for ticket 07 (lower templates) of vovchik-furniture-kit.

Rules come from the brief (docs/specs/00-source-brief.md) and from the review of the first
hand-back (6d8bc4f), written through the public API only, so they hold whatever names an
implementer gives to new workshop keys. They fail on 6d8bc4f and pass on ed17f69, the fix.
"""

import json

import pytest
from kitchen import api
from kitchen.errors import OrderError

HINGE = "hinge_71B3550"
WIDTHS = {"base_drawers": 600, "base_bottle": 150, "base_sink": 750, "dishwasher_panel": 450}


def build(home, template, **module):
    project = {
        "order": "2026-047-petrov",
        "ceiling_height": 2700,
        "walls": [
            {
                "label": "A",
                "length": 2800,
                "rows": [
                    {
                        "kind": "lower",
                        "modules": [
                            {
                                "label": "Н1",
                                "template": template,
                                "width": WIDTHS[template],
                                **module,
                            }
                        ],
                    }
                ],
            }
        ],
        "materials": {
            "body": "ldsp_16_white",
            "facades_lower": "mdf_enamel_matt",
            "facades_upper": "mdf_enamel_matt",
            "handles": "handle_profile",
        },
    }
    path = home / "hidden-project.json"
    path.write_text(json.dumps(project, ensure_ascii=False), encoding="utf-8")
    return api.parts_from_project(path, home)


def facades(result):
    return [p for p in result.modules[0].parts if "фасад" in p.name]


@pytest.mark.parametrize("template", sorted(WIDTHS))
def test_template_builds_whole_millimetre_parts_with_unique_marks(home, template):
    parts = build(home, template).modules[0].parts
    assert parts
    assert len({p.id for p in parts}) == len(parts)
    for part in parts:
        for size in (part.length, part.width, part.thickness):
            assert isinstance(size, int) and size > 0, part.id


def test_drawers_have_three_facades_top_140_and_equal_lower(home):
    """Brief: ящики_3_шт: {верхний: 140, остальные: делят остаток поровну}."""
    result = build(home, "base_drawers")
    heights = sorted(min(p.length, p.width) for p in facades(result))
    assert len(heights) == 3
    assert 140 in heights
    lower = [h for h in heights if h != 140] or [140, 140]
    assert len(lower) == 2 and lower[0] == lower[1]
    assert result.hardware.get("tandembox_M_500") == 3
    assert not result.hardware.get(HINGE)


def test_bottle_is_one_pull_out_without_hinges_or_shelf(home):
    result = build(home, "base_bottle")
    assert result.hardware.get("bottle_150") == 1
    assert not result.hardware.get(HINGE)
    assert not any(p.name.startswith("полка") for p in result.modules[0].parts)
    assert len(facades(result)) == 1


def test_dishwasher_panel_is_one_facade(home):
    result = build(home, "dishwasher_panel")
    assert len(facades(result)) == 1
    assert not result.hardware.get(HINGE)


def test_sink_has_two_doors_with_hinges(home):
    result = build(home, "base_sink")
    assert len(facades(result)) == 2
    assert result.hardware.get(HINGE, 0) >= 4


def test_drawers_and_bottle_do_not_depend_on_the_hinge_table(home):
    """Review: templates without hinges failed when the hinge table could not serve them."""
    path = home / "workshop/construction.yaml"
    text = path.read_text(encoding="utf-8")
    assert "[[900, 2], [1600, 3], [2000, 4], [9999, 5]]" in text
    path.write_text(
        text.replace("[[900, 2], [1600, 3], [2000, 4], [9999, 5]]", "[[100, 2]]"), encoding="utf-8"
    )
    for template in ("base_drawers", "base_bottle"):
        assert build(home, template).modules, template


@pytest.mark.parametrize("template", ["base_sink", "base_bottle", "base_drawers"])
def test_shelves_on_a_template_without_shelves_are_refused(home, template):
    """Review: `shelves` was silently ignored by templates that build no shelf."""
    with pytest.raises(OrderError, match="Н1"):
        build(home, template, shelves=2)
