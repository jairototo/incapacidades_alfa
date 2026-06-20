from app.tasks.incapacidad_tasks import auditar_incapacidad_task, enqueue_auditoria_incapacidad


def test_enqueue_calls_delay(monkeypatch):
    called = {}
    monkeypatch.setattr(auditar_incapacidad_task, "delay", lambda iid: called.setdefault("id", iid))
    enqueue_auditoria_incapacidad("abc-123")
    assert called["id"] == "abc-123"
