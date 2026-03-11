import os
import PyPDF2
import docx
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Google APIs Imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

class SemanticSearchEngine:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        # Lightweight local model, downloads once and runs in memory.
        self.model = SentenceTransformer(model_name)
        
    def search(self, query, documents, top_k=5, threshold=0.15):
        if not documents:
            return []
            
        texts_to_embed = [f"{doc['title']}. {doc['text']}" for doc in documents]
        
        doc_embeddings = self.model.encode(texts_to_embed)
        query_embedding = self.model.encode([query])
        
        similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
        top_indices = np.argsort(similarities)[::-1]
        
        results = []
        for idx in top_indices:
            score = similarities[idx]
            if score >= threshold:
                results.append({
                    'document': documents[idx],
                    'score': float(score)
                })
                
            if len(results) >= top_k:
                break
                
        return results

# --- ACTUAL IMPLEMENTATIONS ---

def fetch_local_files(directory_path, max_files=100):
    """
    Scans a local directory for txt, pdf, docx and extracts text for in-memory processing.
    """
    docs = []
    if not os.path.exists(directory_path):
        return docs
        
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if len(docs) >= max_files:
                break
            
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            text_content = ""
            
            try:
                if ext == '.txt':
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text_content = f.read(1500)
                elif ext == '.pdf':
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        if len(reader.pages) > 0:
                            text_content = reader.pages[0].extract_text()[:1500]
                elif ext == '.docx':
                    doc = docx.Document(file_path)
                    paras = [p.text for p in doc.paragraphs if p.text.strip()]
                    text_content = " ".join(paras)[:1500]
                else:
                    continue
                    
                if text_content.strip():
                    docs.append({
                        "id": file_path,
                        "title": file,
                        "source": "Local File",
                        "text": text_content.strip()
                    })
            except Exception as e:
                pass
                
        if len(docs) >= max_files:
            break
            
    return docs

def get_google_credentials():
    """Handles Google OAuth authentication and token generation."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                return None
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def fetch_gmail(max_results=50):
    """Fetches real recent emails from Gmail account."""
    creds = get_google_credentials()
    if not creds:
        return []
        
    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        docs = []
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='metadata', metadataHeaders=['Subject']).execute()
            
            headers = msg_data.get('payload', {}).get('headers', [])
            subject = "No Subject"
            for header in headers:
                if header['name'] == 'Subject':
                    subject = header['value']
                    break
            snippet = msg_data.get('snippet', '')
            
            docs.append({
                "id": msg['id'],
                "title": subject,
                "source": "Gmail",
                "text": snippet
            })
        return docs
    except Exception as e:
        print(f"Gmail Error: {e}")
        return []

def fetch_google_drive(max_results=50):
    """Fetches real document metadata from Google Drive."""
    creds = get_google_credentials()
    if not creds:
        return []
        
    try:
        service = build('drive', 'v3', credentials=creds)
        # Fetch PDFs, Docs, and Texts
        results = service.files().list(
            pageSize=max_results, 
            fields="nextPageToken, files(id, name, mimeType, description)",
            q="mimeType='application/pdf' or mimeType='application/vnd.google-apps.document' or mimeType='text/plain'"
        ).execute()
        items = results.get('files', [])
        
        docs = []
        for item in items:
            title = item.get('name', 'Unknown')
            # Use description if available, otherwise title (downloading everything would violate speed constraint)
            desc = item.get('description', title)
            docs.append({
                "id": item['id'],
                "title": title,
                "source": "Google Drive",
                "text": desc
            })
        return docs
    except Exception as e:
        print(f"Drive Error: {e}")
        return []
