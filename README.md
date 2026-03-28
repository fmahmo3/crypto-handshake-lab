# Crypto Handshake Lab

> A step-by-step visual walkthrough of a TLS-style cryptographic handshake — Diffie-Hellman key exchange, AES-GCM encryption, and HMAC-SHA256 message authentication — with an interactive tamper mode that lets you break the handshake and watch integrity verification fail in real time.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

---

## What You'll Learn

| Concept | What the lab shows |
|---|---|
| **Diffie-Hellman key exchange** | Alice and Bob derive the same shared secret over an insecure channel without ever transmitting it |
| **HKDF key derivation** | Why raw DH output can't be used directly — and how HKDF-SHA256 stretches it into two independent keys |
| **AES-256-GCM authenticated encryption** | How a random nonce + authentication tag protect both confidentiality and integrity |
| **HMAC-SHA256 message authentication** | How the MAC binds the ciphertext to the shared key so only the intended recipient can verify it |
| **Tamper mode** | What happens when a single bit of the ciphertext is flipped in transit — the HMAC check fails and decryption is aborted |

---

## Architecture

```
┌─────────────┐        HTTP/JSON         ┌──────────────────┐
│             │ ──── POST /handshake ──▶ │                  │
│    React    │       /advance etc.      │  FastAPI Backend │
│  Frontend   │ ◀─── step data + meta ── │                  │
│  (Vite)     │                          │  ┌─────────────┐ │
└─────────────┘                          │  │Crypto Engine│ │
      ▲                                  │  │  DH · HKDF  │ │
      │ browser                          │  │AES-GCM·HMAC │ │
      │                                  │  └─────────────┘ │
 User clicks                             └──────────────────┘
 "Next Step"
```

In Docker, nginx proxies `/api/*` requests from the frontend container to the backend container. In development, Vite's built-in dev-server proxy handles the same routing.

---

## Quick Start

### 1. Docker (recommended)

```bash
git clone https://github.com/your-username/crypto-handshake-lab.git
cd crypto-handshake-lab
docker compose up --build
```

Open **http://localhost:3000** — the full lab is running.

### 2. Manual (two terminals)

**Terminal 1 — Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn api.main:app --reload
# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

**Terminal 2 — Frontend**

```bash
cd frontend
npm install
npm run dev
# UI available at http://localhost:5173
```

### 3. Backend only (curl)

```bash
cd backend
pip install -e .
uvicorn api.main:app

# Start a session
SESSION=$(curl -s -X POST http://localhost:8000/handshake/start | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")

# Walk through all 9 steps
for i in $(seq 1 9); do
  curl -s -X POST http://localhost:8000/handshake/$SESSION/advance | python3 -m json.tool
done

# Enable tamper mode (run before step 9 to see HMAC failure)
curl -s -X POST http://localhost:8000/handshake/$SESSION/tamper

# Or run the whole handshake in one shot
curl -s http://localhost:8000/handshake/$SESSION/full | python3 -m json.tool
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/handshake/start` | Create a new session. Optional JSON body: `{"plaintext": "your message"}` |
| `POST` | `/handshake/{id}/advance` | Execute the next step and return its data |
| `GET`  | `/handshake/{id}/step/{n}` | Retrieve a previously executed step (1-based) |
| `POST` | `/handshake/{id}/tamper` | Enable tamper mode — flips `ciphertext[0] ^ 0xFF` before step 9 |
| `GET`  | `/handshake/{id}/full` | Run all remaining steps and return the full transcript |

Full interactive docs: **http://localhost:8000/docs**

---

## Project Structure

```
crypto-handshake-lab/
├── docker-compose.yml           # Runs backend + frontend together
├── README.md
├── LICENSE
│
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── pyproject.toml           # Package definition + dependencies
│   ├── api/
│   │   ├── main.py              # FastAPI app + CORS
│   │   └── routes.py            # Endpoint handlers + session store
│   └── src/
│       └── crypto_engine/
│           ├── primitives.py    # DH, AES-GCM, HMAC, HKDF functions
│           ├── parties.py       # Alice / Bob Party dataclass
│           └── handshake.py     # 9-step Handshake state machine
│
├── frontend/
│   ├── Dockerfile               # Multi-stage: node build + nginx serve
│   ├── .dockerignore
│   ├── nginx.conf               # Proxy /api/* → backend, gzip, SPA routing
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── utils/api.js         # Axios client
│       ├── hooks/useHandshake.js
│       └── components/
│           ├── HandshakeViewer.jsx
│           ├── StepCard.jsx
│           ├── PartyColumn.jsx
│           ├── HexInspector.jsx
│           ├── TamperToggle.jsx
│           ├── ConnectionLine.jsx
│           ├── KeyExchangeAnim.jsx
│           ├── EncryptionAnim.jsx
│           └── HmacAnim.jsx
│
└── .github/
    └── workflows/
        └── ci.yml               # ruff + pytest · eslint + vite build
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Crypto | Python `cryptography` — DH RFC 3526 Group 14, AES-256-GCM, HMAC-SHA256, HKDF-SHA256 |
| API | FastAPI + uvicorn |
| Frontend | React 18 + Vite 5 + Tailwind CSS 3 + Axios |
| Serving | nginx (production) / Vite dev server (development) |
| Containers | Docker + Docker Compose |
| CI | GitHub Actions |

---

## License

MIT — see [LICENSE](LICENSE).
