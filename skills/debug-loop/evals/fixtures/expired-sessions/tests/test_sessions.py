import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sessions


def setup_function():
    sessions.reset()


def test_missing_session_is_404():
    assert sessions.refresh("nope", now=100)["status"] == 404


def test_live_session_refreshes():
    sessions.append_session("s1", version=1, token="t1", expires_at=200, created_at=100)
    assert sessions.refresh("s1", now=150)["status"] == 200


def test_expired_session_is_401():
    sessions.append_session("s1", version=1, token="t1", expires_at=120, created_at=100)
    assert sessions.refresh("s1", now=150)["status"] == 401


def test_refreshed_session_uses_new_row():
    sessions.append_session("s1", version=1, token="t1", expires_at=120, created_at=100)
    sessions.append_session("s1", version=2, token="t2", expires_at=400, created_at=130)
    result = sessions.refresh("s1", now=150)
    assert result["status"] == 200
    assert result["token"] == "t2"
