from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.requirement("SEC-02")
def test_secret_environment_files_are_excluded_from_git_and_docker():
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    dockerignore = (PROJECT_ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()

    assert ".env" in gitignore
    assert ".env.*" in gitignore
    assert ".env" in dockerignore
    assert ".env.*" in dockerignore
