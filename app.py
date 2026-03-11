import streamlit as st
import os
from core_search import SemanticSearchEngine, fetch_local_files, fetch_gmail, fetch_google_drive

# -- Page Config --
st.set_page_config(
    page_title="MemorySearch",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -- Styles (Dark & Vibrant UI) --
st.markdown("""
<style>
    .result-card {
        padding: 1.2rem;
        border-radius: 8px;
        background-color: #1a1a2e;
        border: 1px solid #16213e;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .source-badge {
        font-size: 0.75rem;
        background-color: #0f3460;
        color: #fff;
        padding: 0.3rem 0.6rem;
        border-radius: 4px;
        margin-right: 0.5rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .score-badge {
        font-size: 0.85rem;
        color: #4CAF50;
        float: right;
        font-weight: bold;
    }
    .result-title {
        color: #e94560;
        margin: 0.5rem 0;
        font-size: 1.2rem;
    }
    .result-text {
        color: #a2a8d3;
        font-size: 0.95rem;
        line-height: 1.4;
    }
</style>
""", unsafe_allow_html=True)

# -- Initialization --
@st.cache_resource(show_spinner="Loading Local AI Embedding Model...")
def get_search_engine():
    return SemanticSearchEngine()

engine = get_search_engine()

# -- Sidebar configuration Setup --
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("1. Local Machine Setup")
    default_dir = os.path.join(os.path.expanduser("~"), "Documents")
    local_dir = st.text_input("Local Folder Path:", 
                              value=default_dir,
                              help="The absolute path to search for .txt, .pdf, and .docx files.")
    
    st.subheader("2. Google API Connect")
    st.markdown("""
    To search Emails and Google Drive:
    1. Go to [Google Cloud Console](https://console.cloud.google.com/).
    2. Create a New Project & Enable **Gmail API** and **Google Drive API**.
    3. Configure OAuth Consent Screen (Add your email as a "Test User").
    4. Go to Credentials > Create Credentials > OAuth Client ID (Desktop App).
    5. Download the JSON file, save it exactly as `credentials.json` in this app's main folder.
    """)
    
    has_creds = os.path.exists("credentials.json")
    if has_creds:
        st.success("✅ `credentials.json` found! Click search to authenticate.")
    else:
        st.error("❌ `credentials.json` missing.")

# -- Main UI Elements --
st.title("🧠 MemorySearch")
st.markdown("### Find documents and emails by remembering the *context* or *topic*. \n *Privacy guarantee: All files are processed completely locally in-memory and instantly discarded.*")

with st.form("search_form"):
    query = st.text_input("What do you remember about the file or email?", placeholder="e.g. Find the document where we discussed the Meghalaya cybersecurity policy.")
    
    st.markdown("**Select Data Sources:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        search_local = st.checkbox("Local Documents", value=True)
    with col2:
        search_email = st.checkbox("Email (Gmail)", value=has_creds, disabled=not has_creds)
    with col3:
        search_drive = st.checkbox("Google Drive", value=has_creds, disabled=not has_creds)
        
    submitted = st.form_submit_button("Search Memory 🔍")

if submitted and query:
    if not any([search_local, search_email, search_drive]):
        st.warning("Please select at least one source to search.")
    else:
        with st.spinner("Fetching data directly into memory (zero persistence)..."):
            documents = []
            
            # 1. Local Search execution
            if search_local:
                docs = fetch_local_files(local_dir, max_files=100)
                if docs:
                    documents.extend(docs)
                else:
                    st.toast(f"Couldn't read valid texts from {local_dir}")
                
            # 2. Gmail Search execution
            if search_email:
                emails = fetch_gmail()
                if emails:
                    documents.extend(emails)
                else:
                    st.toast("No emails extracted or auth failed.")
                
            # 3. Google Drive execution
            if search_drive:
                drive_files = fetch_google_drive()
                if drive_files:
                    documents.extend(drive_files)
                else:
                    st.toast("No Drive files extracted or auth failed.")
                
            # -- Perform Semantic Calculation --
            if documents:
                with st.spinner(f"Running semantic similarity algorithm on {len(documents)} objects..."):
                    results = engine.search(query, documents, top_k=5)
                
                if not results:
                    st.info("No matching contexts found. Try rephrasing based on your memory.")
                else:
                    st.success(f"Processed {len(documents)} total items. Displaying Top matches:")
                    for res in results:
                        doc = res['document']
                        score = res['score']
                        
                        st.markdown(f"""
                        <div class="result-card">
                            <span class="source-badge">{doc['source']}</span>
                            <span class="score-badge">{(score*100):.1f}% Match</span>
                            <h4 class="result-title">{doc['title']}</h4>
                            <p class="result-text">"{doc['text'][:350]}..."</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("No documents could be verified at this given time or sources are empty.")
