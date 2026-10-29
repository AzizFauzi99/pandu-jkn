from module.db import connect


def revoke(jti: str, expires_at: float) -> None:
    """Tandai token sebagai sudah logout. `expires_at` dalam epoch detik."""
    with connect() as conn:
        conn.execute("DELETE FROM token_blacklist WHERE expires_at <= now()")
        conn.execute(
            "INSERT INTO token_blacklist (jti, expires_at) "
            "VALUES (%s, to_timestamp(%s)) ON CONFLICT (jti) DO NOTHING",
            (jti, expires_at),
        )


def is_revoked(jti: str) -> bool:
    with connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM token_blacklist WHERE jti = %s", (jti,)
        ).fetchone()
    return row is not None
