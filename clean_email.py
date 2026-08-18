import base64
import re
from bs4 import BeautifulSoup  # pip install beautifulsoup4


def get_plain_text_body(payload):
    """Walk Gmail's payload structure and extract plain text (or fall back to stripped HTML)."""
    def find_part(parts, mime_type):
        for part in parts:
            if part.get("mimeType") == mime_type:
                return part
            if "parts" in part:
                found = find_part(part["parts"], mime_type)
                if found:
                    return found
        return None

    body_data = None

    if "parts" in payload:
        part = find_part(payload["parts"], "text/plain")
        if part and "data" in part.get("body", {}):
            body_data = part["body"]["data"]
        else:
            part = find_part(payload["parts"], "text/html")
            if part and "data" in part.get("body", {}):
                html = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                return BeautifulSoup(html, "html.parser").get_text()
    elif "data" in payload.get("body", {}):
        body_data = payload["body"]["data"]

    if not body_data:
        return ""

    return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")


def strip_quoted_reply(text):
    """Cut off the text at the first sign of a quoted reply chain."""
    patterns = [
        r"\nOn .+ wrote:\n",
        r"\n-{2,}\s*Original Message\s*-{2,}",
        r"\nFrom:\s.+\nSent:\s.+\nTo:\s.+",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            text = text[:match.start()]

    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        if line.strip().startswith(">"):
            break
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def strip_signature(text):
    """Trim off common signoff / signature patterns."""
    signoff_patterns = [
        r"\n--\s*\n",
        r"\nRegards,",
        r"\nBest,",
        r"\nBest regards,",
        r"\nThanks,",
        r"\nSent from my iPhone",
        r"\nSent from my Android",
    ]
    for pattern in signoff_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            text = text[:match.start()]
    return text


def clean_whitespace(text):
    """Collapse repeated blank lines and trim stray whitespace."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_email_body(payload, subject=""):
    """Full pipeline: extract, strip thread/signature, clean whitespace."""
    text = get_plain_text_body(payload)

    is_forward = subject.strip().lower().startswith(("fwd:", "fw:"))

    if not is_forward:
        text = strip_quoted_reply(text)
        text = strip_signature(text)

    text = clean_whitespace(text)
    return text


def is_likely_no_reply(sender):
    """Quick filter for notification/marketing senders that don't need a reply drafted."""
    sender_lower = sender.lower()
    noise_patterns = [
        "no-reply", "noreply", "notifications@", "notification@",
        "donotreply", "do-not-reply", "jobalerts-noreply",
        "career-interests-noreply", "invitations@linkedin",
        "updates@", "digest@", "newsletter@",
    ]
    return any(pattern in sender_lower for pattern in noise_patterns)