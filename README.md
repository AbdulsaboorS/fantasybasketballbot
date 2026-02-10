# fantasyfootballbot

## CI credential handling

The daily workflow passes ESPN and API credentials directly to `python main.py` as environment variables and does not write credentials into repository files during CI.

The workflow only stages and commits `CONTEXT.md`, and it includes a safeguard that fails the run if staged content appears to include `AEB`/`SWID` credential patterns.
