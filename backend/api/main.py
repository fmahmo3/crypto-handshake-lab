"""FastAPI application entry point.

Run from the ``backend/`` directory:

    uvicorn api.main:app --reload

Or with explicit host/port:

    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

app = FastAPI(
    title="Crypto Handshake Lab API",
    description=(
        "Visual TLS-style handshake engine: Diffie-Hellman key exchange, "
        "AES-256-GCM encryption, and HMAC-SHA256 verification — step by step. "
        "Enable tamper mode to watch authentication fail in real time."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow all origins during development so the React frontend (running on a
# different port) can reach the API without CORS errors.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", tags=["meta"], summary="API health / info")
def root():
    """Return basic API metadata and links to the interactive docs."""
    return {
        "name": "Crypto Handshake Lab API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "start": "POST /handshake/start",
            "advance": "POST /handshake/{session_id}/advance",
            "get_step": "GET /handshake/{session_id}/step/{step_number}",
            "tamper": "POST /handshake/{session_id}/tamper",
            "full": "GET /handshake/{session_id}/full",
        },
    }
