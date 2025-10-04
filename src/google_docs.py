"""Google Docs integration for uploading transcripts and summaries."""

import os
import json
import ssl
import socket
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    import httplib2
except ImportError:
    Request = None
    Credentials = None
    InstalledAppFlow = None
    build = None
    HttpError = None
    httplib2 = None

from .config import GoogleDocsConfig
from .logger import LoggerMixin
from .summarization import DailySummary


class GoogleDocsService(LoggerMixin):
    """Service for integrating with Google Docs API."""
    
    # Scopes required for Google Docs and Drive access
    SCOPES = [
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive.file'
    ]
    
    def __init__(self, config: GoogleDocsConfig):
        self.config = config
        self._docs_service = None
        self._drive_service = None
        self._credentials = None
        self._folder_id = None
        
        if not self._check_dependencies():
            return
        
        self.logger.info("GoogleDocsService initialized")
    
    def _check_dependencies(self) -> bool:
        """Check if required Google API dependencies are installed."""
        if any(dep is None for dep in [Request, Credentials, InstalledAppFlow, build, httplib2]):
            self.logger.error(
                "Google API dependencies not installed. "
                "Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
            )
            return False
        return True
    
    def _create_http_client(self):
        """Create HTTP client with proper SSL configuration."""
        try:
            # Create SSL context with more permissive settings
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Create httplib2 Http instance with SSL context
            http = httplib2.Http(
                timeout=30,
                disable_ssl_certificate_validation=True
            )
            
            return http
        except Exception as e:
            self.logger.warning(f"Could not create custom HTTP client: {e}")
            return None
    
    def authenticate(self) -> bool:
        """Authenticate with Google APIs."""
        if not self.config.enabled:
            self.logger.info("Google Docs integration disabled")
            return False
        
        try:
            creds = None
            token_path = Path(self.config.token_path)
            
            # Load existing credentials
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(str(token_path), self.SCOPES)
            
            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    credentials_path = Path(self.config.credentials_path)
                    if not credentials_path.exists():
                        self.logger.error(f"Credentials file not found: {credentials_path}")
                        self.logger.info("Please download credentials.json from Google Cloud Console")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(credentials_path), self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            
            self._credentials = creds
            
            # Build service objects - use default client (credentials parameter handles auth)
            # Note: http and credentials parameters are mutually exclusive
            try:
                self._docs_service = build('docs', 'v1', credentials=creds)
                self._drive_service = build('drive', 'v3', credentials=creds)
            except Exception as build_error:
                self.logger.error(f"Error building Google API services: {build_error}")
                return False
            
            self.logger.info("Google APIs authenticated successfully")
            return True
            
        except ssl.SSLError as e:
            self.logger.error(f"SSL error authenticating with Google APIs: {e}")
            self.logger.info("Try updating certificates or check network connection")
            return False
        except socket.error as e:
            self.logger.error(f"Network error authenticating with Google APIs: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error authenticating with Google APIs: {e}")
            return False
    
    def ensure_folder_exists(self) -> Optional[str]:
        """Ensure the target folder exists in Google Drive and return its ID."""
        if not self._drive_service:
            return None
        
        if self._folder_id:
            return self._folder_id
        
        try:
            # Search for existing folder
            query = f"name='{self.config.folder_name}' and mimeType='application/vnd.google-apps.folder'"
            results = self._drive_service.files().list(q=query).execute()
            items = results.get('files', [])
            
            if items:
                self._folder_id = items[0]['id']
                self.logger.info(f"Found existing folder: {self.config.folder_name}")
            else:
                # Create new folder
                folder_metadata = {
                    'name': self.config.folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self._drive_service.files().create(body=folder_metadata).execute()
                self._folder_id = folder.get('id')
                self.logger.info(f"Created new folder: {self.config.folder_name}")
            
            return self._folder_id
            
        except HttpError as e:
            self.logger.error(f"Error ensuring folder exists: {e}")
            return None
    
    def create_daily_document(self, date_obj: date, transcript_text: str, summary: Optional[DailySummary] = None) -> Optional[str]:
        """Create a daily document with transcript and summary."""
        if not self._docs_service:
            self.logger.error("Google Docs service not initialized")
            return None
        
        try:
            # Create document title
            title = self.config.document_template.format(date=date_obj.strftime('%Y-%m-%d'))
            
            # Create the document
            document = {
                'title': title
            }
            
            doc = self._docs_service.documents().create(body=document).execute()
            document_id = doc.get('documentId')
            
            # Move to folder if specified
            folder_id = self.ensure_folder_exists()
            if folder_id:
                self._move_to_folder(document_id, folder_id)
            
            # Add content to the document
            self._populate_document(document_id, date_obj, transcript_text, summary)
            
            # Get the document URL
            doc_url = f"https://docs.google.com/document/d/{document_id}"
            
            self.logger.info(f"Created daily document: {title}")
            return doc_url
            
        except HttpError as e:
            self.logger.error(f"Error creating daily document: {e}")
            return None
    
    def _move_to_folder(self, document_id: str, folder_id: str) -> None:
        """Move document to specified folder."""
        try:
            # Get current parents
            file = self._drive_service.files().get(fileId=document_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents'))
            
            # Move to new folder
            self._drive_service.files().update(
                fileId=document_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
            
        except HttpError as e:
            self.logger.error(f"Error moving document to folder: {e}")
    
    def _populate_document(self, document_id: str, date_obj: date, transcript_text: str, summary: Optional[DailySummary] = None) -> None:
        """Populate document with content."""
        try:
            requests = []
            
            # Document header
            header_text = f"Daily Transcript - {date_obj.strftime('%A, %B %d, %Y')}\n\n"
            requests.append({
                'insertText': {
                    'location': {'index': 1},
                    'text': header_text
                }
            })
            
            # Format header
            requests.append({
                'updateTextStyle': {
                    'range': {
                        'startIndex': 1,
                        'endIndex': len(header_text) - 1
                    },
                    'textStyle': {
                        'bold': True,
                        'fontSize': {'magnitude': 16, 'unit': 'PT'}
                    },
                    'fields': 'bold,fontSize'
                }
            })
            
            current_index = len(header_text) + 1
            
            # Add summary section if available
            if summary:
                summary_section = self._create_summary_section(summary)
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': summary_section
                    }
                })
                current_index += len(summary_section)
            
            # Add transcript section
            transcript_header = "Full Transcript\n" + "=" * 50 + "\n\n"
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': transcript_header
                }
            })
            
            # Format transcript header
            requests.append({
                'updateTextStyle': {
                    'range': {
                        'startIndex': current_index,
                        'endIndex': current_index + len("Full Transcript")
                    },
                    'textStyle': {
                        'bold': True,
                        'fontSize': {'magnitude': 14, 'unit': 'PT'}
                    },
                    'fields': 'bold,fontSize'
                }
            })
            
            current_index += len(transcript_header)
            
            # Add transcript text (truncate if too long)
            max_transcript_length = 50000  # Google Docs has limits
            if len(transcript_text) > max_transcript_length:
                transcript_text = transcript_text[:max_transcript_length] + "\n\n[Transcript truncated due to length]"
            
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': transcript_text
                }
            })
            
            # Execute all requests
            if requests:
                self._docs_service.documents().batchUpdate(
                    documentId=document_id,
                    body={'requests': requests}
                ).execute()
            
        except HttpError as e:
            self.logger.error(f"Error populating document: {e}")
    
    def _create_summary_section(self, summary: DailySummary) -> str:
        """Create formatted summary section."""
        section = "Daily Summary\n" + "=" * 50 + "\n\n"
        
        # Basic stats
        section += f"Date: {summary.date.strftime('%A, %B %d, %Y')}\n"
        section += f"Total Duration: {summary.total_duration:.1f} minutes\n"
        section += f"Word Count: {summary.word_count:,}\n"
        section += f"Sentiment: {summary.sentiment.title()}\n\n"
        
        # Summary - Third Person (Analytical)
        section += "Overview (Analytical):\n"
        section += f"{summary.summary}\n\n"
        
        # Summary - First Person (Personal)
        if hasattr(summary, 'summary_first_person') and summary.summary_first_person:
            section += "Personal Reflection:\n"
            section += f"{summary.summary_first_person}\n\n"
        
        # Key topics
        if summary.key_topics:
            section += "Key Topics:\n"
            for topic in summary.key_topics:
                section += f"• {topic}\n"
            section += "\n"
        
        # Action items
        if summary.action_items:
            section += "Action Items:\n"
            for item in summary.action_items:
                section += f"• {item}\n"
            section += "\n"
        
        # Meetings
        if summary.meetings:
            section += "Meetings/Conversations:\n"
            for meeting in summary.meetings:
                section += f"• {meeting.get('title', 'Untitled')}\n"
                if meeting.get('participants'):
                    section += f"  Participants: {', '.join(meeting['participants'])}\n"
                if meeting.get('key_points'):
                    for point in meeting['key_points']:
                        section += f"  - {point}\n"
            section += "\n"
        
        section += "\n"
        return section
    
    def update_document(self, document_id: str, new_content: str) -> bool:
        """Update an existing document with new content."""
        if not self._docs_service:
            return False
        
        try:
            # Get current document content
            doc = self._docs_service.documents().get(documentId=document_id).execute()
            
            # Clear existing content and add new content
            requests = [
                {
                    'deleteContentRange': {
                        'range': {
                            'startIndex': 1,
                            'endIndex': len(doc.get('body', {}).get('content', [{}])[0].get('paragraph', {}).get('elements', [{}])[0].get('textRun', {}).get('content', ''))
                        }
                    }
                },
                {
                    'insertText': {
                        'location': {'index': 1},
                        'text': new_content
                    }
                }
            ]
            
            self._docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            self.logger.info(f"Updated document: {document_id}")
            return True
            
        except HttpError as e:
            self.logger.error(f"Error updating document: {e}")
            return False
    
    def find_document_by_date(self, date_obj: date) -> Optional[str]:
        """Find existing document for a specific date."""
        if not self._drive_service:
            return None
        
        try:
            title = self.config.document_template.format(date=date_obj.strftime('%Y-%m-%d'))
            query = f"name='{title}' and mimeType='application/vnd.google-apps.document'"
            
            results = self._drive_service.files().list(q=query).execute()
            items = results.get('files', [])
            
            if items:
                return items[0]['id']
            
            return None
            
        except HttpError as e:
            self.logger.error(f"Error finding document by date: {e}")
            return None
    
    def get_document_url(self, document_id: str) -> str:
        """Get the URL for a Google Doc."""
        return f"https://docs.google.com/document/d/{document_id}"
    
    def list_documents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent documents in the folder."""
        if not self._drive_service:
            return []
        
        try:
            folder_id = self.ensure_folder_exists()
            if not folder_id:
                return []
            
            query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.document'"
            
            results = self._drive_service.files().list(
                q=query,
                pageSize=limit,
                orderBy='modifiedTime desc',
                fields='files(id, name, modifiedTime, webViewLink)'
            ).execute()
            
            return results.get('files', [])
            
        except HttpError as e:
            self.logger.error(f"Error listing documents: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test the Google API connection."""
        try:
            if not self.authenticate():
                return False
            
            # Try to access Drive
            self._drive_service.files().list(pageSize=1).execute()
            
            self.logger.info("Google API connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Google API connection test failed: {e}")
            return False