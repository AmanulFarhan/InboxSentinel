import base64
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail Read Only Permission
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Domains to collect emails from
TARGET_DOMAINS = [
    "linkedin.com",
    "naukri.com",
    "internshala.com",
    "indeed.com",
    "glassdoor.com"
]

# Number of emails to fetch from each domain
MAX_EMAILS_PER_DOMAIN = 50


def get_service():
    creds = None

    try:
        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )
    except:
        pass

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def extract_body(payload):

    if "parts" in payload:

        # First preference: text/plain
        for part in payload["parts"]:
            body = extract_body(part)
            if body:
                return body

    mime = payload.get("mimeType", "")

    data = payload.get("body", {}).get("data")

    if not data:
        return ""

    decoded = base64.urlsafe_b64decode(data).decode(
        errors="ignore"
    )

    if mime == "text/plain":
        return decoded

    if mime == "text/html":
        return BeautifulSoup(
            decoded,
            "html.parser"
        ).get_text(" ", strip=True)

    return ""


service = get_service()

rows = []

for domain in TARGET_DOMAINS:

    print(f"\nFetching emails from {domain}")

    results = service.users().messages().list(
        userId="me",
        q=f"from:{domain}",
        maxResults=MAX_EMAILS_PER_DOMAIN
    ).execute()

    messages = results.get("messages", [])

    print(f"Found {len(messages)} emails")

    for msg in tqdm(messages):

        try:

            email = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="full"
            ).execute()

            headers = email["payload"]["headers"]

            sender = ""
            subject = ""
            date = ""

            for h in headers:

                if h["name"] == "From":
                    sender = h["value"]

                elif h["name"] == "Subject":
                    subject = h["value"]

                elif h["name"] == "Date":
                    date = h["value"]

            body = extract_body(email["payload"])

            body = " ".join(body.split())

            rows.append({
                "domain": domain,
                "sender": sender,
                "subject": subject,
                "date": date,
                "body": body[:10000]
            })

        except Exception as e:
            print("Error:", e)

df = pd.DataFrame(rows)

df.to_csv(
    "job_portal_emails.csv",
    index=False
)

print("\n=================================")
print(f"Saved {len(df)} emails")
print("Output: job_portal_emails.csv")
print("=================================")