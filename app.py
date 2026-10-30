import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from router import auth, bpjs_status, chat, health, profile, session, summary

app = FastAPI(
    title="Pandu JKN",
    description="API for JKN Healthkaton",
    version="0.0.1",
)

# Origin frontend yang diizinkan (pisahkan dengan koma). Default: semua origin,
# aman karena autentikasi memakai header Authorization, bukan cookie.
_origins = [o.strip() for o in os.getenv("FRONTEND_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health.router, prefix="")
app.include_router(auth.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(summary.router, prefix="/api")
app.include_router(session.router, prefix="/api")
app.include_router(bpjs_status.router, prefix="/api")
