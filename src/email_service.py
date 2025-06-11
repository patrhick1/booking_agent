# src/email_service.py

import imaplib
import email
from email.header import decode_header
import os
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- Gmail Configuration ---
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
SERVICE_ACCOUNT_FILE = 'src/service-account-key.json'

class EmailService:
    """A service to fetch emails from both Gmail and a standard IMAP server."""

    def __init__(self):
        self.gmail_service = self._get_gmail_service()
        # Spam filter keywords from the Make.com scenario
        self.spam_keywords = [
            "delivery status notification", "drink-mouth", "uncle-quite", 
            "sheep-dress", "shown-shown", "meant-funny", "state-forth",
            "whale-floor", "saved-blood", "maybe-least"
        ]
        self.ignore_sender = "aidrian@podcastguestlaunch.com"

    def _get_gmail_service(self):
        """Initialize Gmail service using service account credentials."""
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise ValueError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
        
        # Create credentials from service account file
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=GMAIL_SCOPES)
        
        # For domain-wide delegation, you need to specify the user email to impersonate
        # Get the target email from environment variable
        target_email = os.getenv('GMAIL_TARGET_EMAIL')
        if target_email:
            credentials = credentials.with_subject(target_email)
        
        return build('gmail', 'v1', credentials=credentials)

    def _should_process_email(self, subject, body, sender_email):
        """Replicates the 'Alive Blockers' filter from Make.com."""
        if not sender_email:
            return False
        
        if sender_email.lower() == self.ignore_sender:
            print(f"Skipping email from ignored sender: {sender_email}")
            return False

        lower_subject = subject.lower()
        lower_body = body.lower()
        
        for keyword in self.spam_keywords:
            if keyword in lower_subject or keyword in lower_body:
                print(f"Skipping email due to spam keyword: '{keyword}'")
                return False
        
        return True

    def _clean_text(self, text):
        """Replicates the text cleaning from the Make.com scenario."""
        if not text:
            return ""
        return text.replace(' ', ' ').replace('\t', ' ').replace('\r', '\n')

    def fetch_unread_gmail_emails(self):
        # (This function remains the same, but we'll add the filter and cleaning)
        print("Fetching unread emails from Gmail...")
        results = self.gmail_service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread').execute()
        messages = results.get('messages', [])
        
        email_data = []
        if not messages:
            print("No new messages in Gmail.")
            return []

        for message in messages:
            msg = self.gmail_service.users().messages().get(userId='me', id=message['id']).execute()
            payload = msg['payload']
            headers = payload['headers']
            
            subject, sender_name, sender_email, body = "", "", "", ""

            for header in headers:
                if header['name'].lower() == 'subject':
                    subject = header['value']
                if header['name'].lower() == 'from':
                    sender_info = header['value']
                    sender_name, sender_email = email.utils.parseaddr(sender_info)

            # Extract body
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
            elif 'data' in payload['body']:
                data = payload['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')

            if self._should_process_email(subject, body, sender_email):
                # Combine subject and body as per Make.com logic
                combined_content = f"Subject: {subject}\n\nContent: {body}"
                email_data.append({
                    "subject": subject,
                    "sender_name": sender_name or sender_email.split('@')[0],
                    "sender_email": sender_email,
                    "body": self._clean_text(combined_content) # Use the combined, cleaned text
                })
            
            # Mark email as read
            self.gmail_service.users().messages().modify(userId='me', id=message['id'], body={'removeLabelIds': ['UNREAD']}).execute()
        
        print(f"Fetched and filtered {len(email_data)} new emails from Gmail.")
        return email_data

    def fetch_unread_maildoso_emails(self):
        """Fetches unread emails from Maildoso via IMAP and applies filters."""
        print("Fetching unread emails from Maildoso...")
        try:
            mail = imaplib.IMAP4_SSL(os.getenv('MAILODOSO_IMAP_HOST'), int(os.getenv('MAILODOSO_IMAP_PORT')))
            mail.login(os.getenv('MAILODOSO_USER'), os.getenv('MAILODOSO_PASSWORD'))
            mail.select('inbox')

            status, messages = mail.search(None, 'UNSEEN')
            if status != 'OK':
                print("Error searching for emails in Maildoso.")
                return []
            
            email_ids = messages[0].split()
            
            email_data = []
            if not email_ids:
                print("No new messages in Maildoso.")
                return []

            for e_id in email_ids:
                _, msg_data = mail.fetch(e_id, '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        subject_header = decode_header(msg["Subject"])[0]
                        subject = subject_header[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(subject_header[1] if subject_header[1] else 'utf-8')

                        sender_name, sender_email = email.utils.parseaddr(msg.get("From"))

                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    payload = part.get_payload(decode=True)
                                    body = payload.decode(part.get_content_charset() or 'utf-8', errors='ignore')
                                    break
                        else:
                            payload = msg.get_payload(decode=True)
                            body = payload.decode(msg.get_content_charset() or 'utf-8', errors='ignore')
                        
                        if self._should_process_email(subject, body, sender_email):
                            combined_content = f"Subject: {subject}\n\nContent: {body}"
                            email_data.append({
                                "subject": subject,
                                "sender_name": sender_name or sender_email.split('@')[0],
                                "sender_email": sender_email,
                                "body": self._clean_text(combined_content)
                            })
            
            mail.logout()
            print(f"Fetched and filtered {len(email_data)} new emails from Maildoso.")
            return email_data
        except Exception as e:
            print(f"An error occurred while fetching from Maildoso: {e}")
            return []