# 📱 VibeCheck: WhatsApp Chat Analyzer

**VibeCheck** is a privacy-first, production-grade analytics engine that transforms your WhatsApp chat exports into beautiful, interactive insights. 

Visualize who dominates the conversation, who leaves you on read, and the overall "vibe" (sentiment) of your group dynamics with narrative-driven storytelling.

🔗 **Live Dashboard:** [vibecheck.idyvalour.space](https://vibecheck.idyvalour.space)

---

## Features

### Deep Dive Analytics
* **Volume Analysis:** Interactive breakdowns of message counts per author.
* **Sentiment "Vibe" Check:** NLP-powered positivity scoring to see who brings the best energy.
* **Ghost Meter:** Advanced response time metrics to find the fastest responders and the serial "re-readers".
* **Hourly & Weekly Activity:** Discover your group's peak "prime time" and busiest days.
* **Topic Word Clouds:** Visual representation of the most common themes and slang.

### Behavioral Insights (Fun Stuff)
* **Monologue Detector:** Identifies the "serial texters" who send multiple messages in a row.
* **Conversation Roles:** Find out who always starts the fire and who always has the last word.
* **Link Sharer:** Tracks the group's "News Scout" who shares the most external content.
* **Message Length Analysis:** Novels vs. One-liners – see who writes the longest essays.
* **Achievement Badges:** Automated awards like "Night Owl", "Early Bird", "Professor", and "Chatterbox".
* **Personal Comparison:** A "You vs The Group" card to see exactly where you stand against the averages.

---

## Architecture

The project has been refactored from a monolithic script into a modern, modular **Feature-Module Architecture**:

* **`src/` (Core Engine):** Pure Python library for parsing and analysis. Framework-agnostic.
* **`api/` (Backend):** High-performance **FastAPI** layer providing endpoints for external frontends (e.g., React/Recharts).
* **`app.py` (Dashboard):** Rich **Streamlit** user interface powered by the core engine.
* **Dockerized:** Full containerization with `docker-compose` for easy deployment.

---

## Getting Started

### 1. Local Run (Development)
The project uses `uv` for lightning-fast package management.

```bash
# Clone the repository
git clone https://github.com/idyweb/VibeCheck.git
cd VibeCheck

# Install dependencies
uv sync

# Run the UI
uv run streamlit run app.py

# Run the API
uv run uvicorn api.main:app --reload --port 8000
```

### 2. Docker Run (Production)
```bash
docker compose up -d --build
```
*   **UI:** `http://localhost:8501`
*   **API Specs:** `http://localhost:8000/docs`

---

## API For Developers
The new FastAPI backend allows you to build your own frontend (like React or Recharts) using VibeCheck's analysis engine:

| Endpoint | Description |
|----------|-------------|
| `POST /api/upload` | Upload chat, get `session_id` |
| `GET /api/analysis/summary` | Executive summary stats |
| `GET /api/analysis/emojis` | Signature emojis & top users |
| `GET /api/analysis/compare` | Personal comparison report |
| `GET /api/analysis/monologues` | Serial texter detection |

---

## Privacy & Security Standards
*   **Zero-Storage:** Chat files are processed in-memory and never written to disk or database.
*   **Stateless:** The API uses transient session IDs that expire when the server clears memory.
*   **No PII Leakage:** Built-in name cleaning and anonymization utilities.

---

Built with ❤️ by [Idy](https://github.com/idyweb)