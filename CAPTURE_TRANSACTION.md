# Capturing ESPN add/drop request for real execution

The bot’s **streaming execute** (add/drop) step does not use the `espn-api` library for writes (it’s read-only for basketball). Instead it POSTs to ESPN’s transaction API. To make that work you have two options:

1. **Use the default URL/body**  
   The code uses a guessed endpoint and a minimal JSON body. If ESPN accepts it, nothing else is needed. If you get HTTP 4xx/5xx or an error in the response, use option 2.

2. **Capture one real add/drop from the ESPN site** and plug the URL and body into the bot.

## How to capture the request

1. **Open your league on ESPN**  
   Go to your league’s main page (e.g. `https://fantasy.espn.com/basketball/team?leagueId=...`).

2. **Open DevTools**  
   - Chrome/Edge: `F12` or right‑click → Inspect → **Network** tab.  
   - Firefox: `F12` → **Network** tab.  
   - Safari: Develop → Show Web Inspector → **Network** tab.

3. **Trigger one add/drop**  
   - Use “Add” on a free agent and “Drop” an existing player (or use “Add & Drop” in one step).  
   - Submit the transaction so ESPN sends the request (you can cancel after if you don’t want the move).

4. **Find the transaction request**  
   - In the Network list, look for a request that:  
     - **Method** is **POST**.  
     - **URL** contains things like `fantasy`, `league`, `transaction` (e.g. `lm-api.fantasy.espn.com` or `fantasy.espn.com` and `transactions` in the path).  
   - Click that request and check:  
     - **Request URL** (full URL).  
     - **Request payload** (Payload / Request / JSON body).

5. **Copy into the bot**  
   - **URL**  
     - Set in `.env`:  
       `ESPN_TRANSACTION_URL=<paste the full request URL>`  
     - If the URL already includes your league id and season, you can use it as-is. The code only uses this when set; otherwise it builds a default URL.  
   - **Body**  
     - If the body is JSON, copy it.  
     - Replace your actual league id, team id, year, and the two player ids with placeholders:  
       `{league_id}`, `{team_id}`, `{year}`, `{drop_player_id}`, `{add_player_id}`.  
     - Then either:  
       - Put the JSON string in `.env` as `ESPN_TRANSACTION_BODY=...` (escape quotes for your shell), or  
       - Save it to a file (e.g. `transaction_body.json`) and set in `.env`:  
         `ESPN_TRANSACTION_BODY_FILE=transaction_body.json`

6. **Restart and test**  
   Restart the backend (and run a dry run first if you prefer). When you execute streaming, the bot will use your captured URL and body (with placeholders filled from the current league/team/players).

## Optional: only override the body

- Leave `ESPN_TRANSACTION_URL` unset to use the default built-in URL.  
- Set only `ESPN_TRANSACTION_BODY` or `ESPN_TRANSACTION_BODY_FILE` so the bot uses your captured JSON body with the default URL.  
This is useful when the default URL is correct but the default body shape is wrong.

## Security

- Do **not** put your real `espn_s2` or `SWID` in any file you commit. Keep them only in `.env` (and ensure `.env` is in `.gitignore`).  
- The captured URL does not contain your cookies; the bot sends cookies from `.env` when making the POST.
