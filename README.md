# MemorySearch Pro - AI Memory Assistant

**MemorySearch Pro** is an expert-level AI systems tool designed to help users find documents or emails when they only remember the *context or topic* (e.g., "Find the document where we discussed API validation").

It ensures absolute privacy by utilizing a **zero-storage, temporary session-based pipeline**.

---

## 🏛️ System Architecture Workflow

1. **Query Input & Intent Expansion**: User submits a natural language query. An intent parser expands the query with associated synonyms (e.g., "resume" -> "resume, cv, biodata, profile").
2. **Context-Aware API Fetching**: The expanded query is dynamically injected into Google Drive and Gmail APIs to selectively fetch relevant objects without scraping the entire account.
3. **Deep Content Extraction**: The system parses deeply nested multipart email payloads, specifically downloading and converting attachments (PDF, DOCX, TXT, PPTX) completely in-memory using `io.BytesIO`.
4. **Multi-Vector Semantic Similarity**: We utilize `sentence-transformers` to compute vector cosine similarities strictly in RAM. 
5. **Weighted Priority Ranking**: Matches found inside Attachment Filenames or Attachment Contents hold the highest multiplicative score (+1.5x / +1.4x), ensuring attachments are strongly prioritized as requested. Email subjects, bodies, and standalone documents follow.
6. **Data Destruction**: The moment the Streamlit UI finishes rendering the sorted HTML result payload, the array falls out of scope, safely discarding the user's data from system memory.

---

## ⚙️ Implemented Logic & Features
* **Priority Attachment Search**: Fully parses email attachments, converts internal PDF/DOCX/PPTX streams to text strings on the fly, and uses NLP encoding to verify if the attachment matches the user's intent.
* **Deep Email Search Logic**: Extracts Gmail Payload Headers (`Subject`, `From`, `Date`), Base64 decoded `Text/HTML` bodies via BeautifulSoup, and nested `AttachmentIds`.
* **Result Ranking**: The custom algorithm calculates discrete embedding scores for every sub-part of a document, taking the highest weighted factor (Attachment Name > Attachment Text > Email Subject > Document Text) as the final sort metric.

---

## 🚀 Setup & API Integration

1. **Python Environment**: Ensure you are using `python -m venv venv` and `venv/Scripts/activate`.
2. **Dependency Installation**: `pip install -r requirements.txt` (Now includes `python-pptx` and `beautifulsoup4` for Pro version extraction).
3. **Google API Configuration**: 
   * Navigate to Google Cloud Console.
   * Enable **Gmail API** and **Google Drive API** in the API library.
   * Under **Data Access** / **OAuth Consent Screen**, configure `.../auth/gmail.readonly` and `.../auth/drive.readonly` scopes.
   * Save the Desktop OAuth 2.0 Client credentials locally to this folder as `credentials.json`.
4. **Execution**: `streamlit run app.py`

Enjoy your new personal AI Search Engine!
