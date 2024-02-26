import streamlit as st

import process_llm as llm
import database as db

COLUMN_NAMES = {
    'id_pk':'ID',
    'receipt_id':'Receipt',
    'receipt_date':'Date',
    'price':'Price',
    'product_abbr':'Name on receipt',
    'product_name':'Name',
    'category_main':'Category',
    'category_sub':'Kind',
    'embedding':'Semantic coordinates',
    'name':'Name', #Rewe db
    'category':'Category' #Rewe db
}

# Page config
st.set_page_config(
    page_title="Receipt contextualizer • Home",
    page_icon=":nerd_face:",
    layout="wide",
    initial_sidebar_state="expanded"
    )

# Hide streamlit menu
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
#root > div:nth-child(1) > div.withScreencast > div > div > header {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

# Page navigation
#st.sidebar.title('Receipt :receipt::nerd_face::bar_chart: Contextualizer')
st.sidebar.image('receipt_logo3.png', use_column_width='always')
st.sidebar.page_link('home.py', label='Home', icon='📊')
st.sidebar.page_link('pages/search.py', label='Search', icon='🔎')
st.sidebar.page_link('pages/upload.py', label='Upload', icon='🧾')
st.sidebar.page_link('pages/data.py', label='Data', icon='🗄️')
st.sidebar.page_link('pages/visualization.py', label='Explainer', icon='🤯')

df = db.data()


col1, col2 = st.columns(2)
with col2:
    # Select target
    query_table = st.radio(
        "Select where to search",
        ['receipts', 'rewe'],
        captions=["Find products in my receipts", "Find products available at REWE"]
    )
with col1:
    # Search input field
    query_user_input = st.text_input(
        'Semantic search', placeholder='Use your own words…', value=None)
    # Select number of results
    n_results = st.slider('Number of search results', value=16)
    
    subcol1, subcol2 = st.columns([1,3])
    with subcol1:
        # Submit button
        semantic_search = st.button('OK', type='primary')

    with subcol2:
        query_results = None
        if semantic_search or query_user_input:
            # Status bar
            with st.status('',expanded=False):
                st.write('Generating embedding for query…')
                query_embedding = llm.get_embeddings_by_chunks([query_user_input], 1)
                st.write('Query database…')
                query_results = db.search(query_embedding, n_results, query_table)


if query_results is not None:
    if query_table == 'rewe':
        st.dataframe(query_results.drop('embedding', axis=1)
                .rename(columns=COLUMN_NAMES)[['Name', 'Price', 'Category']], 
                column_config={
                     'Price': st.column_config.NumberColumn(format='%.2f €')},
                     height=600)
                #.style.format({'Price':'{:.2f} €'})
    elif query_table == 'receipts':
        st.dataframe(query_results.drop('embedding', axis=1)
                .rename(columns=COLUMN_NAMES)[['Name', 'Name on receipt', 'Price', 'Category', 'Kind']],
                column_config={
                     'Price': st.column_config.NumberColumn(format='%.2f €')},
                     height=600)
                #.style.format({'Price':'{:.2f} €'}))






