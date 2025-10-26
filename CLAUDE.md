CLAUDE.md

Project brief for Claude Code CLI to scaffold and implement a private, homelab-hosted Personal Finance Automation system with glassmorphic UI.
Stack: FastAPI + PostgreSQL + n8n + Google Drive + OpenAI (categorization), optional Redis.
Goal: Drop statements in Drive → parse → categorize (rules → AI) → store → reports/alerts → sleek dashboard.

⸻

0) Core Objectives
	•	Ingestion: n8n watches Google Drive “Statements/” and POSTs parsed rows to our API.
	•	Normalization: merchant cleanup, dedupe (hash), consistent schema.
	•	Categorization: deterministic rules first, then OpenAI fallback with confidence score.
	•	Receipts: link back to the source file in Drive.
	•	Reporting: monthly/weekly summaries, category trends, top vendors, anomaly flags.
	•	UI: modern, sleek, glassmorphic web dashboard served by FastAPI (Jinja) now; React later.
	•	Ops: Dockerized, env-driven, easy to run on homelab; migrations; tests; CI-ready.

⸻

1) Repo Structure (create these)

finance-automation/
├─ api/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ deps.py
│  │  ├─ config.py
│  │  ├─ db.py
│  │  ├─ models.py
│  │  ├─ schemas.py
│  │  ├─ rules.py
│  │  ├─ categorize.py
│  │  ├─ routers/
│  │  │  ├─ ingest.py
│  │  │  ├─ categorize.py
│  │  │  ├─ reports.py
│  │  │  ├─ alerts.py
│  │  ├─ services/
│  │  │  ├─ vendor_normalize.py
│  │  │  ├─ receipts.py
│  │  │  ├─ anomalies.py
│  │  ├─ templates/
│  │  │  ├─ base.html
│  │  │  ├─ dashboard.html
│  │  │  ├─ reports.html
│  │  ├─ static/
│  │  │  ├─ styles.css
│  ├─ tests/
│  │  ├─ test_ingest.py
│  │  ├─ test_rules.py
│  │  ├─ test_categorize.py
│  ├─ alembic/
│  │  ├─ env.py
│  │  ├─ versions/
│  ├─ alembic.ini
│  ├─ requirements.txt
│  ├─ pyproject.toml
│
├─ n8n/
│  ├─ workflows/
│  │  ├─ drive_ingest.json
│  │  ├─ weekly_report.json
│
├─ ops/
│  ├─ docker-compose.yml
│  ├─ .env.example
│  ├─ makefile
│  ├─ nginx.conf (optional)
│
├─ seed/
│  ├─ seed_rules.sql
│  ├─ seed_vendors.sql
│
├─ README.md
├─ SECURITY.md
└─ CLAUDE.md   ← (this file)


⸻

2) Environment & Secrets

Create ops/.env.example:

POSTGRES_USER=rody
POSTGRES_PASSWORD=supersecret
POSTGRES_DB=finance
DATABASE_URL=postgresql+psycopg2://rody:supersecret@postgres:5432/finance

OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini

JWT_SECRET=change_me
ALLOWED_ORIGINS=http://localhost:8080,https://finance.local

TELEGRAM_WEBHOOK_URL=   # optional


⸻

3) Docker Compose

Create ops/docker-compose.yml:
	•	Services: postgres:16, redis:7 (optional), api (uvicorn), n8n (external), reverse proxy optional.
	•	Mount volumes for Postgres and n8n.
	•	Expose api on 8080.

⸻

4) Database Schema (SQL via Alembic)

Tables (first migration):

-- transactions
id BIGSERIAL PK
txn_date DATE NOT NULL
posted_at TIMESTAMPTZ DEFAULT now()
amount_cents BIGINT NOT NULL
currency TEXT NOT NULL DEFAULT 'USD'
direction TEXT CHECK (direction IN ('debit','credit')) NOT NULL
raw_descriptor TEXT NOT NULL
canonical_vendor TEXT
mcc TEXT
memo TEXT
source_account TEXT NOT NULL
hash_id TEXT UNIQUE NOT NULL
receipt_url TEXT
category TEXT
subcategory TEXT
confidence NUMERIC(3,2)
status TEXT DEFAULT 'ingested'       -- ingested|review|finalized
notes TEXT

-- vendors
canonical_vendor TEXT PK
default_category TEXT
default_subcat TEXT
aliases TEXT[] DEFAULT '{}'

-- rules (deterministic)
id BIGSERIAL PK
priority INT NOT NULL
condition JSONB NOT NULL
action JSONB NOT NULL
active BOOLEAN DEFAULT TRUE
created_at TIMESTAMPTZ DEFAULT now()

-- reports (optional cache)
id BIGSERIAL PK
period TEXT NOT NULL        -- e.g., '2025-10'
kind TEXT NOT NULL           -- 'weekly','monthly'
payload JSONB NOT NULL
created_at TIMESTAMPTZ DEFAULT now()

Indexes:
	•	transactions(txn_date), transactions(canonical_vendor), transactions(category), rules(active, priority)

Seed files:
	•	seed/seed_rules.sql with common vendors/MCC patterns.
	•	seed/seed_vendors.sql with initial canonical vendors + aliases.

⸻

5) FastAPI App

api/app/config.py
	•	Load env vars, model name, thresholds (LOW_CONFIDENCE=0.80), etc.

api/app/models.py (SQLAlchemy)
	•	ORM for tables above.

api/app/schemas.py (Pydantic)
	•	TxnIn, TxnOut, CategorizeOut, SummaryOut, AlertOut.

api/app/rules.py
	•	Apply deterministic rules from DB (JSON conditions: contains, regex, mcc, amount range, account).

api/app/categorize.py
	•	If rules miss, call OpenAI:
	•	Prompt (few-shot) using fixed taxonomy for personal finance:

Taxonomy = [Groceries, Dining, Transport, Fuel, Utilities, Rent/Mortgage,
Internet, Mobile, Subscriptions, Shopping, Healthcare, Pets, Gifts/Charity,
Entertainment, Travel-Air, Travel-Hotel, Travel-Other, Income, Transfers, Savings]


	•	Return {category, subcategory, confidence, vendor}.
	•	Store category/subcategory/confidence.

Routers
	1.	/ingest (POST)
	•	Upsert by hash_id.
	•	Normalize merchant (services/vendor_normalize.py).
	•	Return id.
	2.	/categorize/{id} (POST)
	•	Run rules → if none, LLM.
	•	If confidence < threshold or amount_cents > limit, set status='review'.
	•	Return CategorizeOut.
	3.	/finalize/{id} (POST)
	•	Accept category adjustment; mark status='finalized'.
	4.	/report/summary (GET)
	•	Query by month or range; totals per category, top vendors, line chart data.
	5.	/alerts (GET)
	•	New vendor over threshold, duplicates, z-score spikes, missing receipts.

Templates (glassmorphic)
	•	templates/base.html, templates/dashboard.html, templates/reports.html
	•	static/styles.css: provide tokens below.

⸻

6) CSS Tokens (Glassmorphic)

api/app/static/styles.css (add core styles)

:root{
  --bg: #0E1116;
  --bg2: #121826;
  --card: rgba(255,255,255,0.08);
  --border: rgba(255,255,255,0.12);
  --text: #E0E0E0;
  --accent: #00D4FF;
  --accent2:#6BE7FF;
}

body{
  margin:0; font-family: Inter, ui-sans-serif, system-ui;
  color:var(--text);
  background: linear-gradient(135deg,var(--bg) 0%,var(--bg2) 100%);
}

.card{
  background: var(--card);
  backdrop-filter: blur(14px);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.25);
}

.badge{
  border:1px solid var(--border);
  border-radius:999px;
  padding:4px 10px;
}

.accent{ text-shadow: 0 0 18px var(--accent); }
a{ color: var(--accent); text-decoration: none; }
a:hover{ text-decoration: underline; }


⸻

7) OpenAI Prompts

Categorizer system message:

You classify personal finance transactions into a fixed taxonomy.
Prefer deterministic mapping from known vendors/MCCs; otherwise infer sensibly.
Return strict JSON with: category, subcategory, confidence (0-1), vendor.

Categorizer user template:

Taxonomy = [Groceries, Dining, Transport, Fuel, Utilities, Rent/Mortgage,
Internet, Mobile, Subscriptions, Shopping, Healthcare, Pets, Gifts/Charity,
Entertainment, Travel-Air, Travel-Hotel, Travel-Other, Income, Transfers, Savings]

Transaction:
date={txn_date}
amount={amount} {currency} ({direction})
descriptor="{raw_descriptor}"
memo="{memo}"
mcc="{mcc}"

Examples:
- "NETFLIX.COM" → {"category":"Subscriptions","subcategory":"Streaming","confidence":0.97,"vendor":"Netflix"}
- "CASEY'S STORE 1234" → {"category":"Fuel","subcategory":"Gas Station","confidence":0.92,"vendor":"Casey's"}

Now classify.

PDF statement extractor (for n8n → OpenAI):

Extract a CSV with columns: date, description, amount, direction, mcc?, memo?
Only return the CSV. PDF text below:
<<<{pdf_text}>>>


⸻

8) n8n Workflows (generate JSON stubs)
	•	n8n/workflows/drive_ingest.json
	•	Trigger: Google Drive “New File in Folder” (filter: .csv, .ofx, .pdf)
	•	CSV/OFX branch: parse → map fields → compute hash_id = sha256(date|amount_cents|descriptor|account) → POST /ingest → POST /categorize/{id} → low-confidence route to Telegram approval webhook (optional) → /finalize/{id}
	•	PDF branch: extract text → OpenAI “statement extractor” → same as above
	•	Receipt matching: search Drive ± date window and amount tolerance; PATCH /transactions/{id} with receipt_url
	•	n8n/workflows/weekly_report.json
	•	Cron weekly → SQL aggregate via Postgres node → OpenAI summary (“one habit improvement”) → POST /reports and optionally send to Telegram.

⸻

9) Makefile (ops/makefile)

Targets:

init: create venv, install deps
migrate: alembic upgrade head
seed: run seed SQLs
up: docker compose up -d
down: docker compose down
logs: docker compose logs -f api
test: pytest -q
format: ruff check --fix && black api


⸻

10) API Contracts (JSON)

POST /ingest
	•	in: TxnIn

{
  "txn_date":"2025-10-24",
  "amount_cents":784,
  "currency":"USD",
  "direction":"debit",
  "raw_descriptor":"STARBUCKS 1234",
  "source_account":"amex_blue_cash",
  "memo": null,
  "mcc": "5814",
  "hash_id":"<sha256>"
}

	•	out: { "id": 123, "status": "ingested" }

POST /categorize/{id}
	•	out:

{
  "id":123,
  "category":"Dining",
  "subcategory":"Coffee",
  "confidence":0.91,
  "status":"finalized|review"
}

POST /finalize/{id}
	•	in: { "category":"Dining","subcategory":"Coffee" }
	•	out: { "ok": true }

GET /report/summary?month=YYYY-MM
	•	out:

{
  "period":"2025-10",
  "totals_by_category":[{"category":"Groceries","amount_cents":45000}, ...],
  "top_vendors":[{"vendor":"Hy-Vee","amount_cents":22000},...],
  "timeseries":[{"date":"2025-10-01","sum_cents":4300},...]
}

GET /alerts
	•	out: [ { "type":"new_vendor_over_threshold", "vendor":"Acme Gym", "amount_cents":3999, "date":"2025-10-20" }, ... ]

⸻

11) Deterministic Rule Seeds (seed/seed_rules.sql)
	•	MCC → Category:
	•	('5411','5422') → Groceries
	•	('5812','5814') → Dining
	•	('4111','4121') → Transport/Rideshare
	•	Fuel brands → Fuel
	•	Descriptor contains:
	•	NETFLIX|HULU|SPOTIFY|ICLOUD|AMAZON PRIME|YOUTUBE → Subscriptions
	•	HY-VEE|FAREWAY|COSTCO|WALMART SUPERCENTER|TARGET → Groceries
	•	DELTA|UNITED|AMERICAN AIR|SOUTHWEST → Travel-Air
	•	MARRIOTT|HILTON|HYATT|IHG → Travel-Hotel
	•	Credits with PAYROLL|DIRECT DEP|VENMO CASHOUT → Income (or Transfers if own accounts).

⸻

12) Testing
	•	Unit tests for:
	•	Rule engine mappings
	•	Hash de-dupe logic
	•	Categorizer fallback (mock OpenAI)
	•	Integration:
	•	/ingest → /categorize → /finalize flow with a fixture CSV
	•	Snapshot tests for report summaries.

⸻

13) Security & Ops
	•	JWT on write endpoints; read-only for dashboard.
	•	Behind Tailscale; optional Cloudflare Tunnel for read-only dashboards.
	•	Backups: nightly pg_dump; weekly basebackup; retention 90 days.
	•	Logs: redact raw_descriptor patterns that resemble PAN; never store full card numbers.

⸻

14) Acceptance Criteria
	•	Drop a CSV/PDF into Drive → transaction appears in dashboard within 2 minutes.
	•	Deterministic rules tag ≥70% of transactions; LLM handles the rest.
	•	Low-confidence items surface in “Review” with one-click finalize.
	•	Monthly summary loads < 300ms on local network.
	•	All services run via docker compose up -d with only .env filled.
	•	Tests pass locally (pytest) and pre-commit hooks format code.

⸻

15) Tasks for Claude (generate files)
	1.	Scaffold FastAPI app files exactly per structure above; wire SQLAlchemy + Alembic; create initial migration.
	2.	Implement /ingest, /categorize/{id}, /finalize/{id}, /report/summary, /alerts.
	3.	Implement rules engine and vendor_normalize utilities.
	4.	Implement OpenAI client call with env model; strict JSON parsing & retry on malformed JSON.
	5.	Create templates and styles.css with the glassmorphic tokens; basic dashboard showing:
	•	Month selector, total income/expense/savings cards
	•	Category donut, top vendors list, daily spend sparkline
	6.	Create ops/docker-compose.yml, ops/.env.example, ops/makefile.
	7.	Create seed_rules.sql and seed_vendors.sql.
	8.	Add unit tests for rules, categorize, and ingest.
	9.	Emit n8n workflow JSON stubs for drive_ingest.json and weekly_report.json.
	10.	Write README.md with setup steps, env, make targets, and n8n instructions.

⸻

16) Nice-to-have (phase 2)
	•	Add /report/subscriptions (recurring detection).
	•	Add anomaly z-score per category and vendor.
	•	Optional pgvector merchant embeddings for fuzzy matching fallback.
	•	React frontend (Next.js) consuming the same endpoints.

⸻

Done = You can:
	•	docker compose up -d
	•	make migrate && make seed
	•	Open http://localhost:8080/ → see dashboard with sample data.
	•	Run tests: make test.
