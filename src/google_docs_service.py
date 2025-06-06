# src/google_docs_service.py

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/documents.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
]
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
FOLDER_ID = os.getenv('GOOGLE_PODCAST_INFO_FOLDER_ID') # This is used as a default in one method

class GoogleDocsService:
    """
    A service to interact with Google Drive and Google Docs APIs.
    Handles reading document content and listing files in folders.
    """
    def __init__(self):
        if not SERVICE_ACCOUNT_FILE or not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set or file not found.")
        
        try:
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            self.docs_service = build('docs', 'v1', credentials=credentials)
            self.drive_service = build('drive', 'v3', credentials=credentials)
            print("GoogleDocsService initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize GoogleDocsService: {e}")
            raise

    def get_document_content(self, document_id: str) -> str:
        """Reads a Google Doc and returns its text content."""
        try:
            doc = self.docs_service.documents().get(documentId=document_id).execute()
            content = doc.get('body', {}).get('content', [])
            return self._read_structural_elements(content)
        except Exception as e:
            print(f"Error getting content for document ID {document_id}: {e}")
            return ""

    def _read_structural_elements(self, elements: list) -> str:
        """Recursively reads text from a list of Google Docs structural elements."""
        text = ''
        for value in elements:
            if 'paragraph' in value:
                para_elements = value.get('paragraph').get('elements')
                for elem in para_elements:
                    if 'textRun' in elem:
                        text += elem.get('textRun').get('content')
            elif 'table' in value:
                table = value.get('table')
                for row in table.get('tableRows', []):
                    for cell in row.get('tableCells', []):
                        text += self._read_structural_elements(cell.get('content', []))
        return text

    def get_files_in_folder(self, folder_id: str) -> list:
        """Lists all files and folders within a given Google Drive folder."""
        if not folder_id:
            return []
        try:
            query = f"'{folder_id}' in parents and trashed = false"
            results = self.drive_service.files().list(
                q=query,
                pageSize=200,
                fields='files(id, name, mimeType, webViewLink)'
            ).execute()
            return results.get('files', [])
        except Exception as e:
            print(f"Error getting files for folder ID {folder_id}: {e}")
            return []