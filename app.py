import streamlit as st
from core_search import SemanticSearchEngine, fetch_local_files, fetch_mock_gmail, fetch_mock_drive

# -- Page Config --
st.set_page_config(
    page_title="MemorySearch",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# -- Styles --
st.markdown("""
<style>
    .result-card {
        padding: 1rem;
        border-radius: 8px;
        background-color: #1E1E1E;
        border: 1px solid #333;
        margin-bottom: 1rem;
    }
    .source-badge {
        font-size: 0.8rem;
        background-color: #333;
        color: #fff;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        margin-right: 0.5rem;
    }
    .score-badge {
        font-size: 0.8rem;
        color: #4CAF50;
        float: right;
    }
</style>
""", unsafe_allow_html=True)

# -- Initialization --
@st.cache_resource(show_spinner="Loading AI model (runs locally)...")
def get_search_engine():
    # Load embedding model once per server start
    return SemanticSearchEngine()

engine = get_search_engine()

# -- UI Elements --
st.title("🧠 MemorySearch")
st.markdown("**Find documents and emails using natural language. No data is stored.**")

with st.form("search_form"):
    query = st.text_input("What do you remember about the file or email?", placeholder="e.g. Find the email where we discussed the API validation issue.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        search_local = st.checkbox("Local Documents", value=True)
    with col2:
        search_email = st.checkbox("Email (Gmail)", value=True)
    with col3:
        search_drive = st.checkbox("Google Drive", value=True)
        
    submitted = st.form_submit_button("Search 🔍")

if submitted and query:
    if not any([search_local, search_email, search_drive]):
        st.warning("Please select at least one source to search.")
    else:
        with st.spinner("Searching and matching in-memory..."):
            documents = []
            
            # Fetch data dynamically into memory
            if search_local:
                # Provide a path to search in local system (e.g. Documents folder). For now using a mocked fetch
                documents.extend(fetch_local_files())
                
            if search_email:
                # Requires OAuth flow implementation in production
                documents.extend(fetch_mock_gmail())
                
            if search_drive:
                # Requires OAuth flow implementation in production
                documents.extend(fetch_mock_drive())
                
            # Perform Semantic Search
            if documents:
                results = engine.search(query, documents, top_k=5)
                
                if not results:
                    st.info("No highly relevant matches found. Try rephrasing.")
                else:
                    st.success(f"Found {len(documents)} items in sources. Here are the top matches:")
                    for res in results:
                        doc = res['document']
                        score = res['score']
                        
                        st.markdown(f"""
                        <div class="result-card">
                            <span class="source-badge">{doc['source']}</span>
                            <span class="score-badge">{score:.2f} Match</span>
                            <h4 style="margin: 0.5rem 0;">{doc['title']}</h4>
                            <p style="color: #ccc; font-size: 0.9rem; margin-bottom: 0;">"{doc['text'][:200]}..."</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("No documents could be fetched from the selected sources.")
                
        # At the end of the block, 'documents' and 'results' fall out of scope
        # Data is naturally garbage collected, fulfilling the privacy requirement.
