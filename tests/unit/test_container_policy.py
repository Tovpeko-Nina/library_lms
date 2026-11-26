import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.requirement("CTR-01")
def test_application_image_is_versioned_and_runs_as_non_root():
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

    from_line = next(line for line in dockerfile.splitlines() if line.startswith("FROM "))
    assert ":latest" not in from_line
    assert re.search(r"^FROM python:\d+\.\d+\.\d+-", from_line)
    assert "USER 10001:10001" in dockerfile
    assert "STOPSIGNAL SIGTERM" in dockerfile


@pytest.mark.requirement("CTR-02")
def test_secrets_and_local_artifacts_are_excluded_from_image_context():
    ignored = (PROJECT_ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()

    assert ".env" in ignored
    assert ".env.*" in ignored
    assert "backups" in ignored
    assert "*.dump" in ignored
    assert ".git" in ignored


@pytest.mark.requirement("CTR-03")
def test_compose_keeps_database_private_and_healthchecks_enabled():
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert ":latest" not in compose
    assert compose.count("healthcheck:") == 2
    assert not re.search(r'["\'](?:0\.0\.0\.0:|127\.0\.0\.1:)?5432:5432["\']', compose)
    assert "postgres_data:/var/lib/postgresql/data" in compose
    assert "condition: service_healthy" in compose


@pytest.mark.requirement("CTR-04")
def test_application_container_has_security_and_resource_limits():
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "read_only: true" in compose
    assert "no-new-privileges:true" in compose
    assert "cap_drop:" in compose and "- ALL" in compose
    assert 'cpus: "0.50"' in compose
    assert "mem_limit: 256m" in compose
    assert "pids_limit: 100" in compose
