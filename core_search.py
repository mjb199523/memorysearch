import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class SemanticSearchEngine:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        # Lightweight local model, downloads once and runs in memory.
        # It creates a 384-dimensional vector for texts. Extremely fast.
        self.model = SentenceTransformer(model_name)
        
    def search(self, query, documents, top_k=5, threshold=0.15):
        """
        Embeds documents and the query on the fly, computes similarity, 
        and returns the results.
        documents should be a list of dicts: {'title': str, 'text': str, 'source': str}
        """
        if not documents:
            return []
            
        # Extract text for embedding (using title + snippet/content context)
        texts_to_embed = [f"{doc['title']}. {doc['text']}" for doc in documents]
        
        # Compute embeddings
        doc_embeddings = self.model.encode(texts_to_embed)
        query_embedding = self.model.encode([query])
        
        # Use cosine similarity to find closest matches
        similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
        
        # Rank the results
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


# --- MOCK FETCHERS FOR DEMONSTRATION/STARTER PURPOSES ---
# In a real app, these fetch temporary data using APIs or os module and return lists of dictionaries.

def fetch_local_files(directory_path=None):
    """
    Scans a local directory for txt, pdf, docx.
    For this starter, we return dummy files matching the user requirements.
    """
    return [
        {
            "id": "local_1",
            "title": "Q3 Cybersecurity Policy.docx",
            "source": "Local File",
            "text": "This document outlines the Meghalaya cybersecurity policy for government networks and schools. It emphasizes data protection, zero-trust architecture, and periodic audits."
        },
        {
            "id": "local_2",
            "title": "Meeting Notes - API Design.txt",
            "source": "Local File",
            "text": "Discussed the API response validation issue. We need to validate payloads before sending them to the backend to avoid internal server errors."
        }
    ]

def fetch_mock_gmail():
    """
    Uses Google Gmail API (via google-api-python-client) to fetch recent emails.
    """
    return [
        {
            "id": "email_1",
            "title": "Re: Project Updates",
            "source": "Gmail",
            "text": "Sumit shared the district mapping API. We can use it to map school locations for the dashboard."
        },
        {
            "id": "email_2",
            "title": "Lunch today?",
            "source": "Gmail",
            "text": "Hey, are we still on for lunch at 1 PM downstairs?"
        }
    ]

def fetch_mock_drive():
    """
    Uses Google Drive API to fetch recent documents.
    """
    return [
        {
            "id": "drive_1",
            "title": "API Specifications v2.pdf",
            "source": "Google Drive",
            "text": "Contains the specifications for the school district mapping services, including endpoints, authentication methods, and rate limits."
        }
    ]
