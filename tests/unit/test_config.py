import pytest

from app.core.config import env_flag

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_env_flag_accepts_true_values(monkeypatch, value):
    monkeypatch.setenv("FEATURE_FLAG", value)

    assert env_flag("FEATURE_FLAG") is True


@pytest.mark.parametrize("value", ["0", "false", "no", "off", "unexpected"])
def test_env_flag_treats_other_values_as_false(monkeypatch, value):
    monkeypatch.setenv("FEATURE_FLAG", value)

    assert env_flag("FEATURE_FLAG", default=True) is False


def test_env_flag_uses_default_when_variable_is_missing(monkeypatch):
    monkeypatch.delenv("FEATURE_FLAG", raising=False)

    assert env_flag("FEATURE_FLAG", default=True) is True
