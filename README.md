# Email Responder

An automation that reads unread Gmail messages, decides whether each one needs a reply, and — if so — drafts one using an LLM. Every draft is saved directly into Gmail for the user to review, edit, and send manually. **Nothing is ever sent automatically.**

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
- Local file-based tracking to avoid duplicate drafts on repeat runs

## Setup

1. Create a Google Cloud project, enable the Gmail API, and generate OAuth2 desktop credentials (`credentials.json`)
2. Get a free Groq API key from [console.groq.com](https://console.groq.com)
3. Create a `.env` file:
   ```
   GROQ_API_KEY=your_key_here
   ```
4. Install dependencies:
   ```
   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client groq python-dotenv beautifulsoup4
   ```
5. Run once to authenticate:
   ```
   python fetch_emails.py
   ```

## Automation

Runs on a schedule via Windows Task Scheduler, checking for new unread emails every 15 minutes.

## Known limitations

- Single-user only — tied to one Gmail account's local credentials
- Requires the machine to be powered on (Task Scheduler doesn't run while the PC is off)
- Google's OAuth "Testing" mode caps this to manually-approved test users; a public/multi-user version would require Google's app verification process
```

