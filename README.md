<div align="center">

# 🛠️ AI IT Operations Assistant

**An AI-powered workspace for IT support teams — explore ticket analytics, investigate individual tickets, and get grounded, safe troubleshooting guidance.**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Gradio](https://img.shields.io/badge/UI-Gradio-F97316?logo=gradio&logoColor=white)
![Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-4285F4?logo=google&logoColor=white)
![SQLite](https://img.shields.io/badge/DB-SQLite-003B57?logo=sqlite&logoColor=white)
![RAG](https://img.shields.io/badge/Retrieval-Local%20RAG-00CFCA)
![Read-only](https://img.shields.io/badge/Database%20access-Read--only-success)

</div>

---

## 📖 Overview

**AI IT Operations Assistant** turns a support-ticket database into an interactive operations center. IT engineers can ask questions in plain language, browse active tickets, get an AI-generated investigation for any ticket, and draft customer replies — all while the AI stays **read-only**, **grounded in real tool results**, and **privacy-aware**.

The assistant never invents numbers. Every figure comes from a predefined analytics function or a validated read-only SQL query, and troubleshooting advice is retrieved from a local knowledge base *before* falling back to generic playbooks.

## ✨ Key Features

| | Feature | What it does |
|---|---|---|
| 💬 | **Chat assistant** | Ask about ticket status, trends, SLA, resolution times, or request troubleshooting help. Returns an answer plus a relevant chart and result table. |
| 📊 | **Operations dashboard** | KPI cards (total tickets, SLA breaches, customer satisfaction) and charts by status, priority, issue category, creation trend, and resolving staff. |
| 🎫 | **Ticket workspace** | Searchable / filterable active-ticket table. Selecting a row instantly shows the record and classification, then streams in an AI investigation (Summary + Detailed Analysis). |
| ✍️ | **AI reply copilot** | Generates an editable, professional customer reply draft with one-click copy. Nothing is ever sent automatically. |
| 📚 | **Knowledge-base RAG** | Multilingual semantic search over local IT runbooks (`.md`, `.txt`, `.pdf`, `.docx`) with approval-status labels. |
| 🧪 | **Troubleshooting playbooks** | Safe, general triage steps for common IT domains used as a last-resort fallback. |
| 🔎 | **Similar-ticket search** | Keyword search over historical ticket descriptions and resolution notes for extra context. |
| 🗂️ | **Schema inspector** | Live view of the database tables and columns without modifying anything. |

## 🏗️ Architecture

```mermaid
flowchart LR
    U([👤 IT Engineer]) --> UI[🖥️ Gradio UI<br/><code>app.py</code>]
    UI --> AG[🤖 Agent Orchestrator<br/><code>agent.py</code>]
    UI --> AN[📊 Analytics<br/><code>analytics.py</code>]
    AG <-->|tool calls| LLM[(✨ Gemini<br/>OpenAI-compatible API)]
    AG --> AN
    AG --> KB[📚 Knowledge Base RAG<br/><code>knowledge_base.py</code>]
    AG --> TS[🧪 Playbooks<br/><code>troubleshooting.py</code>]
    AG --> DB[🛡️ Safe DB Layer<br/><code>database.py</code>]
    AN --> DB
    DB --> SQL[(🗄️ SQLite<br/>Gold tables)]
    KB --> DOCS[/📄 knowledge_base/*.md/]
    CFG[⚙️ <code>config.py</code> + <code>.env</code>] -.-> UI
    CFG -.-> AG
    CFG -.-> DB
```

## 🔄 How a Question Is Answered

The model never touches the database directly. It *requests* a tool; Python runs it and returns the result for the model to explain.

```mermaid
sequenceDiagram
    autonumber
    actor E as IT Engineer
    participant UI as Gradio UI
    participant A as Agent (agent.py)
    participant G as Gemini
    participant T as Python Tools
    participant D as SQLite (read-only)

    E->>UI: "How many tickets are in each status?"
    UI->>A: ask_assistant(question, history)
    loop up to 4 tool rounds
        A->>G: messages + tool definitions
        G-->>A: tool_call (e.g. get_tickets_by_status)
        A->>T: execute tool in Python
        T->>D: validated read-only query
        D-->>T: rows
        T-->>A: compact JSON result
    end
    A->>G: tool results
    G-->>A: final grounded answer
    A-->>UI: answer + Plotly chart + result table
    UI-->>E: renders chat, chart and table
```

## 🧭 Intent Routing & Troubleshooting Workflow

The agent routes each request by intent. For technical issues it follows a strict **source-search order** so advice is always evidence-based.

```mermaid
flowchart TD
    Q([❓ User request]) --> R{What kind of request?}
    R -->|Numbers / metrics| M[Call a predefined analytics tool]
    R -->|Specific ticket ID| T[get_ticket_for_investigation]
    R -->|IT incident / how-to| S1

    M --> ANS
    T --> ANS

    subgraph W[🔍 Mandatory source-search workflow]
        direction TB
        S1[1️⃣ Search the Knowledge Base] --> K{Relevant<br/>document found?}
        K -->|Yes| USE[Use it as primary evidence<br/>state filename + approval status]
        K -->|No| S2[2️⃣ Trusted external docs<br/><i>only if a real web-search tool exists</i>]
        S2 --> E{Suitable<br/>result?}
        E -->|No| S3[3️⃣ Fallback: generic playbook<br/>+ similar historical tickets]
    end

    USE --> STEP
    E -->|Yes| STEP
    S3 --> STEP[Give ONE safe diagnostic action<br/>or ask ONE clarifying question]
    STEP --> ANS([✅ Grounded answer])
```

## 🛡️ Safety & Privacy by Design

```mermaid
flowchart LR
    SQLIN[AI-generated SQL] --> P1[Parse with SQLGlot]
    P1 --> P2{Single SELECT only?<br/>No CTE / set ops / DML}
    P2 -->|No| X[❌ Rejected]
    P2 -->|Yes| P3{Approved tables only?<br/>No wildcard *<br/>No blocked functions}
    P3 -->|No| X
    P3 -->|Yes| P4{Personal-data columns<br/>blocked?}
    P4 -->|Blocked| X
    P4 -->|OK| P5[Enforce row LIMIT<br/>default 200, max 1000]
    P5 --> RUN[✅ Execute on SQLite]
```

- **Read-only by construction** — only one validated `SELECT` is ever executed; the assistant cannot create, update, assign, close, or delete anything.
- **Approved schema only** — queries are limited to eight Gold tables: `facttickets`, `dimcustomer`, `dimdate`, `dimissue`, `dimstaff`, `dimticketcontext`, `dimticketflags`, `dimticketstate`.
- **PII protection** — columns such as customer email, name, age, and gender are blocked; no wildcard projections; secrets and emails are redacted from retrieved knowledge-base text.
- **Prompt-injection resistant** — retrieved documents, ticket text, and notes are treated as *untrusted evidence, never as instructions*.
- **No fabricated sources** — the model may only cite tools that actually returned results.
- **Honest metrics** — resolver attribution is never presented as assigned workload; resolution time, wall-clock time, and paused time stay distinct.
- **Secrets stay local** — API keys live in `.env` and are redacted from logs and error messages.

## 📁 Project Structure

```text
ai-it-operations-assistant/
├── app.py                  # Gradio UI: Chat, Dashboard, Ticket Workspace, Schema tabs
├── agent.py                # Gemini tool-calling orchestration + system prompt + tool schemas
├── analytics.py            # KPIs, SLA/escalation/resolution metrics, charts, ticket investigation
├── database.py             # SQLAlchemy engine, schema inspection, SQL validator (SQLGlot)
├── knowledge_base.py       # Local multilingual RAG: chunking, embeddings, semantic search
├── troubleshooting.py      # Safe general IT playbooks per issue domain
├── config.py               # Settings loaded from environment / .env
├── knowledge_base/         # Starter IT runbooks (Markdown with front-matter)
│   ├── vpn_troubleshooting.md
│   ├── network_connectivity.md
│   ├── account_access.md
│   ├── email_access.md
│   └── security_incident.md
├── data/                   # Place your local SQLite database here (git-ignored)
├── requirements.txt
├── .env.example
└── .gitignore
```

## 🧩 What Each Module Does

| Module | Responsibility |
|---|---|
| **`app.py`** | Builds the Gradio interface with three tabs — **Chat**, **Dashboard** (KPIs, filters, ticket workspace, analytics accordion) and **Database Schema**. Streams ticket details first, then the AI analysis, so the UI never freezes. Includes the reply-draft generator and clipboard copy. |
| **`agent.py`** | Defines the system prompt, the 12 tool schemas, and the tool-calling loop (max 4 rounds, retry on transient errors). Executes tools in Python, compacts results, picks the right chart, and converts API errors into friendly messages. |
| **`analytics.py`** | Predefined, verified queries: ticket summary, by status / priority / issue, trends (day → year), SLA flags, escalations, resolution & satisfaction metrics, resolver workload, active-ticket list, similar-ticket search, and single-ticket investigation. Also builds Plotly charts. |
| **`database.py`** | Connection handling with timeouts, live schema reflection, relationship verification, and the **read-only SQL validator** (SQLGlot AST checks, table/column allow-listing, forced `LIMIT`). |
| **`knowledge_base.py`** | Loads `.md/.txt/.pdf/.docx` files, parses front-matter (`approval_status`, `source_type`), splits into overlapping chunks, embeds with FastEmbed, and returns top-k excerpts by cosine similarity with a minimum score threshold. |
| **`troubleshooting.py`** | Fallback playbooks for network, account access, email, software installation, security incident, device performance, application error, and printer/peripheral issues. |
| **`config.py`** | Typed, bounded settings (`SQL_MAX_ROWS`, `DB_CONNECT_TIMEOUT`, host/port, model, DB path) loaded from `.env`. |

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python |
| **UI** | Gradio |
| **LLM** | Google Gemini via the OpenAI-compatible endpoint (`openai` SDK) |
| **Data** | SQLite · SQLAlchemy · Pandas |
| **Visualization** | Plotly |
| **SQL safety** | SQLGlot (AST parsing & validation) |
| **RAG / embeddings** | FastEmbed — `paraphrase-multilingual-MiniLM-L12-v2` (runs locally, supports Arabic & English) |
| **Document parsing** | pypdf · python-docx |
| **Config** | python-dotenv |

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.10+
- A [Gemini API key](https://aistudio.google.com/apikey)
- A locally prepared SQLite database containing the Gold tables listed above

> 🔒 The database and customer-level CSV exports are **intentionally excluded** from this repository. Use an authorized local database only.

### 2. Install

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

<details>
<summary>macOS / Linux</summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
</details>

### 3. Configure

```powershell
Copy-Item .env.example .env
notepad .env
```

| Variable | Description | Default |
|---|---|---|
| `GEMINI_API_KEY` | Your Gemini API key | — |
| `GEMINI_MODEL` | Model used for tool calling | `gemini-3.1-flash-lite` |
| `SQLITE_DATABASE_PATH` | Path to your local database | `./data/gold_support.db` |
| `APP_HOST` / `APP_PORT` | Where the Gradio app listens | `127.0.0.1` / `7860` |
| `SQL_MAX_ROWS` | Hard cap on rows returned by SQL (1–1000) | `200` |
| `DB_CONNECT_TIMEOUT` | Database connect timeout in seconds (1–30) | `5` |
| `RAG_EMBEDDING_MODEL` | *(optional)* Override the embedding model | multilingual MiniLM |
| `RAG_MIN_SCORE` | *(optional)* Minimum similarity for KB results | `0.25` |

### 4. Run

```powershell
.\.venv\Scripts\python.exe .\app.py
```

Open the local URL printed in the terminal (default: <http://127.0.0.1:7860>).

> ℹ️ On the first knowledge-base search, FastEmbed downloads the embedding model and caches it locally.

## 📚 Extending the Knowledge Base

Drop your own runbooks into `knowledge_base/` as `.md`, `.txt`, `.pdf`, or `.docx`. For Markdown, add front-matter so the assistant can tell official procedures from generic guidance:

```markdown
---
title: VPN connection troubleshooting basics
source_type: general_it_guidance
approval_status: not_organization_approved   # or: organization_approved
version: 1
---
# Your runbook content...
```

Documents marked `not_organization_approved` are presented as generic guidance, never as official company procedure.

## 💡 Example Questions

- *How many tickets are in each status?*
- *Show ticket creation trends by month.*
- *What are the observed SLA breach flag values and counts?*
- *Compare resolution time and first-response time, keeping the measures separate.*
- *Help me troubleshoot a VPN connection problem.*
- *Find previous tickets similar to an email sign-in failure.*
- *Investigate ticket ID 1001.*

## 🔐 Security Notes

- Keep API keys in `.env` — never in source code or `.env.example`.
- Never commit database files, customer data, or CSV exports (already covered by `.gitignore`).
- AI-generated drafts are suggestions only; review them before sending anything outside the app.

## 🗺️ Possible Next Steps

- Add a web-search tool so Step 2 of the troubleshooting workflow can cite official vendor documentation.
- Persist chat history and add per-user authentication.
- Containerize the app with Docker for one-command deployment.

---
