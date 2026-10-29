-- Tabel pendukung login/logout dan session. Aman dijalankan ulang.
-- Tidak mengubah tabel `users` (dikelola Database management).

CREATE TABLE IF NOT EXISTS sessions (
    id          text PRIMARY KEY,
    user_email  text NOT NULL
                REFERENCES users (email) ON DELETE CASCADE ON UPDATE CASCADE,
    title       text NOT NULL,
    starred     boolean NOT NULL DEFAULT false,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS sessions_user_updated_idx
    ON sessions (user_email, updated_at DESC);

-- jti token yang sudah logout, disimpan sampai token itu kedaluwarsa.
CREATE TABLE IF NOT EXISTS token_blacklist (
    jti         text PRIMARY KEY,
    expires_at  timestamptz NOT NULL
);
