"""Session store.

The `sessions` table is append-only: refreshing a session appends a new row for
the same session_id with version = previous version + 1. `created_at` is stored
with one-second resolution.
"""

ROWS = []


def reset():
    ROWS.clear()


def append_session(session_id, version, token, expires_at, created_at):
    ROWS.append(
        {
            "session_id": session_id,
            "version": version,
            "token": token,
            "expires_at": expires_at,
            "created_at": created_at,
        }
    )


def get_session(session_id):
    rows = [r for r in ROWS if r["session_id"] == session_id]
    if not rows:
        return None
    return max(rows, key=lambda r: r["created_at"])


def refresh(session_id, now):
    """Return the live session, or a 401 payload when it has expired."""
    row = get_session(session_id)
    if row is None:
        return {"status": 404}
    if row["expires_at"] <= now:
        return {"status": 401}
    return {"status": 200, "token": row["token"]}
