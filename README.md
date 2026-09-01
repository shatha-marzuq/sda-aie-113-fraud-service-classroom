# Fraud Service 
 
A production-grade, containerised fraud-scoring API built on FastAPI, scikit-learn, and
clean architecture principles. This project was developed as the capstone for
**SDAIA Academy's**.
 
**Author:** Shatha Marzuq
 
---
 
## Table of Contents
 
- [Project Description](#project-description)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Setup & Installation](#setup--installation)
- [Running the Service](#running-the-service)
- [Usage / API Reference](#usage--api-reference)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Project Structure](#project-structure)
- [Security & Logging](#security--logging)
- [Training Program Attribution](#training-program-attribution)
---
 
## Project Description
 
**Raqib** is the fraud-scoring capability of a simulated Saudi digital-payments provider.
Given a transaction (amount, merchant category, channel, timestamp), the service returns
a fraud probability and a decision (`ALLOW`, `REVIEW`, or `BLOCK`) using a trained
scikit-learn model wrapped behind a clean, testable service layer.
 
The project demonstrates the full lifecycle of taking an ML model from a research
notebook to a production-ready, containerised, tested, and automated service:
 
1. **Refactor** — messy notebook → clean `src-layout` package
2. **Serve** — FastAPI prediction API with pydantic validation
3. **Containerise** — multi-stage Docker build with health checks
4. **Test** — unit, integration, and model-behaviour test suites
5. **Automate** — CI/CD pipeline with linting and coverage gates
6. **Harden** — typed configuration, secret hygiene, and structured logging
---
 
## Architecture Overview
 
The codebase follows **clean / hexagonal architecture** — dependencies point inward only.
Domain code never imports FastAPI, scikit-learn, or any infrastructure library.
 
```
Entrypoints (FastAPI app, CLI)
        │
        ▼
Adapters / Infrastructure  (SklearnModel, feature store, DB — swappable)
        │
        ▼
Service (use-case)         (FraudScorer: validate → featurise → predict → apply policy)
        │
        ▼
Domain                     (Transaction, RawScore, decision policies — pure Python)
```
 
**Key design decisions:**
- The ML model is treated as an **adapter** behind a `Protocol` (`Model.predict_proba`),
  so it can be swapped (e.g. XGBoost → PyTorch, local file → model registry) without
  touching the service or domain layers.
- Configuration is a **typed, validated contract** (`pydantic-settings`), fail-fast at
  startup rather than failing on the first request.
- Logs are **structured JSON events** correlated by `trace_id`, with sensitive fields
  masked defensively before they ever leave the process.
---
 
## Prerequisites
 
- **Docker Desktop** (with Docker Compose v2) — primary environment
- **Python 3.12+** — only needed for local (non-Docker) development
- **Git**
- *(Optional)* [`gitleaks`](https://github.com/gitleaks/gitleaks) for secret scanning
- *(Optional)* `jq` for querying JSON logs from the command line
No external API keys are required to run this project locally — the ML model artefact
ships with the repository via Git.
 
---
 
## Environment Variables
 
All configuration is read from environment variables prefixed with `FRAUD_`
(validated via `pydantic-settings`). See [`configs/settings.example.env`](configs/settings.example.env)
for the full documented template — **never commit a real `.env` file.**
 
| Variable                 | Required | Default                         | Description                                  |
|---------------------------|:--------:|----------------------------------|-----------------------------------------------|
| `FRAUD_MODEL_PATH`         | No       | `models/fraud_xgb_v3.joblib`     | Path to the joblib model bundle              |
| `FRAUD_BLOCK_THRESHOLD`    | No       | `0.85`                           | Probability threshold for a `BLOCK` decision (0.5–0.99) |
| `FRAUD_LOG_LEVEL`          | No       | `INFO`                           | Logging level                                |
| `FRAUD_GIT_SHA`            | No       | `dev`                            | Injected by CI to tag the running build      |
| `FRAUD_REGISTRY_TOKEN`     | No       | *(none)*                         | Secret token for a model registry (masked in logs) |
 
Copy the example file to get started locally:
 
```bash
cp configs/settings.example.env .env
```
 
---
 
## Setup & Installation
 
### Option A — Docker (recommended)
 
```bash
git clone https://github.com/<your-org>/sda-aie-113-fraud-service-classroom.git
cd sda-aie-113-fraud-service-classroom
docker compose up --build -d
```
 
### Option B — Local Python environment
 
```bash
git clone https://github.com/<your-org>/sda-aie-113-fraud-service-classroom.git
cd sda-aie-113-fraud-service-classroom
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# source .venv/bin/activate       # macOS/Linux
pip install -e .
```
 
---
 
## Running the Service
 
**With Docker:**
 
```bash
docker compose up --build -d
docker compose ps
```
 
**Locally (without Docker):**
 
```bash
uvicorn fraud_service.api.app:app --reload
```
 
The API will be available at `http://localhost:8000`.
 
### Expected output on successful startup
 
```json
{"event": "model_loaded version=v3.2.0 seconds=0.96", "level": "info", "timestamp": "..."}
```
 
---
 
## Usage / API Reference
 
### Health & readiness
 
```bash
curl http://localhost:8000/v1/health
curl http://localhost:8000/v1/ready
```
 
### Score a transaction
 
```bash
curl -X POST http://localhost:8000/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
        "transaction_id": "TXN-TEST-01",
        "amount_sar": 250,
        "merchant_category": "grocery",
        "channel": "pos",
        "timestamp": "2026-09-01T03:30:00Z"
      }'
```
 
**Expected response:**
 
```json
{
  "transaction_id": "TXN-TEST-01",
  "fraud_probability": 0.624946,
  "decision": "ALLOW",
  "model_version": "v3.2.0",
  "trace_id": "ae8896d0-4756-4538-af68-1e86a61cfb9a"
}
```
 
---
 
## Testing
 
```bash
pytest -m "not slow"
```
 
The suite includes:
- **Unit tests** — domain policies and feature engineering
- **Integration tests** — the FastAPI `/v1/predict` contract
- **Behavioural tests** — model invariance and directional-sensitivity checks
Coverage is enforced at a minimum of **80%** and currently sits above **82%**.
 
---
 
## CI/CD Pipeline
 
Every push to `main` triggers a GitHub Actions workflow that:
1. Runs `ruff check` for linting
2. Runs the full `pytest` suite with coverage enforcement
3. Fails the build if either check does not pass
See the **Actions** tab of this repository for the latest pipeline run.
 
---
 
## Project Structure
 
```
fraud-service/
├── pyproject.toml                 # dependencies + tool config
├── Makefile                       # make test / make lint / make image
├── requirements.lock              # pinned dependency versions
├── configs/settings.example.env   # documented config template (no real secrets)
├── INCIDENT.md                    # secret-leak response drill documentation
├── src/
│   └── fraud_service/
│       ├── domain/                # entities.py, policies.py — pure business logic
│       ├── service/                # scorer.py, interfaces.py — use-case orchestration
│       ├── adapters/               # sklearn_model.py — the model as a swappable adapter
│       ├── api/                    # app.py, routes.py, schemas.py — FastAPI entrypoint
│       ├── config.py               # typed, validated settings
│       └── logging_setup.py        # structured JSON logging with secret masking
├── models/                         # versioned model artefact (input, not source)
└── tests/                          # unit/ · integration/ · behavioural/
```
 
---
 
## Security & Logging
 
- Secrets are never committed, never baked into images, and never logged
  (enforced with `pydantic.SecretStr` and defensive log masking).
- `gitleaks` is used to scan the repository for accidentally committed secrets.
- See [`INCIDENT.md`](INCIDENT.md) for the documented secret-leak response procedure.
- Logs are structured JSON, correlated by `trace_id`, and deliberately omit
  personally identifiable information (PDPL-aware logging).
---
 
## Training Program Attribution
 
This project was built as part of **SDA-AIE-113 · Software Engineering Practices for
AI Systems**, delivered under the **AI Engineer Track** at
[**SDAIA Academy**].
 
 
