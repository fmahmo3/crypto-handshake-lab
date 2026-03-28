"""API route handlers for the crypto handshake lab.

Session state lives in a module-level dict — fine for a demo/lab, not for
production (no persistence, not safe across workers).
"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from crypto_engine.handshake import (
    DEFAULT_MESSAGE,
    Handshake,
    HandshakeComplete,
)

router = APIRouter(prefix="/handshake", tags=["handshake"])

# In-memory session store: session_id -> Handshake instance
_sessions: dict[str, Handshake] = {}


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class StartRequest(BaseModel):
    """Optional body for POST /handshake/start."""

    plaintext: str = DEFAULT_MESSAGE


class TamperRequest(BaseModel):
    """Optional body for POST /handshake/{session_id}/tamper (reserved for future options)."""

    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_session(session_id: str) -> Handshake:
    """Return the Handshake for *session_id* or raise 404."""
    h = _sessions.get(session_id)
    if h is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found. Start a new one with POST /handshake/start.",
        )
    return h


def _session_meta(session_id: str, h: Handshake) -> dict[str, Any]:
    """Common session metadata included in most responses."""
    return {
        "session_id": session_id,
        "current_step": h.current_step,
        "total_steps": h.TOTAL_STEPS,
        "is_complete": h.is_complete(),
        "tamper_mode": h.tamper_mode,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/start", summary="Create a new handshake session")
def start_handshake(body: StartRequest = StartRequest()) -> dict[str, Any]:
    """Create a new handshake session and return its ID.

    The session starts at step 0 (no steps executed). Call ``/advance`` to
    walk through steps one at a time, or ``/full`` to run all steps at once.

    - **plaintext**: The message Alice will encrypt for Bob. Defaults to a
      demo string; supply your own to see it flow through the handshake.
    """
    session_id = str(uuid.uuid4())
    _sessions[session_id] = Handshake(plaintext=body.plaintext)
    h = _sessions[session_id]
    return {
        **_session_meta(session_id, h),
        "plaintext": h.plaintext,
        "message": (
            "Session created. Call POST /handshake/{session_id}/advance to execute "
            "steps one at a time, or GET /handshake/{session_id}/full to run all steps."
        ),
    }


@router.post("/{session_id}/advance", summary="Execute the next handshake step")
def advance_step(session_id: str) -> dict[str, Any]:
    """Execute the next step in the handshake and return its data.

    Steps are numbered 1–9. Each response includes the full step record
    (name, description, party, values) plus updated session metadata.

    Returns HTTP 400 if all steps have already been executed.
    """
    h = _get_session(session_id)
    try:
        step = h.advance()
    except HandshakeComplete as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        **_session_meta(session_id, h),
        "step": step,
    }


@router.get("/{session_id}/step/{step_number}", summary="Retrieve a completed step")
def get_step(session_id: str, step_number: int) -> dict[str, Any]:
    """Return the recorded data for a previously executed step.

    - **step_number**: 1-based step index (1–9).

    Returns HTTP 404 if the step has not been executed yet.
    """
    h = _get_session(session_id)
    try:
        step = h.get_step(step_number)
    except IndexError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {
        "session_id": session_id,
        "current_step": h.current_step,
        **step,
    }


@router.post("/{session_id}/tamper", summary="Enable tamper mode for this session")
def enable_tamper(session_id: str) -> dict[str, Any]:
    """Enable tamper mode — the ciphertext will be corrupted before step 9.

    When step 9 runs, the first byte of the ciphertext is XOR-flipped before
    HMAC verification. This causes the integrity check to fail and decryption
    to be aborted, demonstrating how authenticated encryption detects attacks.

    Tamper mode must be enabled before step 9 is executed.  Returns HTTP 400
    if the handshake is already complete.
    """
    h = _get_session(session_id)
    if h.current_step >= h.TOTAL_STEPS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot enable tamper mode after the final step has already been "
                "executed. Start a new session with POST /handshake/start."
            ),
        )
    h.enable_tamper()
    return {
        **_session_meta(session_id, h),
        "message": (
            "Tamper mode enabled. When step 9 runs, the first byte of the ciphertext "
            "will be flipped (XOR 0xFF) before HMAC verification, causing it to fail."
        ),
    }


@router.get("/{session_id}/full", summary="Run all remaining steps and return the full transcript")
def get_full_handshake(session_id: str) -> dict[str, Any]:
    """Execute all remaining steps and return the complete handshake transcript.

    If some steps have already been executed (e.g. you advanced to step 3
    manually), only the remaining steps are run. The response always contains
    all nine steps.

    This is the fastest way to get a complete handshake for display — useful
    for the initial frontend load or for resetting the demo.
    """
    h = _get_session(session_id)
    steps = h.run_all()
    return {
        **_session_meta(session_id, h),
        "plaintext": h.plaintext,
        "steps": steps,
    }
