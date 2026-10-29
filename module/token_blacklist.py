from utils.db import run_admin


def revoke(jti: str, expires_at: float) -> None:
    run_admin("delete from token_blacklist where expires_at <= now()")
    run_admin(
        "insert into token_blacklist (jti, expires_at) values (%s, to_timestamp(%s))",
        (jti, expires_at),
    )


def is_revoked(jti: str) -> bool:
    return bool(run_admin("select 1 from token_blacklist where jti = %s", (jti,)))
