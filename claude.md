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

- **Streaming add/drop** uses `espn_transactions.add_drop()`. The correct ESPN write host is **`lm-api-writes.fantasy.espn.com`** (not `lm-api.fantasy.espn.com`).
- **Next step for the user:** Paste the captured **Request URL** and **Request body** (JSON) from a browser add/drop in DevTools. Once provided, the agent should:
  1. Set default or env so the bot uses `lm-api-writes.fantasy.espn.com` and the correct path.
  2. If the user provides the exact JSON body, create a body template with placeholders `{league_id}`, `{team_id}`, `{year}`, `{drop_player_id}`, `{add_player_id}` and wire it via `ESPN_TRANSACTION_URL` and `ESPN_TRANSACTION_BODY` or `ESPN_TRANSACTION_BODY_FILE`.
- User is non-technical; prefer clear, stepwise instructions and ready-to-paste config snippets.

---

## 6. Handoff checklist

When you finish a session, ensure:

- [ ] PROJECT_CONTEXT.md Changelog is updated for any confirmed changes.
- [ ] CONTEXT.md is updated only if run log or deployment status changed (no code/changelog).
- [ ] No secrets in any committed file; `.env` remains gitignored.
- [ ] claude.md “Current work-in-progress” reflects what the next agent should do next (if anything).
