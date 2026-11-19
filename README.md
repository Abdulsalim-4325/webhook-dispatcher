<div align="center">

# 🛡️ Sentinel Event Dispatch Engine
### High-Throughput, At-Least-Once Webhook Delivery & Resilience Platform

[![CI Pipeline](https://github.com/Abdulsalim-4325/webhook-dispatcher/actions/workflows/ci.yml/badge.svg)](https://github.com/Abdulsalim-4325/webhook-dispatcher/actions)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-5.4.0-37814A.svg)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-7.0-DC382D.svg)](https://redis.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*An enterprise-grade, distributed event dispatch engine designed for core API platform infrastructure at Tier-1 Global Capability Centers (Walmart, Target, Stripe/Razorpay) and European engineering standards.*

</div>

---

## 📌 Executive Architecture Summary

Sentinel Dispatcher accepts incoming business events via an asynchronous FastAPI ingestion gate and offloads outbound webhook delivery to a resilient Celery worker pool backed by Redis and PostgreSQL. It enforces **at-least-once delivery guarantees**, zero-trust network boundaries, and dynamic backpressure mitigation.

```
                                  [ CLIENTS ]
                                       │
                      POST /api/v1/events (with Idempotency-Key)
                                       ▼
                       ┌───────────────────────────────┐
                       │   FastAPI Ingestion Layer     │
                       │  - Token Bucket Rate Limiter  │
                       │  - Idempotency Gate (Redis)   │
                       │  - Schema Validation (Pydantic│
                       └───────────────┬───────────────┘
                                       │
                         Writes Event & Delivery State
                                       ▼
                       ┌───────────────────────────────┐
                       │   PostgreSQL (State Store)    │
                       │  - Events & Subscriptions     │
                       │  - Delivery Attempts Log      │
                       │  - Dead-Letter Queue (DLQ)    │
                       └───────────────┬───────────────┘
                                       │
                           Pushes Task to Redis Broker
                                       ▼
                       ┌───────────────────────────────┐
                       │   Redis (Queue / Locks / CB)  │
                       │  - Fair-Share Sub-Queues      │
                       │  - Distributed Locks          │
                       │  - Circuit Breaker Counters   │
                       └───────────────┬───────────────┘
                                       │
                      Worker consumes with Prefetch=1
                                       ▼
                       ┌───────────────────────────────┐
                       │   Celery Async Worker Pool    │
                       │  - Socket SSRF & DNS Pinning  │
                       │  - HMAC-SHA256 Payload Signer │
                       │  - Non-blocking HTTPX Client  │
                       │  - Per-Domain Circuit Breaker │
                       └───────────────┬───────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                │                                             │
      Success (2xx)                            Failure / Timeout / 5xx
                │                                             │
     Mark Delivery DELIVERED                 Retry with Exponential Backoff + Jitter
                                                              │
                                                   Exceeded Max Retries?
                                                              │
                                                   ┌──────────┴──────────┐
                                                  Yes                    No
                                                   │                     │
                                           Transition to DLQ       Re-queue with
                                           (Awaiting Manual         Calculated
                                            Replay / Review)         ETA delay
```

---

## ⚡ Core Engineering Highlights

### 1. Zero-Trust Socket SSRF & DNS-Pinning Protection
Outbound webhook engines are prime vectors for **Server-Side Request Forgery (SSRF)** and **Cloud Metadata Extraction** (`169.254.169.254`). Sentinel validates outbound destinations before issuing requests:
* Blocks loopback (`127.0.0.1`), RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and AWS/GCP/Azure link-local metadata endpoints.
* Validates DNS resolution at the socket layer to neutralize **Time-of-Check to Time-of-Use (TOCTOU) DNS Rebinding** attacks.

### 2. Cryptographic Integrity: HMAC-SHA256 & Replay Defense
Payloads are signed with a destination-specific cryptographic secret using `HMAC-SHA256`:
$$\text{Signature} = \text{HMAC-SHA256}(\text{secret}, \, \texttt{t=} \parallel \text{timestamp} \parallel \texttt{.} \parallel \text{payload})$$
* Transmitted via the `X-Sentinel-Signature` and `X-Sentinel-Timestamp` headers.
* Verifiers enforce a 300-second UNIX timestamp drift tolerance to prevent replay attacks.
* Constant-time comparison (`hmac.compare_digest`) neutralizes side-channel timing attacks.

### 3. Exponential Backoff with Full Jitter
To prevent **Thundering Herd** worker starvation against downstream servers recovering from outages:
$$\text{Sleep} = \text{random}(0.5, \, \min(M, \, B \times 2^{\text{attempt}}))$$
Where $B = 2.0\text{s}$ (base delay) and $M = 60.0\text{s}$ (maximum delay ceiling).

### 4. Celery Worker Pool Starvation Protections
* `worker_prefetch_multiplier = 1`: Prevents a single worker from buffering slow or timing-out HTTP requests, allowing fast tasks to be served immediately by available workers.
* `task_acks_late = True`: Guarantees at-least-once execution if a worker instance crashes mid-delivery.
* Fair queue partitioning across `default`, `retries`, and `dlq`.

### 5. Idempotent Ingestion Gates
Ingested events enforce atomic deduplication using Redis `SET NX EX` locks keyed on `Idempotency-Key` to avoid double-processing during transient client retries.

---

## 📂 Production Folder Hierarchy

```
sentinel-dispatcher/
├── .github/workflows/ci.yml       # GitHub Actions automated lint & test pipeline
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entrypoint, lifespan, and CORS middleware
│   │   ├── api/v1/                # Clean versioned routing (health, events, webhooks, dlq)
│   │   ├── core/                  # Settings, async DB engine, Redis client, SSRF/HMAC security
│   │   ├── models/                # SQLAlchemy ORM models (Event, Subscription, Delivery, DLQ)
│   │   ├── schemas/               # Pydantic v2 validation contracts
│   │   ├── services/              # Domain services (Idempotency, Circuit Breaker, Dispatcher)
│   │   └── workers/               # Celery application, queue configurations, and retry tasks
│   └── tests/                     # Pytest suite (SSRF tests, HMAC tests, health probe tests)
├── frontend/                      # React 18 / Vite dark-mode telemetry dashboard
├── mock-receiver/                 # Standalone target service simulating 200s, 500s, and timeouts
├── docker-compose.yml             # Orchestration for API, Worker, Redis, Postgres, Mock Server
├── Dockerfile                     # Multi-stage optimized production container image
├── pyproject.toml                 # Ruff, Mypy, and Pytest configuration
├── requirements.txt               # Pinned dependencies
├── Makefile                       # Developer command runner (make dev, make test, make lint)
└── .env.example                   # Environment variable template
```

---

## 🚀 Quickstart Guide

### Option A: Local Docker Compose (Recommended)

Start all services (PostgreSQL, Redis, FastAPI, Celery Worker, and Mock Receiver) with one command:

```bash
docker compose up --build -d
```

* **FastAPI Docs:** `http://localhost:8000/docs`
* **Health Probe:** `http://localhost:8000/api/v1/health/live`
* **Mock Receiver:** `http://localhost:9000/health`

### Option B: Bare-Metal Local Development

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Install dependencies
make install

# 3. Run linter and type-checker
make lint

# 4. Run automated test suite
make test

# 5. Start development servers
make dev     # Starts FastAPI on :8000
make worker  # Starts Celery Worker
```

---

## 🧪 Testing & Verification

The test suite covers security invariants, cryptographic signing, and backoff mathematics:

```bash
pytest -v backend/tests
```

```
backend/tests/test_api/test_health.py::test_root_endpoint PASSED
backend/tests/test_api/test_health.py::test_liveness_probe PASSED
backend/tests/test_security/test_ssrf.py::test_ssrf_rejects_loopback PASSED
backend/tests/test_security/test_ssrf.py::test_ssrf_rejects_cloud_metadata PASSED
backend/tests/test_security/test_ssrf.py::test_ssrf_rejects_rfc1918_private_ranges PASSED
backend/tests/test_security/test_ssrf.py::test_ssrf_rejects_unsupported_schemes PASSED
backend/tests/test_security/test_hmac.py::test_hmac_signature_generation_and_verification PASSED
backend/tests/test_security/test_hmac.py::test_hmac_signature_rejects_tampered_payload PASSED
backend/tests/test_security/test_hmac.py::test_hmac_signature_rejects_expired_timestamp PASSED
backend/tests/test_workers/test_retries.py::test_exponential_backoff_jitter_bounds PASSED
```

---

## 📄 License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
