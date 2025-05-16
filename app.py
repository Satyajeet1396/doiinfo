import streamlit as st
import requests
import pandas as pd
from io import BytesIO

# Streamlit App Configuration
st.set_page_config(page_title='🔍 CrossRef Metadata Fetcher', layout='wide')

# App Title
st.title('🔍 CrossRef Metadata Fetcher')
st.write('Upload a file with DOIs or enter them manually to fetch metadata from CrossRef.')

def clean_doi(doi):
    """Normalize DOI strings by removing common prefixes and whitespace."""
    prefixes = [
        'https://doi.org/', 
        'http://doi.org/',
        'doi:', 
        'DOI:'
    ]
    doi = str(doi).strip()
    for prefix in prefixes:
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi.strip()

# File upload section
uploaded_file = st.file_uploader("Upload CSV/Excel file with DOIs", 
                               type=['csv', 'xlsx'],
                               help="File should contain a 'DOI' column")

dois_file = []
if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Find DOI column (case-insensitive)
        doi_col = next((col for col in df.columns if col.lower() == 'doi'), None)
        
        if doi_col is not None:
            dois_file = df[doi_col].astype(str).apply(clean_doi).tolist()
            dois_file = [doi for doi in dois_file if doi]  # Remove empty strings
            st.success(f"Found {len(dois_file)} DOIs in uploaded file")
        else:
            st.error("No 'DOI' column found in the uploaded file")
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")

# Manual DOI input
dois_text = st.text_area('Or enter DOIs manually (one per line):', 
                        height=150,
                        help="Separate multiple DOIs with new lines")
dois_text = [clean_doi(doi) for doi in dois_text.split('\n') if doi.strip()]

# Combine and deduplicate DOIs
all_dois = dois_file + dois_text
seen = set()
dois_list = [doi for doi in all_dois if not (doi in seen or seen.add(doi))]

# CrossRef API configuration
API_URL = 'https://api.crossref.org/works/'
HEADERS = {'User-Agent': 'CrossRef-Metadata-Fetcher/1.0 (mailto:your@email.com)'}

@st.cache_data(show_spinner=False)
def fetch_metadata(doi):
    """Fetch metadata from CrossRef API with error handling and proper user-agent."""
    try:
        response = requests.get(f"{API_URL}{doi}", headers=HEADERS)
        if response.status_code == 200:
            return response.json().get('message', {})
        st.error(f"Error {response.status_code} for DOI: {doi}")
    except Exception as e:
        st.error(f"Failed to fetch {doi}: {str(e)}")
    return {}

# Main processing
if st.button('Fetch Metadata'):
    if not dois_list:
        st.warning("Please provide DOIs through file upload or text input")
    else:
        st.info(f"Fetching metadata for {len(dois_list)} unique DOIs...")
        
        # Fetch metadata with progress
        progress_bar = st.progress(0)
        metadata_list = []
        for i, doi in enumerate(dois_list):
            metadata_list.append(fetch_metadata(doi))
            progress_bar.progress((i+1)/len(dois_list))
        
        # Create DataFrame
        if metadata_list:
            df = pd.json_normalize(metadata_list)
            st.write('### Metadata Summary')
            st.dataframe(df.head())
            
            # Download options
            csv_buffer = BytesIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8')
            st.download_button(
                '📥 Download as CSV',
                data=csv_buffer.getvalue(),
                file_name='metadata.csv',
                mime='text/csv'
            )

            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button(
                '📥 Download as Excel',
                data=excel_buffer.getvalue(),
                file_name='metadata.xlsx',
                mime='application/vnd.ms-excel'
            )
        else:
            st.error("No metadata retrieved - check DOI inputs and try again")
