# Email Responder

An automation that reads unread Gmail messages, decides whether each one needs a reply, and — if so — drafts one using an LLM. Every draft is saved directly into Gmail for the user to review, edit, and send manually. **Nothing is ever sent automatically.**

Runs automatically in the cloud via GitHub Actions every 20 minutes — no local machine needs to be powered on.

## Why draft-only, not auto-send

LLMs can be confidently wrong — invent facts, misjudge tone, or answer questions they have no way of actually knowing (like your calendar availability). Auto-sending removes any chance to catch that before it reaches someone's inbox. Keeping a human in the loop was a deliberate design choice, not a limitation.

## How it works

1. **Fetch** — pulls unread emails via the Gmail API
2. **Filter** — skips no-reply/notification senders (LinkedIn alerts, automated confirmations, etc.) before spending any LLM calls on them
3. **Clean** — strips quoted reply chains and signatures from the email body so the LLM only sees the actual new message; forwarded emails are handled differently, since their quoted content *is* the message
4. **Classify** — the LLM decides whether a reply is genuinely needed at all (skips pure FYI/calendar-confirmation emails), erring toward drafting when uncertain
5. **Draft** — generates a reply in a natural, non-robotic tone, explicitly forbidden from inventing facts about the user (availability, contact details, task status, etc.) — it hedges with "I'll check and confirm" instead of guessing
6. **Save** — writes the draft into Gmail, correctly threaded to the original email, via the Gmail API

## Stack

- Python
- Gmail API (OAuth2) — read + draft-create access
- Groq API (`openai/gpt-oss-120b`) for drafting
- GitHub Actions for scheduling and hosting
- Local/repo-tracked file-based tracking to avoid duplicate drafts on repeat runs

## Setup (local)

1. Create a Google Cloud project, enable the Gmail API, and generate OAuth2 desktop credentials (`credentials.json`)
2. Move the app's OAuth publishing status to "In production" (Google Auth Platform → Audience) — required for stable, long-lived tokens; personal-use apps with under 100 users don't need full verification for this
3. Get a free Groq API key from [console.groq.com](https://console.groq.com)
4. Create a `.env` file:
   ```
   GROQ_API_KEY=your_key_here
   ```
5. Install dependencies:
   ```
   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client groq python-dotenv beautifulsoup4
   ```
6. Run once to authenticate:
   ```
   python fetch_emails.py
   ```

## Automation (cloud, via GitHub Actions)

The workflow at `.github/workflows/email-responder.yml` runs the script every 20 minutes on GitHub's servers.

To deploy your own copy:
1. Fork/clone this repo
2. Add three repository secrets (Settings → Secrets and variables → Actions):
   - `CREDENTIALS_JSON` — full contents of your `credentials.json`
   - `TOKEN_JSON` — full contents of your `token.json` (generated after local auth)
   - `GROQ_API_KEY` — your Groq API key
3. Push to `main` — the workflow runs automatically on schedule, or trigger it manually from the Actions tab

The workflow reconstructs the credential files from secrets at runtime, runs the script, then commits the updated `processed_ids.txt` back to the repo so duplicate-tracking persists across runs (each run starts on a fresh cloud machine with no local memory).

## Known limitations

- Single-user only — tied to one Gmail account's credentials
- GitHub Actions free tier has a monthly minutes cap; 30-minute intervals comfortably fit within it
- Scheduled runs aren't guaranteed to fire at the exact minute (GitHub's cron can be delayed under load)
```



