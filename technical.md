# Technical Product Requirements Document (TPRD)

> **Product**: *Nova Insights Platform (NIP)*
> **Audience**: Engineering, Data Platform, DevOps, ML, QA
> **Version**: 0.1 (Draft)
> **Date**: 28 Apr 2025
> **Tooling Focus**: Built and maintained primarily via **Cursor** (AI‑native IDE) for code creation, review and pair‑programming.

---

## 1. Purpose
Provide an end‑to‑end, engineering‑level specification for delivering the Nova Insights Platform described in the functional PRD. This document guides implementation inside **Cursor**—every requirement is traceable to a repository path, test, or CI pipeline job.

---

## 2. High‑Level Architecture
```
                    ┌─────────────────────────┐
                    │     Metabase (BI)       │
                    └────────────┬────────────┘
                                 │
                        (JDBC/SQL Queries)
                                 │
┌───────────────┐      ┌─────────▼─────────┐       ┌─────────────────┐
│  Singer Taps  │────► │  BigQuery (DW)   │ ─────► │  Cloud Functions│
│  (Spotify,    │      │  Raw + DataMart  │       │  PitchScore API │
│   Apple …)    │      └─────────┬─────────┘       └─────────────────┘
└───────────────┘                │
          ▲                      │ (dbt)
          │            ┌─────────▼─────────┐
          │            │   GCS Staging     │
          │            └───────────────────┘
          │                    │
          │           (Meltano Orchestration)
          │
┌─────────┴─────────┐
│  Terraform IaC    │
└───────────────────┘
```

---

## 3. Repositories & Branch Strategy
| Repo | Purpose | Default Branch | Branching Model |
|------|---------|---------------|-----------------|
| **nip‑etl** | Singer taps, Meltano project, Dockerfiles | `main` | Trunk‑based; feature branches auto‑merge via Cursor‑generated PR descriptions |
| **nip‑analytics** | dbt project (models + tests + docs) | `main` | Same |
| **nip‑infra** | Terraform modules & env configs | `main` | GitOps; PR environments via Terraform Cloud |
| **nip‑services** | Cloud Functions (Pitch Score, alerts) | `main` | Same |

All repos instrumented with Cursor’s “Continuous Feedback” to auto‑suggest code improvements and inline docstrings.

---

## 4. Detailed Requirements
### 4.1 Data Ingestion
| ID | Requirement | Spec | Acceptance Tests |
|----|-------------|------|------------------|
| **ING‑01** | Nightly pull of Spotify analytics flat‑files | **Singer tap‑spotify‑artists** (custom fork) running in Docker on Cloud Run Jobs | File presence confirmed; row‑count ≠ 0; schema hash matches contract |
| **ING‑02** | Multi‑DSP schema unification | Meltano Mapper transforms -> Parquet files in GCS `staging/raw_{{source}}/dt={{ds}}` | Unit tests in `pytest` verifying column names & types |
| **ING‑03** | Incremental loads | `state.json` per tap; supports bookmarks | Simulated re‑runs load <1 % duplicate rows |

### 4.2 Data Warehouse & Modeling
| ID | Requirement | Spec | Acceptance Tests |
|----|-------------|------|------------------|
| **DW‑01** | Raw tables | Same‑as‑source, partitioned by `ingestion_ts` | BigQuery table exists and partition pruning verified |
| **DW‑02** | DataMart `streams_fact` | Grain: (isrc, dsp, date) | dbt test: `unique+not_null` PK |
| **DW‑03** | Data freshness SLA | < 4 h after DSP file availability | dbt `source_freshness.yml` alerts on breach |
| **DW‑04** | Pitch Score feature table | Latest 30 d artist, playlist & audio features | ML dataset snapshot passes row‑count + null checks |

### 4.3 Machine Learning Service
| ID | Requirement | Spec |
|----|-------------|------|
| **ML‑01** | Model | XGBoost binary classifier predicting `playlist_add` probability (0–1) |
| **ML‑02** | Training cadence | Weekly Cloud Build job → Vertex AI Training |
| **ML‑03** | Serving | Cloud Functions REST endpoint ≤ 250 ms p95 |
| **ML‑04** | Monitoring | Vertex AI Model Monitoring + custom BigQuery logging |

### 4.4 API & Integration
| Endpoint | Method | Auth | Payload | Notes |
|----------|--------|------|---------|-------|
| `/v1/pitch-score` | `POST` | Service Account + JWT | `{ "isrc": "SE7DX2406949" }` | Returns `{ "score": 0.88 }` |
| `/v1/alerts/threshold` | `POST` | Same | `{ "metric":"streams", "value":100000 }` | Creates alert rule |

### 4.5 Dashboarding & Access
- Metabase deployed on GKE Autopilot.
- SSO via Google Identity; row‑level security through BigQuery authorized views.

### 4.6 CI/CD
| Stage | Tool | Trigger |
|-------|------|---------|
| Lint & Unit Tests | `pre‑commit`, `pytest` | Push to PR branch |
| Build & Push Image | Cloud Build | Merge to `main` |
| Terraform Plan & Apply | Terraform Cloud | Merge to `main` (autopruned) |
| dbt Run + CI tests | Cloud Build | Merge to `main` |

Cursor AI comments automatically summarise PR diffs and suggest reviewers.

---

## 5. Non‑Functional Targets
| Attribute | Target |
|-----------|--------|
| Latency (API) | ≤ 250 ms p95 |
| Throughput | 50 K requests/day |
| Data volume | Up to 5 TB/year |
| Uptime | 99.5 % monthly |
| Recovery Time Objective (RTO) | 2 h |

---

## 6. Monitoring & Alerting
| Component | Metrics | Alerts |
|-----------|---------|--------|
| ETL Jobs | Success/Failure, duration | PagerDuty if job fails twice |
| BigQuery | Slot utilisation, query latency | Slack warning at ≥80 % slots |
| ML API | p95 latency, error‑rate | PagerDuty at >1 % 5xx |

---

## 7. Dev‑Env & Tooling Standard (Cursor‑centric)
1. **Cursor IDE** is the canonical environment. All repo setup tasks include a `.cursor.yml` to enforce formatting, tests, and code‑context windows.
2. **Python 3.11** with Poetry for dependency management.
3. **SQLFluff** for dbt SQL linting, auto‑fixed on save via Cursor actions.
4. **Pre‑commit** hooks run Black, isort, ruff.

---

## 8. Migration & Cut‑over Plan
| Step | Action | Owner |
|------|--------|-------|
| 1 | Backfill 18 months of DSP data to BigQuery | Data Eng |
| 2 | Dry‑run dashboards vs. current spreadsheets | Analytics |
| 3 | Parallel‑run for 2 cycles; sign‑off accuracy (±0.5 %) | Finance |
| 4 | Swap Metabase URL; archive legacy sheets | PM |

---

## 9. Open Technical Questions
1. Use **Cloud Composer** vs. **Meltano Scheduled Cloud Run** for orchestration?
2. Do we need multi‑region BigQuery for DR, or is daily export to GCS sufficient?
3. Should Pitch Score training be Vertex AI or in‑warehouse BigQuery ML?
4. Which feature store (if any) do we adopt? (Feast vs. bespoke BigQuery table).

---

_End of Technical PRD_
