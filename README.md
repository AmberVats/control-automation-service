# Control Automation Service

[![CI Pipeline](https://github.com/AmberVats/control-automation-service/actions/workflows/ci.yml/badge.svg)](https://github.com/AmberVats/control-automation-service/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red.svg)
![Tests](https://img.shields.io/badge/pytest-55%20passed-success.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

> **Enterprise financial control automation microservice** developed for **Product Control Analytics**. Exposes declarative reconciliation, tolerance variance, and data quality routines as versioned REST endpoints within a **Citizen Developer framework**, backed by immutable SQL audit trails, HTML executive reporting, and an Excel/VBA client for business users.

---

## 📚 Table of Contents
- [🏛️ System Architecture](#️-system-architecture)
- [🌟 Key Capabilities](#-key-capabilities)
- [🧩 Reusable Component Catalogue](#-reusable-component-catalogue)
- [📝 Declarative Control Specification (YAML)](#-declarative-control-specification-yaml)
- [🚀 Local Machine Setup Guide (From Git)](#-local-machine-setup-guide-from-git)
- [📡 REST API Reference](#-rest-api-reference)
- [📊 Excel / VBA Client Integration](#-excel--vba-client-integration)
- [📄 Executive HTML Reporting Engine](#-executive-html-reporting-engine)
- [🗄️ SQL Audit Views & Relational Schema](#️-sql-audit-views--relational-schema)
- [🐳 Docker Deployment](#-docker-deployment)
- [🧪 Testing & CI/CD](#-testing--cicd)
- [📖 Detailed Documentation](#-detailed-documentation)

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Clients["1. Business Clients & Triggers"]
        VBA["Excel / VBA Client\n(ControlRunner.xlsx + .bas)"]
        HTTP["Automated Triggers / CI-CD / API"]
        CRON["Background Cron Scheduler\n(src.scheduler.cron)"]
        HTMLDoc["Documentation & Reports\n(docs/architecture_and_overview.html)"]
    end

    subgraph Service["2. FastAPI Control Microservice (/api/v1)"]
        API["FastAPI App\n(src.main:app)"]
        Loader["YAML Spec Loader & Validator\n(src.engine.loader)"]
        Registry["Component Registry\n(src.components.registry)"]
        Executor["Control Execution Engine\n(src.engine.executor)"]
        Audit["Audit & Exception Logger\n(src.engine.audit)"]
        Reporter["HTML Reporting Engine\n(src.report.html_report)"]
    end

    subgraph Components["3. Reusable Control Component Suite"]
        C1["reconciliation.two_way_match\n(Composite keys, tolerances)"]
        C2["tolerance.threshold_check\n(Variance limits)"]
        C3["quality.completeness\n(Null, missing, blank checks)"]
        C4["quality.referential_integrity\n(Orphan foreign key checks)"]
        C5["quality.staleness\n(Data freshness & timestamps)"]
    end

    subgraph Persistence["4. Relational Persistence & SQL Views"]
        DB[(Database: SQLite / PostgreSQL)]
        T1["controls & control_runs"]
        T2["control_exceptions"]
        V1["v_control_run_history\nv_recent_exceptions\nv_control_summary"]
    end

    VBA -->|HTTP POST/GET| API
    HTTP -->|HTTP POST/GET| API
    CRON -->|Executes DB Controls| Executor

    API --> Loader
    Loader --> Executor
    Registry --> Executor

    C1 --> Registry
    C2 --> Registry
    C3 --> Registry
    C4 --> Registry
    C5 --> Registry

    Executor --> Audit
    Executor --> Reporter
    Audit --> DB
    DB --> T1
    DB --> T2
    DB --> V1
```

---

## 🌟 Key Capabilities

1. **Citizen Developer Framework**: Business users and Product Control analysts configure complex financial controls purely through declarative **YAML specifications**—no Python code changes required.
2. **Deterministic Versioning & Config Hashing**: Every control definition is hashed via **SHA-256**. Changes over quarters/years are auditable down to the exact configuration that produced a historical result.
3. **Reusable Component Suite**: Plug-and-play components for 2-way reconciliations, threshold tests, data completeness, foreign-key integrity, and feed staleness.
4. **Enterprise REST API**: Versioned FastAPI endpoints (`/api/v1/controls`, `/api/v1/runs`, `/api/v1/components`, `/metrics`).
5. **VBA / Excel Integration**: Thin Excel `.xlsx` client using `MSXML2.ServerXMLHTTP` and JSON parsing. Business users interact with controls via a familiar spreadsheet interface while all business logic remains centralized, version-controlled, and audited server-side.
6. **Executive HTML Reporting**: Live `/api/v1/runs/{run_id}/report.html` endpoint and file generator with zero external dependencies.
7. **Immutable Audit Trail & SQL Views**: Every execution records row counts, execution duration, status (`PASS`, `BREACH`, `FAIL`), and row-level breach records with SQL views (`v_control_run_history`, `v_control_summary`).

---

## 🧩 Reusable Component Catalogue

| Component Name | Category | Description | Key Parameters |
|---|---|---|---|
| `reconciliation.two_way_match` | Reconciliation | 2-way dataset matching across composite keys with absolute and relative field tolerances. | `source`, `target`, `keys`, `compare`, `tolerance` |
| `tolerance.threshold_check` | Tolerance | Compares expected vs actual numerical values within specified tolerance. | `expected`, `actual`, `tolerance` |
| `quality.completeness` | Quality | Detects missing fields, `NULL` values, or empty strings in mandatory attributes. | `data`, `required_fields`, `allow_empty_string` |
| `quality.referential_integrity` | Quality | Verifies that foreign keys in child datasets exist in parent master datasets. | `source`, `lookup`, `foreign_key`, `primary_key` |
| `quality.staleness` | Quality | Validates that feed timestamps or as-of dates do not exceed maximum age thresholds. | `data`, `timestamp_field`, `as_of_date`, `max_age_days` |

---

## 📝 Declarative Control Specification (YAML)

Non-developers create control files in `controls/`:

```yaml
# controls/eod_position_break.yaml
name: eod_position_break
version: 2
component: reconciliation.two_way_match
description: End-of-Day position reconciliation between Risk System and Core Books & Records.
owner: product_control_analytics
schedule: "0 18 * * 1-5"
enabled: true

source:
  type: query_file
  query_file: queries/risk_positions.sql

target:
  type: query_file
  query_file: queries/books_positions.sql

keys:
  - as_of_date
  - instrument_id
  - book

compare:
  - quantity
  - market_value

tolerance:
  quantity:
    absolute: 0.0
  market_value:
    absolute: 50.0
    relative: 0.0001

notify:
  on_breach:
    - pc-analytics-alerts@globalmarkets.com
```

---

## 🚀 Local Machine Setup Guide (From Git)

Follow these step-by-step instructions to clone, set up, and run the service on your local machine.

### Prerequisites
- **Python 3.12+** installed
- **Git** installed

### Step 1: Clone the Repository
```bash
git clone https://github.com/AmberVats/control-automation-service.git
cd control-automation-service
```

### Step 2: Set Up Python Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Seed Demo Financial Database
Populate the local SQLite database with realistic trades, positions, market prices, and intentional break anomalies:
```bash
python -m data.seed_demo_data
```

### Step 5: Start the FastAPI Microservice
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Once running, access:
* **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Component Catalogue:** [http://localhost:8000/api/v1/components](http://localhost:8000/api/v1/components)
* **Service Metrics:** [http://localhost:8000/metrics](http://localhost:8000/metrics)
* **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 📡 REST API Reference

### 1. Register / Update a Control
```bash
curl -X POST http://localhost:8000/api/v1/controls \
  -H "Content-Type: application/json" \
  -d '{"yaml_content": "name: price_check\nversion: 1\ncomponent: tolerance.threshold_check\nparameters:\n  expected: 100\n  actual: 105\n  tolerance: 2"}'
```

### 2. List Registered Controls
```bash
curl -X GET http://localhost:8000/api/v1/controls
```

### 3. Execute a Control
```bash
curl -X POST http://localhost:8000/api/v1/controls/eod_position_break/run \
  -H "Content-Type: application/json" \
  -d '{"as_of_date": "2026-08-15", "triggered_by": "manual_trigger"}'
```

### 4. Fetch Run Exceptions
```bash
curl -X GET http://localhost:8000/api/v1/runs/{run_id}/exceptions?limit=50
```

### 5. View Executive HTML Report
```
http://localhost:8000/api/v1/runs/{run_id}/report.html
```

---

## 📊 Excel / VBA Client Integration

The repository includes a ready-to-use Excel client interface (`excel_client/ControlRunner.xlsx`) and exported `.bas` modules in `excel_client/modules/`:

- `ControlClient.bas`: Handles asynchronous HTTP calls to `/api/v1/controls` and `/api/v1/runs`.
- `JsonConverter.bas`: Native VBA parser for JSON arrays and nested dictionaries.
- `SheetFormatter.bas`: Styles exception and history sheets in Global Markets Product Control formatting.

---

## 📄 Executive HTML Reporting Engine

The service generates corporate HTML exception reports with zero external dependencies:
* **API Endpoint:** `GET /api/v1/runs/{run_id}/report.html`
* **Static File Generator:** `src.report.html_report.generate_html_report_file`
* **Sample Report:** [`reports/report_eod_position_break_2663112b.html`](file:///reports/report_eod_position_break_2663112b.html)

---

## 🗄️ SQL Audit Views & Relational Schema

```sql
-- 1. View full run history with latency and breach metrics
SELECT * FROM v_control_run_history WHERE status = 'BREACH';

-- 2. View recent exception breaches with parent control context
SELECT * FROM v_recent_exceptions LIMIT 20;

-- 3. View aggregate performance summary across all controls
SELECT * FROM v_control_summary;
```

---

## 🐳 Docker Deployment

```bash
# Start microservice, PostgreSQL, and background scheduler
docker-compose up -d --build
```

---

## 🧪 Testing & CI/CD

The test suite contains **55 automated unit, integration, and end-to-end tests** with 0 warnings:

```bash
pytest -v
```

```
============================= test session starts =============================
tests/test_component_base.py ....                                        [ 10%]
tests/test_config.py ....                                                [ 18%]
tests/test_tolerance.py ..                                               [ 22%]
tests/test_two_way_match.py ...                                          [ 28%]
tests/test_quality.py .........                                          [ 45%]
tests/test_registry.py ..........                                        [ 64%]
tests/test_loader.py .....                                               [ 73%]
tests/test_audit.py ..                                                   [ 77%]
tests/test_report.py ..                                                  [ 81%]
tests/test_api.py ....                                                   [ 88%]
tests/test_scheduler.py .                                                [ 90%]
tests/test_end_to_end.py ...                                             [100%]
======================= 55 passed in 1.01s =======================
```

---

## 📖 Detailed Documentation

* **[PROJECT_OVERVIEW_AND_BUILD_GUIDE.md](file:///PROJECT_OVERVIEW_AND_BUILD_GUIDE.md)**: Full business problem statement, architectural breakdown, phase-by-phase build journey, and interview guide.
* **[docs/architecture_and_overview.html](file:///docs/architecture_and_overview.html)**: Interactive HTML architecture and documentation portal.

---

## 📄 License
MIT License. Developed for Global Markets Product Control Analytics Data Engineering.
