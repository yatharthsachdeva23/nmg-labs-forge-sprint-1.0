# CLAUDE.md — Project Memory: SEO Command Center

This file serves as the central context and architectural guide for the SEO Command Center. It outlines the project's purpose, architecture, core rules, and environment requirements.

## 🎯 Project Goal
A Claude Code plugin that automates the audit of Screaming Frog SEO exports. It detects issues deterministically, prioritizes them via a model-driven engine, provides fixes (rewriting titles/redirects), and surfaces findings through a live dashboard (localhost:7700) and a final HTML/JSON report.

## 🏗️ Architecture
The system is divided into three primary layers:

### 1. Detection Layer (`seo/`)
- **`detector.py`**: Contains pure Python logic for deterministic SEO issue detection. It processes `internal_all.csv` and identifies violations based on a fixed rulebook.

### 2. Orchestration & Interface Layer (`mcp/`)
- **`server.py`**: A dual-purpose server providing:
  - **MCP Tools**: Exposes tools (`load`, `detect_issues`, `set_fixes`, `recommend`, `write_report`, `export_report`) to Claude Code.
  - **Live Dashboard**: Hosts an SSE-powered cockpit at `http://localhost:7700` to track the audit in real-time.

### 3. Execution & Reporting Layer
- **`run.py`**: Entry point for executing the full pipeline.
- **`skills/seo-audit/`**: Contains the high-level orchestration logic (`SKILL.md`).
- **`agents/`**: Defines the personas for the `ingest`, `auditor`, `fixer`, and `reporter` agents.
- **`outputs/`**: Stores the final deliverables: `report.json` (validated against schema) and `report.html`.

## 📏 Core Deterministic SEO Rules
The `seo/detector.py` module implements 17 core rules across five dimensions:

| Dimension | Rule | Severity | Logic / Threshold |
| :--- | :--- | :--- | :--- |
| **Titles** | `missing_title` | High | No title tag on indexable 200 pages |
| | `duplicate_title` | High | Identical title tags across multiple pages |
| | `title_too_long` | Medium | > 561px or > 60 characters |
| | `title_too_short` | Low | 0 < Length < 30 characters |
| **Meta Descs**| `missing_meta_description` | Medium | No meta description on indexable 200 pages |
| | `duplicate_meta_description`| Medium | Identical meta descriptions across pages |
| | `meta_description_too_long`| Low | > 155 characters |
| **H1 Tags** | `missing_h1` | Medium | Missing H1 header on 200 pages |
| | `duplicate_h1` | Low | Identical H1 headers across indexable pages |
| **HTTP Status**| `broken_link` | High | Status Code 4xx |
| | `server_error` | High | Status Code 5xx |
| | `redirect` | Medium | Status Code 3xx |
| | `redirect_chain` | High | Multi-hop redirect paths or cycles |
| **Content/Perf**| `orphan_page` | Medium | Indexable page with 0 inlinks |
| | `thin_content` | Low | < 200 words on indexable pages |
| | `slow_page` | Low | Response time > 1.0 second |
| | `non_indexable_but_linked` | Medium | Non-indexable page receiving internal link equity |

## 🛠️ Fixer Logic & Length Guards
The `run_cloud_fixer` in `mcp/server.py` implements critical guards to ensure quota efficiency and SEO compliance:

- **Quota Protection**: To prevent excessive model usage during testing/development, the fixer caps the number of processed URLs to **5 for titles** and **5 for broken links**.
- **Strict Length Guard**: 
  - New titles must be **strictly under 60 characters**.
  - If a generated title exceeds this limit, it is automatically truncated to **57 characters** and appended with an ellipsis (`...`).
- **Batch Efficiency**: Title fixes are processed in a single batch call per set of URLs to minimize compute overhead.

## 💻 Environment & Configuration
- **Python Version**: Verified and locked to **`py -3.12`**.
- **Dependencies**: Requires `mcp` SDK for server functionality.
- **Execution**: Run via `python run.py sample-export/` for end-to-end testing.
- **Dashboard**: Accessible at `http://localhost:7700`.
- **Model**: Defaulting to `gemma4:31b-cloud` for high-reasoning fixes.
