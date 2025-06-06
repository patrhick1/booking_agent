import base64
from email.mime.text import MIMEText
from src.email_service import EmailService # Reuse the auth logic

class GmailApiService(EmailService):
    """Service for Gmail actions like creating drafts."""

    def create_draft(self, to: str, subject: str, body: str):
        """Creates a draft email in the user's Gmail account."""
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            draft_body = {'message': {'raw': raw_message}}
            draft = self.gmail_service.users().drafts().create(userId='me', body=draft_body).execute()
            print(f"Draft created successfully. Draft ID: {draft['id']}")
            return f"Draft created with ID: {draft['id']}"
        except Exception as e:
            print(f"An error occurred while creating Gmail draft: {e}")
            return f"Error creating draft: {e}"