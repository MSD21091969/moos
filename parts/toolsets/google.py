"""Google API tools - Gmail integration."""
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any

# Gmail API imports (requires: pip install google-api-python-client google-auth-oauthlib)
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False


# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Paths
_root = Path(__file__).parent.parent
CREDENTIALS_PATH = _root / "credentials.json"
TOKEN_PATH = _root / ".gmail_token.json"
SYNC_STATE_PATH = _root / ".sync_state.json"
SYNC_LOGS_DIR = _root / "sync_logs"


def _get_gmail_service():
    """Authenticate and return Gmail service."""
    if not GMAIL_AVAILABLE:
        raise ImportError("Gmail API not installed. Run: uv add google-api-python-client google-auth-oauthlib")
    
    creds = None
    
    # Load existing token
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    
    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                return None  # Need credentials.json from Google Cloud Console
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save token
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)


def get_last_sync() -> datetime | None:
    """Get last sync timestamp."""
    if SYNC_STATE_PATH.exists():
        data = json.loads(SYNC_STATE_PATH.read_text())
        return datetime.fromisoformat(data.get("last_sync", ""))
    return None


def set_last_sync(timestamp: datetime | None = None):
    """Set last sync timestamp."""
    ts = timestamp or datetime.utcnow()
    SYNC_STATE_PATH.write_text(json.dumps({
        "last_sync": ts.isoformat()
    }))


def fetch_emails(since: datetime | None = None, max_results: int = 50) -> list[dict]:
    """Fetch emails since given date.
    
    Args:
        since: Fetch emails after this date. If None, uses last sync or 24h ago.
        max_results: Maximum emails to fetch.
        
    Returns:
        List of {date, sender, subject, snippet}
    """
    service = _get_gmail_service()
    if not service:
        return [{"error": "Gmail not configured. Need credentials.json from Google Cloud Console."}]
    
    # Default to last sync or 24h ago
    if since is None:
        since = get_last_sync() or (datetime.utcnow() - timedelta(hours=24))
    
    # Gmail query format
    query = f"after:{since.strftime('%Y/%m/%d')}"
    
    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        emails = []
        
        for msg in messages:
            msg_data = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
            
            emails.append({
                "id": msg['id'],
                "date": headers.get('Date', ''),
                "sender": headers.get('From', ''),
                "subject": headers.get('Subject', ''),
                "snippet": msg_data.get('snippet', '')[:100],
            })
        
        return emails
        
    except Exception as e:
        return [{"error": str(e)}]


def gmail_sync() -> str:
    """Sync Gmail and return summary of new emails.
    
    This is the main entry point for the Gmail sync workflow.
    """
    # Ensure sync_logs directory exists
    SYNC_LOGS_DIR.mkdir(exist_ok=True)
    
    # Fetch emails
    last_sync = get_last_sync()
    emails = fetch_emails(since=last_sync)
    
    if not emails:
        return "No new emails since last sync."
    
    if "error" in emails[0]:
        return f"Gmail error: {emails[0]['error']}"
    
    # Format summary
    today = datetime.utcnow().strftime("%Y-%m-%d")
    lines = [f"# Email Sync - {today}", "", f"**Emails since**: {last_sync or 'never'}", f"**Count**: {len(emails)}", ""]
    
    for email in emails:
        lines.append(f"## {email['subject']}")
        lines.append(f"- **From**: {email['sender']}")
        lines.append(f"- **Date**: {email['date']}")
        lines.append(f"- **Preview**: {email['snippet']}...")
        lines.append("")
    
    summary = "\n".join(lines)
    
    # Write to dated file
    output_path = SYNC_LOGS_DIR / f"{today}.md"
    output_path.write_text(summary, encoding="utf-8")
    
    # Update sync state
    set_last_sync()
    
    return f"Synced {len(emails)} emails. Saved to {output_path}"
