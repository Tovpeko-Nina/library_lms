"""Автоматическая проверка минимального функционального покрытия ТЗ."""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REQUIREMENT_PATTERN = re.compile(r'pytest\.mark\.requirement\("(FR-\d{2})"\)')
FUNCTIONAL_REQUIREMENTS = {f"FR-{number:02d}" for number in range(1, 28)}


@pytest.mark.requirement("QA-10")
def test_every_functional_requirement_has_an_automated_test():
    test_root = Path(__file__).resolve().parents[1]
    mapped_requirements = set()

    for test_file in test_root.rglob("test_*.py"):
        if test_file == Path(__file__):
            continue
        mapped_requirements.update(
            REQUIREMENT_PATTERN.findall(test_file.read_text(encoding="utf-8"))
        )

    missing = FUNCTIONAL_REQUIREMENTS - mapped_requirements
    assert not missing, f"Нет автоматических тестов для требований: {sorted(missing)}"
