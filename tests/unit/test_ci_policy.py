import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
CODEOWNERS = PROJECT_ROOT / ".github" / "CODEOWNERS"


@pytest.mark.requirement("CI-01")
def test_ci_runs_for_push_pull_request_main_and_merge_queue():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert re.search(r"(?m)^  push:$", workflow)
    assert re.search(r"(?m)^  pull_request:$", workflow)
    assert "branches: [main]" in workflow
    assert re.search(r"(?m)^  merge_group:$", workflow)
    assert re.search(r"(?m)^  workflow_dispatch:$", workflow)


@pytest.mark.requirement("CI-02")
def test_ci_contains_every_mandatory_gate_and_dind_execution():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    required_jobs = {
        "style",
        "tests",
        "migrations",
        "backup",
        "security",
        "container",
        "build",
        "image-scan",
        "required",
        "publish",
    }
    for job in required_jobs:
        assert re.search(rf"(?m)^  {re.escape(job)}:$", workflow), job

    assert workflow.count("uses: ./.github/actions/dind-check") >= 8
    assert "make container-check DOCKER=docker" in workflow
    assert "make test-migration DOCKER=docker" in workflow
    assert "make test-recovery DOCKER=docker" in workflow


@pytest.mark.requirement("SEC-11")
def test_external_actions_are_pinned_to_full_commit_sha():
    workflow_files = list((PROJECT_ROOT / ".github").rglob("*.yml"))
    external_use = re.compile(r"uses:\s+([^\s#]+)")

    for workflow_file in workflow_files:
        for action in external_use.findall(workflow_file.read_text(encoding="utf-8")):
            if action.startswith("./"):
                continue
            assert re.fullmatch(r"[^@]+@[0-9a-f]{40}", action), (
                workflow_file,
                action,
            )


@pytest.mark.requirement("CI-03")
def test_publish_is_sha_tagged_main_only_and_depends_on_required_gate():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "github.ref == 'refs/heads/main'" in workflow
    assert "needs: [required, build, image-scan]" in workflow
    assert "library-lms-ci:${{ github.sha }}" in workflow
    assert "secrets.DOCKERHUB_USERNAME" in workflow
    assert "secrets.DOCKERHUB_TOKEN" in workflow


@pytest.mark.requirement("CI-04")
def test_critical_acceptance_files_have_code_owners():
    owners = CODEOWNERS.read_text(encoding="utf-8")

    for protected_path in (
        "/.github/",
        "/tests/",
        "/Makefile",
        "/pyproject.toml",
        "/pytest.ini",
        "/Dockerfile.ci",
        "/scripts/ci/",
    ):
        assert protected_path in owners

    assert "@Tovpeko-Nina" in owners
    assert "@Alexxxaila" in owners


@pytest.mark.requirement("CI-05")
def test_dind_daemon_is_isolated_and_privileged_explicitly():
    dind = (PROJECT_ROOT / "scripts" / "ci" / "dind.sh").read_text(encoding="utf-8")

    assert "--privileged" in dind
    assert "DOCKER_TLS_CERTDIR=" in dind
    assert "docker:27.5.1-dind-alpine3.21" in dind
    assert "tcp://127.0.0.1:2375" in dind
