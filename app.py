import streamlit as st
import os
import json
from core_search import SemanticSearchEngine, fetch_local_files, fetch_gmail, fetch_google_drive

# -- Handle Streamlit Cloud Secrets --
try:
    if "google_credentials" in st.secrets:
        with open("credentials.json", "w") as f:
            f.write(st.secrets["google_credentials"])
    if "google_token" in st.secrets:
        with open("token.json", "w") as f:
            f.write(st.secrets["google_token"])
except Exception:
    pass


# -- Page Config --
st.set_page_config(
    page_title="MemorySearch | Personal Assistant", 
    page_icon="🧠", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# -- Premium Light UI Styles --
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #f8f9fa;
    }
    
    .main {
        background-color: #f8f9fa;
    }

    /* Header Styling */
    .stHeadingContainer h1 {
        font-weight: 700;
        color: #1a1a1a;
        letter-spacing: -1px;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #6c757d;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* Search Bar Customization */
    div[data-baseweb="input"] {
        border-radius: 12px !important;
        border: 1px solid #e0e0e0 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03) !important;
        transition: all 0.2s ease;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #007bff !important;
        box-shadow: 0 4px 15px rgba(0,123,255,0.1) !important;
    }

    /* Result Card Styling */
    .result-card {
        padding: 1.5rem;
        border-radius: 12px;
        background-color: #ffffff;
        border: 1px solid #f0f0f0;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .result-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.08);
        border-color: #e0e0e0;
    }
    
    .source-badge {
        font-size: 0.7rem;
        background-color: #f1f3f5;
        color: #495057;
        padding: 0.25rem 0.6rem;
        border-radius: 100px;
        margin-right: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        border: 1px solid #dee2e6;
        vertical-align: middle;
    }
    
    .meta-info {
        font-size: 0.85rem;
        color: #adb5bd;
        display: flex;
        align-items: center;
        margin-bottom: 0.8rem;
    }
    
    .result-title {
        color: #212529;
        margin: 0.5rem 0;
        font-size: 1.3rem;
        font-weight: 600;
    }
    
    .sender-name {
        font-weight: 500;
        color: #495057;
        margin-right: 1rem;
    }

    .attachment-pill {
        display: inline-flex;
        align-items: center;
        background-color: #e7f3ff;
        padding: 0.3rem 0.8rem;
        border-radius: 100px;
        font-size: 0.85rem;
        color: #007bff;
        margin: 0.5rem 0 1rem 0;
        border: 1px solid #cce5ff;
        font-weight: 500;
    }
    
    .snippet-box {
        color: #495057;
        font-size: 0.95rem;
        line-height: 1.6;
        background-color: #fdfdfd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
    }
    
    .score-label {
        color: #40c057;
        font-weight: 700;
        float: right;
        font-size: 0.8rem;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #ced4da;
        font-size: 0.8rem;
        margin-top: 4rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# -- Initialization --
@st.cache_resource(show_spinner="Warming up memory assistant...")
def get_search_engine():
    return SemanticSearchEngine()

engine = get_search_engine()

# -- Main UI --
st.title("🧠 MemorySearch")
st.markdown('<p class="subtitle">Your private memory assistant. Find what you actually need, minus the noise.</p>', unsafe_allow_html=True)

# Configuration / Sidebar (Hidden by default but accessible)
with st.sidebar:
    st.header("⚙️ Settings")
    local_dir = st.text_input("Local Folder Path:", value=os.path.join(os.path.expanduser("~"), "Documents"))
    
    st.markdown("---")
    st.subheader("🔑 Google Auth")
    
    has_creds = os.path.exists("credentials.json")
    has_token = os.path.exists("token.json")
    
    if has_creds:
        if has_token:
            try:
                with open("token.json", "r") as f:
                    token_data = json.load(f)
                    expiry = token_data.get("expiry")
                    has_refresh = "refresh_token" in token_data
                    
                    if expiry:
                        from datetime import datetime
                        expiry_dt = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
                        if expiry_dt < datetime.now(expiry_dt.tzinfo):
                            if has_refresh:
                                st.info("🔄 Session Hibernating. It will auto-refresh when you search.")
                                if st.button("Reconnect Google APIs NOW", use_container_width=True):
                                    from core_search import get_google_credentials
                                    if get_google_credentials():
                                        st.rerun()
                            else:
                                st.warning("⚠️ Access Revoked. Re-authentication required.")
                        else:
                            st.success("✅ Google APIs Connected (Active)")
                    else:
                        st.success("✅ Google APIs Connected")
            except Exception:
                st.error("❌ Token Corrupted. Needs Re-authentication.")
        else:
            st.info("ℹ️ Ready to Connect. Authenticate by performing any search.")
    else:
        st.error("❌ Google APIs Missing (credentials.json)")

# Search Form
with st.form("search_form", clear_on_submit=False):
    query = st.text_input(
        "", 
        placeholder="Search for something... e.g. 'Project proposal from last March' or 'Where is my resume?'",
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns([1,1,1])
    with col1: search_email = st.checkbox("Gmail (Primary Only)", value=has_creds, disabled=not has_creds)
    with col2: search_drive = st.checkbox("Google Drive", value=has_creds, disabled=not has_creds)
    with col3: search_local = st.checkbox("Local Documents", value=True)
    
    submitted = st.form_submit_button("Search My Memory", type="primary", use_container_width=True)

# -- Search Logic --
if submitted and query:
    if not (search_email or search_drive or search_local):
        st.warning("Select at least one search source.")
    else:
        with st.spinner("Analyzing memory across sources..."):
            documents = []
            
            # Fetch Data
            if search_local: documents.extend(fetch_local_files(local_dir, max_files=40))
            if search_email: documents.extend(fetch_gmail(query))
            if search_drive: documents.extend(fetch_google_drive(query))

            if documents:
                # Semantic Rank
                results = engine.search(query, documents, top_k=10, threshold=0.12)
                
                if not results:
                    st.info("No clear matches found. Try refining your query.")
                else:
                    st.write(f"Showing top {len(results)} relevant items:")
                    
                    for res in results:
                        att_html = f'<div class="attachment-pill">📎 {res["attachment_name"]}</div>' if res.get('attachment_name') else ''
                        disp_date = res['date']
                        
                        # Determine if result is clickable
                        url = res.get('url')
                        card_header = f"""
                        <div class="meta-info">
                            <span class="source-badge">{res['source']}</span>
                            <span class="sender-name">{res['sender']}</span>
                            <span>&bull; {disp_date}</span>
                        </div>
                        """
                        
                        if url:
                            # Wrap in a link for Gmail/Drive
                            st.markdown(f"""
<a href="{url}" target="_blank" style="text-decoration: none; color: inherit;">
<div class="result-card">
<h3 class="result-title">{res['title']}</h3>
{att_html}
<div class="snippet-box">{res['explanation']}</div>
<div style="font-size: 0.75rem; color: #007bff; margin-top: 0.5rem;">↗ Click to open in browser</div>
</div>
</a>
""", unsafe_allow_html=True)
                        else:
                            # Local file display with "Open File" button
                            with st.container():
                                st.markdown(f"""
<div class="result-card" style="margin-bottom: 0;">
<h3 class="result-title">{res['title']}</h3>
{att_html}
<div class="snippet-box">{res['explanation']}</div>
</div>
""", unsafe_allow_html=True)
                                if st.button(f"Open File: {res['title']}", key=f"btn_{res['id']}"):
                                    try:
                                        os.startfile(res['id'])
                                        st.toast(f"Opening {res['title']}...")
                                    except Exception as e:
                                        st.error(f"Could not open file: {e}")
                                st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.snow()
                st.warning("No data found. Ensure your folders and accounts are accessible.")

st.markdown('<div class="footer">Zero Tracking &bull; Zero Persistence &bull; MemorySearch Alpha &bull; Windows Local Support</div>', unsafe_allow_html=True)
