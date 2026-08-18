import os.path
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from clean_email import clean_email_body, is_likely_no_reply
from draft_generator import generate_draft_reply
from save_draft import create_gmail_draft

sys.stdout.reconfigure(encoding="utf-8")

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
PROCESSED_IDS_FILE = "processed_ids.txt"


def get_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_header(headers, name):
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def load_processed_ids():
    if not os.path.exists(PROCESSED_IDS_FILE):
        return set()
    with open(PROCESSED_IDS_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())


def mark_as_processed(message_id):
    with open(PROCESSED_IDS_FILE, "a") as f:
        f.write(message_id + "\n")


def main():
    service = get_service()
    processed_ids = load_processed_ids()

    results = service.users().messages().list(
        userId="me", labelIds=["UNREAD"], maxResults=5
    ).execute()
    messages = results.get("messages", [])

    print(f"Found {len(messages)} unread message(s).")

    if not messages:
        print("No unread messages found.")
        return

    for msg in messages:
        msg_id = msg["id"]

        if msg_id in processed_ids:
            print("-" * 50)
            print(f"Message {msg_id}: Already processed, skipping.")
            continue

        full_msg = service.users().messages().get(
            userId="me", id=msg_id, format="full"
        ).execute()

        headers = full_msg["payload"]["headers"]
        sender = get_header(headers, "From")

        if is_likely_no_reply(sender):
            print("-" * 50)
            print(f"From: {sender}")
            print("Skipped (no-reply/notification sender)")
            mark_as_processed(msg_id)
            continue

        subject = get_header(headers, "Subject")
        body = clean_email_body(full_msg["payload"], subject=subject)

        print("-" * 50)
        print(f"From: {sender}")
        print(f"Subject: {subject}")
        print(f"Cleaned body:\n{body}")

        draft = generate_draft_reply(sender, subject, body)

        if draft is None:
            print("\n[No reply needed — skipped]")
            mark_as_processed(msg_id)
            continue

        print(f"\nDraft reply:\n{draft}")

        if "[DRAFT GENERATION FAILED" in draft:
            print("\n[Skipped saving — draft generation failed, review manually]")
            mark_as_processed(msg_id)
            continue

        message_id_header = get_header(headers, "Message-ID")
        thread_id = full_msg["threadId"]

        create_gmail_draft(
            service=service,
            to_email=sender,
            subject=subject,
            body_text=draft,
            thread_id=thread_id,
            message_id_header=message_id_header,
        )
        print("\n[Saved as Gmail draft]")

        mark_as_processed(msg_id)


if __name__ == "__main__":
    main()