from re import M
import markdown
import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.express as px
import plotly.graph_objects as go
import json

from sympy import marcumq

import process_llm as llm

# Page config
st.set_page_config(
    page_title="Receipt contextualizer • Home",
    page_icon=":nerd_face:",
    layout="centered",
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

st.sidebar.divider()

presentation = st.sidebar.toggle('Presentation mode', value=True)


# read product data and prepare for visualisation
rewe_products = pd.read_csv('../data/prod_bav_cleaned.csv', index_col=0)
plot_products = rewe_products.copy()
plot_products.drop(['price','image','x_embeds_tsne','y_embeds_tsne'],axis=1,inplace=True)

# Load categories string for prompt in the interactive widget
categories = llm.get_rewe_categories()


intro, prompting, embeddings = st.tabs(['Intro', 'LLM as classifier model', 'LLM text embeddings'])

with intro:
    st.image('https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExN21neXU2Y2JlYjRoN29xb2Q2N3RxZGVhaWpoZDd6cDJuZmxqNmFzaiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/WRQBXSCnEFJIuxktnw/giphy.gif')

with prompting:
    # 1st step
    st.subheader('Part 1: LLM as classifier model')

    if presentation:
        st.markdown("""
    Prompt engineering
    - Role
    - Clear tasks
    - Limitation: predefined categories
    - Few-shot examples
    - Input
    """)
    else:
        st.markdown("""
    Our goal is to use a large language model as a data source.
    In the case of **RECEIPT CLASSIFIER**, we want it to categorize grocery store products.

    To ensure standardization, we limit its output to a *predefined classes* of grocery store products.

    We scraped the categories of the REWE webshop. We only used the top two levels and excluded overlapping categories. 
    The limitation restricts the LLM to ONLY use these categories to get reliable output.

    We also dialled down the *temperature* of the model, to make it take less *creative freedom*. 
    The categories then can be used to aggregate previously unrelated items.

    The prompt follows this structure
    - Role
        - You are an expert in categorizing items…
    - Task
        - Give a name
        - Categorize
    - Limitations
        - The predefined categories
    - Few-shot examples
        - Examples for correctly categorized abbreviated products
    - Input
        - An abbreviated item from the receipt scan

    Check out our prompt:""")

    st.write('To generate data from receipts, prompt the LLM for each item on a receipt.')

    # Interactive prompt engineering

    interactive_llm_prompt = st.container(height=300, border=True)

    with interactive_llm_prompt:
        

        input, output = interactive_llm_prompt.columns([1,2])
        with input:
            st.subheader('Scanned item')
            query = st.text_input(label='Enter a product', label_visibility='collapsed', value=None)
            

        with output:
            st.subheader('Augmented data')
            if query is not None:
                @st.cache_data
                def mistral_api(query, categories):
                    response = llm.process_abbr_item([query], categories)
                    return response
                response = mistral_api(query, categories)
                st.table(pd.DataFrame(response).T)
            else:
                st.info('👈 Enter an item from a receipt.')
        

    # Display categories used for LLM prompt
    with st.expander('Rewe categories'):
        with open('../data/categories_rewe.json', 'r') as f:
            rewe_categories = json.load(f)
        # Exclude labels
        for excluded_category in ['Vegane Vielfalt', 'International', 'Regional']:
            rewe_categories.pop(excluded_category)
        # Write main and subcategories in readable markdown
        categories_strings = []
        for category in rewe_categories:
            categories_strings.append(f'1. {category}')
            for subcategory in rewe_categories[category]:
                categories_strings.append(f'    - {subcategory}')
        st.markdown('\n'.join(categories_strings))

    # Display prompt
    with st.expander('LLM prompt'):
        prompt = llm.get_prompt(' ', categories)
        st.code(prompt, language='text')

    if not presentation:
        st.markdown("""
        To understand why this works, take a look at embeddings. This also explains some errors,
        when a product is placed in a different category by the model than the supermarked did.
        """)


with embeddings:
    # Understanding Embeddings
    st.subheader('Part 2: LLM text embeddings')


 

    # This function shall plot the embedded products by category 
    # - the user can choose which categories shall be plotted

    # Make a list of all categories and add an option to use all categories
    prod_list = rewe_products.category.unique().tolist()
    keys = [num for num in range(17)] # produce a list of unique keys for each category
    prod_list.insert(0,'ALLE')
    categories = st.multiselect('Multiselect', prod_list) # creates the selection object for the categories
    if "ALLE" in categories:
        categories = prod_list

    # create a dictionary that contains the parts of the rewe_products DF that correspond to the chosen category
    dfs = {cat: rewe_products[rewe_products["category"] == cat] for cat in categories}

    # use a color_scale to make sure all categories are ploted in unique colors
    color_scale = px.colors.qualitative.Light24_r

    fig = go.Figure()
    for idx, (cat, df) in enumerate(dfs.items()):
        color_idx = idx % len(color_scale)
        fig = fig.add_trace(go.Scatter(x=df["x_embeds_tsne"], y=df["y_embeds_tsne"], name=cat, text = df['name'], mode='markers',
                                    marker=dict(color=color_scale[color_idx]),hovertemplate='%{text}'))
    fig.update_layout(title='Visualisation of product name embeddings')   
    st.plotly_chart(fig)

    st.write('Choose product categories for visualisation:')


   # make checkbox for the user to choose, if the data shall be shown
    if st.checkbox('Show product data'):

        # plot the count of products per category    
        fig = px.bar(plot_products.groupby('category').name.count()).update_layout(
            xaxis = {"categoryorder":"total descending"},
            yaxis_title="Sum of expenses in €",
            xaxis_title='',
            showlegend=False,
            title='Number of products per category at REWE')
        st.plotly_chart(fig)
        # print dataframe and show images of the products in the image column
        st.dataframe(rewe_products.drop(['x_embeds_tsne','y_embeds_tsne'],axis=1),
                column_config={
                    'image':st.column_config.ImageColumn('Product Image'),
                    'price':st.column_config.NumberColumn('Price', format='%.2f €'),
                    'name':'Name',
                    'category':'Category'},
                    hide_index=True)