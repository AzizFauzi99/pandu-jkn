from utils.db import run_admin


def revoke(jti: str, expires_at: float) -> None:
    """Tandai token sebagai sudah logout. `expires_at` dalam epoch detik."""
    run_admin("DELETE FROM token_blacklist WHERE expires_at <= now()")
    run_admin(
        "INSERT INTO token_blacklist (jti, expires_at) "
        "VALUES (%s, to_timestamp(%s)) ON CONFLICT (jti) DO NOTHING",
        (jti, expires_at),
    )


def is_revoked(jti: str) -> bool:
    rows = run_admin("SELECT 1 FROM token_blacklist WHERE jti = %s", (jti,))
    return bool(rows)
