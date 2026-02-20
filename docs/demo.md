# Study Pal – End-to-End Demo Script

**Purpose:** Repeatable, impressive demo that walks through the full multi-agent flow: Intent Router → Tutor → Analyzer → Scheduler → Motivator. Use this to showcase your multi-agent orchestration skills.

---

## Prerequisites

- **Python 3.10+**
- **OPENAI_API_KEY** in `.env` (required; copy from `.env.example`).
- **Optional:** Node.js 18+ for the Web UI (see [QUICK_START.md](QUICK_START.md)).
- **Demo asset:** `tests/fixtures/calculus_sample.pdf` (included in repo).

---

## Option A – Terminal Demo

1. **Start the app**
   ```bash
   cd study_pal
   source .venv/bin/activate   # or your venv
   export OPENAI_API_KEY=sk-...   # or use .env
   python terminal_app.py
   ```
   Enter a username when prompted (e.g. `demo_user`) or press Enter for `demo_user`.

2. **Upload material**
   - Type: `upload`
   - When asked for path, enter: `tests/fixtures/calculus_sample.pdf`
   - Confirm you see a success message and chunk count.

3. **Tutor**
   - Ask: *"Explain the concept of a limit in calculus."*
   - Get an RAG-grounded explanation from the Tutor agent.

4. **Quiz**
   - Ask for a quiz (e.g. *"Give me a quiz on limits"*), answer the questions, get feedback.

5. **Analyze session**
   - Say: *"I'm done. Analyze my studying."*
   - The Intent Router sends you to the Analyzer; you get a summary and weak points.

6. **Schedule next session**
   - When asked *"schedule next session?"* reply *"Yes"*, then give a time window (e.g. *"Wednesday 18:00–20:00"*).
   - The Scheduler creates a plan; if it asks about calendar sync, say *"Yes"* or *"No"* (both work; calendar is optional).

7. **Motivation**
   - Say: *"Give me a pep talk."*
   - The Motivator returns a persona-aligned message.

**What to highlight:** One entry point (your message) → Intent Router (LLM) → the right agent. Tutor uses RAG over your PDF; Analyzer writes to shared state; Scheduler can optionally sync to calendar; Motivator uses profile/quotes. Watch logs to narrate handoffs.

---

## Option B – Web UI Demo

1. **Start API and frontend** (see [QUICK_START.md](QUICK_START.md)):
   ```bash
   ./start_dev.sh
   ```
   Or manually: run `./api/run.sh` in one terminal, then `cd frontend && npm run dev` in another.

2. **Register**
   - Open http://localhost:3000, go to Register, create a user (e.g. `demo_user`).

3. **Same flow as terminal**
   - In chat, use the upload control to upload `tests/fixtures/calculus_sample.pdf` (or the path from your machine if testing locally).
   - Then use the same message sequence:
     - *"Explain the concept of a limit in calculus."*
     - Request a quiz, answer it, get feedback.
     - *"I'm done. Analyze my studying."*
     - When asked, *"Yes"* to schedule, then e.g. *"Wednesday 18:00–20:00"*.
     - *"Give me a pep talk."*

4. **Highlight**
   - Same multi-agent flow as terminal; the API wraps the same LangGraph chatbot. You can point to network tab or API logs to show single entry → routing → agent responses.

---

## Validation Checklist

- [ ] Upload succeeds and chunk count is shown.
- [ ] Tutor answers from the uploaded material (RAG).
- [ ] Quiz request returns questions and accepts answers with feedback.
- [ ] *"I'm done. Analyze my studying."* triggers the Analyzer (summary/weaknesses).
- [ ] Scheduler creates a plan (and optionally mentions calendar sync).
- [ ] *"Give me a pep talk."* returns a Motivator message.

If any step fails, check: `OPENAI_API_KEY` is set, dependencies are installed (`pip install -r requirements.txt`), and logs in `logs/` (terminal) or API console for errors.

---

## Known Limitations

- **OPENAI_API_KEY** is required for the full demo; no key → errors when the graph calls the LLM.
- **Calendar MCP** is optional; if not configured, the Scheduler still works and explains that sync isn’t available.
- **First run** can be slower (ChromaDB, graph build); subsequent messages are faster.

For setup details, see [README.md](README.md) and [QUICK_START.md](QUICK_START.md).
