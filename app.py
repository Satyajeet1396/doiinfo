import streamlit as st
import requests
import pandas as pd
from io import StringIO

# Streamlit App Configuration
st.set_page_config(page_title='CrossRef Metadata Fetcher', layout='wide')

# App Title
st.title('🔍 CrossRef Metadata Fetcher')
st.write('Enter a list of DOIs, and fetch their complete metadata from CrossRef.')

# DOI Input
dois = st.text_area('Enter DOIs (one per line):', height=200)
dois_list = [doi.strip() for doi in dois.split('\n') if doi.strip()]

# CrossRef API endpoint
api_url = 'https://api.crossref.org/works/'

@st.cache_data
def fetch_metadata(doi):
    response = requests.get(f'{api_url}{doi}')
    if response.status_code == 200:
        return response.json().get('message', {})
    else:
        st.error(f'Failed to fetch data for DOI: {doi}')
        return {}

# Fetch Data Button
if st.button('Fetch Metadata'):
    if not dois_list:
        st.warning('Please enter at least one DOI.')
    else:
        st.info('Fetching data, please wait...')
        metadata_list = [fetch_metadata(doi) for doi in dois_list]

        # Extract all unique keys
        all_keys = sorted(set().union(*(d.keys() for d in metadata_list)))
        
        # Create DataFrame
        df = pd.DataFrame([{key: str(metadata.get(key, '')) for key in all_keys} for metadata in metadata_list])
        
        # Display DataFrame
        st.write('### Metadata Table')
        st.dataframe(df)

        # CSV Download
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button('Download Metadata as CSV', data=csv_buffer.getvalue(), file_name='crossref_metadata.csv', mime='text/csv')
