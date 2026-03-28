# Crypto Handshake Lab — Backend

Python cryptography engine and REST API for the visual TLS-style handshake lab.

The engine walks through a complete key exchange protocol in nine discrete,
inspectable steps:

| # | Step | Party |
|---|------|-------|
| 1 | DH Parameter Generation | shared |
| 2 | Alice Key Generation | Alice |
| 3 | Bob Key Generation | Bob |
| 4 | Public Key Exchange | shared |
| 5 | Shared Secret Derivation | shared |
| 6 | Key Derivation (HKDF) | shared |
| 7 | Message Encryption (AES-GCM) | Alice |
| 8 | HMAC-SHA256 Signing | Alice |
| 9 | Verification & Decryption | Bob |

Every step returns a rich JSON object with human-readable descriptions and all
intermediate hex values — designed for the React frontend to visualise.

---

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running the server

```bash
uvicorn api.main:app --reload
```

The API is now available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

## Running tests

```bash
pytest                        # all tests
pytest tests/test_primitives.py  # primitives only
pytest tests/test_handshake.py   # handshake orchestrator only
pytest tests/test_api.py         # API endpoints only
pytest -v                     # verbose output
```

---

## API Reference

### `POST /handshake/start`

Create a new handshake session.

**Request body** (optional):
```json
{ "plaintext": "Hello, Bob! This is Alice's secret message." }
```

**Response:**
```json
{
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "current_step": 0,
  "total_steps": 9,
  "is_complete": false,
  "tamper_mode": false,
  "plaintext": "Hello, Bob! This is Alice's secret message.",
  "message": "Session created. Call POST /handshake/{session_id}/advance ..."
}
```

```bash
curl -X POST http://localhost:8000/handshake/start \
  -H "Content-Type: application/json" \
  -d '{"plaintext": "Hello, Bob!"}'
```

---

### `POST /handshake/{session_id}/advance`

Execute the next step and return its data.

**Response:**
```json
{
  "session_id": "3fa85f64-...",
  "current_step": 1,
  "total_steps": 9,
  "is_complete": false,
  "tamper_mode": false,
  "step": {
    "step": 1,
    "name": "DH Parameter Generation",
    "description": "Establish the public Diffie-Hellman parameters...",
    "party": "shared",
    "values": {
      "p": "0xffffffffffffffffc90fdaa2...",
      "p_bits": 2048,
      "g": "0x2",
      "group": "RFC 3526 Group 14 (2048-bit MODP)"
    }
  }
}
```

```bash
SESSION=$(curl -s -X POST http://localhost:8000/handshake/start | jq -r .session_id)

# Advance step by step
curl -X POST http://localhost:8000/handshake/$SESSION/advance
curl -X POST http://localhost:8000/handshake/$SESSION/advance
```

---

### `GET /handshake/{session_id}/step/{step_number}`

Retrieve a previously executed step (1-based).

```bash
curl http://localhost:8000/handshake/$SESSION/step/1
```

Returns `404` if the step has not been executed yet.

---

### `POST /handshake/{session_id}/tamper`

Enable tamper mode. When step 9 runs, the first byte of the ciphertext will be
XOR-flipped before HMAC verification, causing the integrity check to fail and
decryption to be aborted.

Must be called before step 9 is executed.

```bash
SESSION=$(curl -s -X POST http://localhost:8000/handshake/start | jq -r .session_id)
curl -X POST http://localhost:8000/handshake/$SESSION/tamper
curl     http://localhost:8000/handshake/$SESSION/full
```

The final step will show:
```json
{
  "tampered": true,
  "values": {
    "hmac_verified": false,
    "handshake_success": false,
    "decrypted_message": null,
    "error": "HMAC verification failed — message integrity compromised."
  }
}
```

---

### `GET /handshake/{session_id}/full`

Run all remaining steps and return the complete nine-step transcript in one
response. Idempotent — safe to call on an already-complete session.

```bash
SESSION=$(curl -s -X POST http://localhost:8000/handshake/start | jq -r .session_id)
curl http://localhost:8000/handshake/$SESSION/full | jq .
```

**Response:**
```json
{
  "session_id": "3fa85f64-...",
  "current_step": 9,
  "total_steps": 9,
  "is_complete": true,
  "tamper_mode": false,
  "plaintext": "Hello, Bob! This is Alice's secret message.",
  "steps": [ ... ]
}
```

---

## Complete tamper-mode demo (bash)

```bash
BASE=http://localhost:8000

# 1. Start a new session
SESSION=$(curl -s -X POST $BASE/handshake/start | jq -r .session_id)
echo "Session: $SESSION"

# 2. Walk through steps 1–4 manually
for i in 1 2 3 4; do
  echo "--- Step $i ---"
  curl -s -X POST $BASE/handshake/$SESSION/advance | jq '.step.name, .step.values'
done

# 3. Enable tamper mode
curl -s -X POST $BASE/handshake/$SESSION/tamper | jq .message

# 4. Run remaining steps 5–9
curl -s $BASE/handshake/$SESSION/full | jq '.steps[-1].values'
# Expected: hmac_verified: false, handshake_success: false
```

---

## Architecture

```
backend/
├── src/
│   └── crypto_engine/
│       ├── primitives.py   # Pure functions: DH, AES-GCM, HMAC, HKDF
│       ├── parties.py      # Party class (Alice / Bob)
│       └── handshake.py    # Handshake orchestrator — step-by-step state machine
├── api/
│   ├── main.py             # FastAPI app, CORS middleware
│   └── routes.py           # Endpoints + in-memory session store
├── tests/
│   ├── test_primitives.py
│   ├── test_handshake.py
│   └── test_api.py
└── pyproject.toml
```

### Cryptographic choices

| Primitive | Choice | Reason |
|-----------|--------|--------|
| DH group | RFC 3526 Group 14 (2048-bit MODP) | Well-known, ~112-bit security, fast startup |
| KDF | HKDF-SHA256 | Extracts & expands DH output; two independent keys via distinct `info` labels |
| Encryption | AES-256-GCM | Authenticated encryption; GCM tag detects ciphertext tampering |
| MAC | HMAC-SHA256 | Additional integrity layer; binds message to shared secret |

### Session storage

Sessions live in a module-level `dict[str, Handshake]` — intentional for
simplicity. Parts 2 and 3 can swap this for Redis or a proper database if
multi-process/persistent sessions are needed.
