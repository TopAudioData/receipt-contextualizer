import streamlit as st

import process_llm as llm
import database as db

import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

df = db.data()
st.set_page_config(layout="wide")


st.title('Search')

col1, col2 = st.columns(2)
with col2:
    query_table = st.radio(
        "Select where to search",
        ['receipts', 'rewe'],
        captions=["Find products in my receipts", "Find products available at REWE"]
    )
    n_results = st.slider('Number of search results', value=10)
with col1:
    query_user_input = st.text_input(
        'Semantic search', placeholder='Use your own words…', value=None)
    semantic_search = st.button('Search')

    query_results = None
    if semantic_search or query_user_input:
        with st.status('Searching…', expanded=True):
            st.write('Embedding query…')
            query_embedding = llm.get_embeddings_by_chunks([query_user_input], 1)
            st.write('Fetching data…')
            query_results = db.search(query_embedding, n_results, query_table)



if query_results is not None:
    st.dataframe(query_results.drop(['embedding', 'id_pk'], axis=1))



