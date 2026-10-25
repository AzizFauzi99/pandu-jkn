from fastapi import FastAPI

from router import chat, health, summary

app = FastAPI(
    title="Pandu JKN",
    description="API for JKN Healthkaton",
    version="0.0.1",
)


app.include_router(health.router, prefix="")
app.include_router(chat.router, prefix="/api")
app.include_router(summary.router, prefix="/api")