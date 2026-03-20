# ◆ Shadow Agent

Lightweight AI Agent Orchestrator — didesain untuk Termux (Android, RAM 3GB+).

**Stack:** Python · FastAPI · SQLite · Rich CLI · Anthropic + OpenAI

---

## Arsitektur

```
shadow-agent/
├── config.py              # Central config + env vars
├── cli.py                 # Entry point CLI (Rich TUI)
├── requirements.txt
├── .env.example
│
├── core/
│   ├── database.py        # SQLite layer (sessions, tasks, stats)
│   ├── provider.py        # AI provider abstraction (Anthropic + OpenAI + fallback)
│   └── orchestrator.py    # Multi-agent pipeline runner
│
├── agents/
│   ├── base.py            # BaseAgent class
│   └── agents.py          # Planner, Researcher, Writer, Coder + registry
│
├── api/
│   └── server.py          # FastAPI REST API + SSE streaming
│
├── web/
│   └── templates/
│       └── index.html     # Web UI (single file, no build step)
│
└── data/
    └── shadow.db          # SQLite database (auto-created)
```

---

## Instalasi (Termux)

```bash
# 1. Update Termux
pkg update && pkg upgrade

# 2. Install Python
pkg install python

# 3. Clone / copy project
cd ~
# (paste atau copy folder shadow-agent ke sini)

# 4. Install dependencies
cd shadow-agent
pip install -r requirements.txt

# 5. Setup environment
cp .env.example .env
nano .env   # isi ANTHROPIC_API_KEY dan/atau OPENAI_API_KEY
```

---

## Penggunaan

### Mode Interaktif (Termux)
```bash
python cli.py
```

### CLI Commands
```bash
# Jalankan full goal pipeline
python cli.py run "Research and write an article about Python async programming"

# Force provider tertentu
python cli.py run "Write a poem about the ocean" --provider anthropic

# Jalankan satu agent saja
python cli.py agent researcher --prompt "What is WebAssembly?"
python cli.py agent coder      --prompt "Write a Python quicksort function"
python cli.py agent writer     --prompt "Write a product description for wireless earbuds"
python cli.py agent planner    --prompt "Plan a SaaS landing page project"

# Lihat sessions
python cli.py sessions

# Lihat provider status
python cli.py status

# Lihat usage stats
python cli.py stats

# Start Web UI + API server
python cli.py serve
python cli.py serve --port 8080
```

### Web UI
```bash
python cli.py serve
# Buka browser: http://localhost:5000
# Dari HP lain di WiFi yang sama: http://<ip-hp>:5000
```

---

## Konfigurasi Agent → Provider

Edit `config.py` untuk override per-agent:

```python
agent_provider_map = {
    "planner":    "anthropic",   # Claude lebih baik untuk reasoning
    "researcher": "openai",      # GPT untuk summarize
    "writer":     "anthropic",   # Claude lebih baik untuk nulis
    "coder":      "anthropic",   # Claude lebih baik untuk code
}
```

---

## API Endpoints

```
GET  /api/health              Health check
GET  /api/providers           Status Anthropic + OpenAI
GET  /api/agents              List semua agent + deskripsi
GET  /api/sessions            List semua sessions
GET  /api/sessions/{id}       Detail session + tasks
GET  /api/tasks/{id}          Detail task + messages
POST /api/run/goal            Run full pipeline (sync)
POST /api/run/goal/stream     Run full pipeline (SSE streaming)
POST /api/run/agent           Run single agent
GET  /api/stats               Usage stats per provider/hari
GET  /api/docs                FastAPI Swagger UI
```

### Contoh API calls:
```bash
# Run pipeline
curl -X POST http://localhost:5000/api/run/agent \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"coder","prompt":"Write a Python function to parse JSON"}'

# Run goal
curl -X POST http://localhost:5000/api/run/goal \
  -H "Content-Type: application/json" \
  -d '{"goal":"Research and summarize the latest trends in AI agents"}'
```

---

## RAM Usage (estimasi Termux)

| Komponen | RAM |
|---|---|
| Python process | ~40MB |
| FastAPI + uvicorn | ~60MB |
| SQLite | ~5MB |
| Rich CLI | ~15MB |
| **Total** | **~120–200MB** |

Jauh di bawah batas 3GB. Masih ada headroom untuk 5–10 concurrent API calls.

---

## Extend

### Tambah agent baru:
```python
# agents/agents.py
class SummarizerAgent(BaseAgent):
    agent_type = "summarizer"
    system_prompt = "You are an expert summarizer..."
    def describe(self): return "Summarizes long content."

AGENT_REGISTRY["summarizer"] = SummarizerAgent
```

### Tambah provider baru (misal Groq):
Tambah function `_call_groq()` di `core/provider.py` dan tambah ke `callers` dict di `call_ai()`.

---

## Lisensi
MIT — gunakan, modifikasi, jadikan milik lo sendiri.
