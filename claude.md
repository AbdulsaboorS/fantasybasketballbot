# Claude code agent handoff

Use this file when switching to another agent (e.g. Claude) so work can continue without overlap or confusion.

---

## 1. Read these in order

1. **claude.md** (this file) — how to work in this repo and where things live.
2. **PROJECT_CONTEXT.md** — single source of truth for **project/code state**: structure, tech, config, changelog.
3. **CONTEXT.md** — **user/season context** only: record, guardrails, run log, deployment status. Do not put code or changelog here.

There is no overlap: project state lives in PROJECT_CONTEXT, user/season narrative in CONTEXT, agent rules in this file.

---

## 2. Key paths

| What | Where |
|------|--------|
| Bot logic, suggestions, execute flow | `main.py` |
| Streaming add/drop (ESPN POST) | `espn_transactions.py` |
| FastAPI backend | `api/main.py` |
| React frontend | `web/` (Vite, TypeScript, Tailwind) |
| Strategy, untouchables, non-secret config | `context.json` |
| Credentials (never commit) | `.env` (see `.env.example`) |
| How to capture transaction URL/body | `CAPTURE_TRANSACTION.md` |

---

## 3. Rules you must follow

- **After any confirmed code/config change:** Update **PROJECT_CONTEXT.md** → add a dated Changelog entry with why, what changed, files touched, how to test, and any gotchas. (See `.cursor/rules/project_context_updates.mdc`.)
- **Never commit real credentials.** Only `.env.example` with placeholders; real values stay in `.env` (gitignored).
- **Do not duplicate content:** Put project/tech/changelog in PROJECT_CONTEXT.md only. Put user record, guardrails, run log in CONTEXT.md only. Keep claude.md limited to instructions for agents.

---

## 4. How to run

- **Backend:** From repo root, with `.env` set:  
  `uvicorn api.main:app --reload --port 8000`
- **Frontend:** `cd web && npm install && npm run dev` → open http://localhost:5173
- **CLI:** `python3 main.py` (dry run) or `DRY_RUN=False python3 main.py` (then confirm to execute)

---

## 5. Current work-in-progress (as of last handoff)

**Project is feature-complete. No active development.**

- Bot runs via GitHub Actions (daily + pre-tipoff). Suggestions work fully. Execution requires ESPN request captures that the user has chosen not to do — the bot will surface suggestions and game-day alerts but not auto-execute moves.
- Live demo: Railway (backend) + Vercel (frontend, read-only). Team name hidden from public view; shows only after password login.
- If a future agent picks this up: the only remaining gap is setting `ESPN_TRANSACTION_URL`/`ESPN_TRANSACTION_BODY` and `ESPN_LINEUP_URL`/`ESPN_LINEUP_BODY` env vars in Railway + GitHub Secrets. See `CAPTURE_TRANSACTION.md` and `CAPTURE_LINEUP.md` for instructions.

---

## 6. Handoff checklist

When you finish a session, ensure:

- [ ] PROJECT_CONTEXT.md Changelog is updated for any confirmed changes.
- [ ] CONTEXT.md is updated only if run log or deployment status changed (no code/changelog).
- [ ] No secrets in any committed file; `.env` remains gitignored.
- [ ] claude.md “Current work-in-progress” reflects what the next agent should do next (if anything).
