import base64
from email.mime.text import MIMEText


def create_gmail_draft(service, to_email, subject, body_text, thread_id, message_id_header):
    """Build a reply MIME message and save it as a Gmail draft in the correct thread."""

    # Ensure subject has "Re:" prefix (skip if already present)
    if not subject.lower().startswith("re:"):
        reply_subject = f"Re: {subject}"
    else:
        reply_subject = subject

    message = MIMEText(body_text)
    message["to"] = to_email
    message["subject"] = reply_subject

    # These headers make Gmail/email clients treat it as a proper reply
    if message_id_header:
        message["In-Reply-To"] = message_id_header
        message["References"] = message_id_header

    raw_bytes = base64.urlsafe_b64encode(message.as_bytes())
    raw_message = raw_bytes.decode("utf-8")

    draft_body = {
        "message": {
            "raw": raw_message,
            "threadId": thread_id,
        }
    }

    draft = service.users().drafts().create(userId="me", body=draft_body).execute()
    return draft