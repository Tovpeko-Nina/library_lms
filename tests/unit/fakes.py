from contextlib import contextmanager


class FakeCursor:
    def __init__(self, result=None):
        self.result = result

    def fetchone(self):
        if isinstance(self.result, list):
            return self.result[0] if self.result else None
        return self.result

    def fetchall(self):
        if self.result is None:
            return []
        if isinstance(self.result, list):
            return self.result
        return [self.result]


class ScriptedDatabase:
    """Small deterministic DB double for service-level unit tests."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((" ".join(query.split()), params))
        if not self.responses:
            raise AssertionError(f"Не задан ответ для SQL-вызова: {query}")
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return FakeCursor(response)

    def assert_finished(self):
        assert self.responses == [], f"Не использованы ответы БД: {self.responses!r}"


def install_database(monkeypatch, module, responses):
    database = ScriptedDatabase(responses)

    @contextmanager
    def fake_get_db():
        yield database

    monkeypatch.setattr(module, "get_db", fake_get_db)
    return database
