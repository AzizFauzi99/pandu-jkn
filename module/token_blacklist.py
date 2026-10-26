import time

# Penyimpanan sementara di memori: jti token -> waktu kedaluwarsa (epoch detik).
# Ganti isi fungsi-fungsi di bawah dengan tabel database setelah skema tersedia.
_revoked: dict[str, float] = {}


def _purge_expired() -> None:
    now = time.time()
    for jti in [j for j, exp in _revoked.items() if exp <= now]:
        del _revoked[jti]


def revoke(jti: str, expires_at: float) -> None:
    _purge_expired()
    _revoked[jti] = expires_at


def is_revoked(jti: str) -> bool:
    return jti in _revoked
