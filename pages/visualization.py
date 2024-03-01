from re import M
import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.express as px
import plotly.graph_objects as go
import json

import process_llm as llm
import database as db

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
rewe_products = pd.read_csv('data/prod_bav_cleaned.csv', index_col=0)
plot_products = rewe_products.copy()
plot_products.drop(['price','image','x_embeds_tsne','y_embeds_tsne'],axis=1,inplace=True)

# Load categories string for prompt in the interactive widget
categories = llm.get_rewe_categories()


prompting, embeddings = st.tabs(['LLM as classifier model', 'LLM text embeddings'])


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
                #st.info('👈 Enter an item from a receipt.')
                pass
        

    # Display categories used for LLM prompt
    with st.expander('Rewe categories'):
        with open('data/categories_rewe.json', 'r') as f:
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
    
    with st.expander('Augmented data'):
        #Get receipts data from database
        df = db.data()
        column_names = {
            'id_pk':'ID',
            'receipt_id':'Receipt',
            'receipt_date':'Date',
            'price':'Price',
            'product_abbr':'Name on receipt',
            'product_name':'Name',
            'category_main':'Category',
            'category_sub':'Kind',
            'embedding':'Semantic coordinates'
        }

        # For prototype: insert dates
        receipt_ids =   ['Rewe_1.jpg', 'Rewe_2.jpg', 'Rewe_3.jpg', 'Rewe_4.jpg', 'Rewe_5.jpg', 'Rewe_6.jpg', 'Rewe_7.jpg', 'Rewe_8.jpg', 'Rewe_9.jpg', 'Rewe_10.jpg', 'Rewe_11.jpg', 'Rewe_12.jpg', 'Rewe_13.jpg', 'Rewe_14.jpg']
        receipt_dates = ['20.01.2024', '12.12.2023', '30.12.2023', '13.12.2023', '08.11.2023', '11.11.2023', '18.11.2023', '11.11.2023', '07.11.2023', '22.01.2024',  '04.12.2023',  '09.02.2024',  '20.12.2023',  '03.01.2024']

        df_dates = pd.DataFrame(zip(receipt_ids, receipt_dates), columns=['receipt_id', 'receipt_date'])
        df_dates.receipt_date = pd.to_datetime(df_dates.receipt_date, dayfirst=True)
        df = df.join(df_dates.set_index('receipt_id'), on='receipt_id')




        # Show all data and edit data in expander

        full_data = st.toggle('Show :receipt::nerd_face::bar_chart: generated data')
        if full_data:
            # Show AI generated data
            st.dataframe(df.rename(columns=column_names).sort_values(by='Date', ascending=False)
                        [['Date', 'Name on receipt', 'Price', 'Name', 'Category', 'Kind']], # TODO: add back in 'Receipt' after presentation
                        column_config={
                            'Date': st.column_config.DateColumn(format='DD.MM.YYYY'),
                            'Price': st.column_config.NumberColumn(format='%.2f €')},
                            height=600,
                            hide_index=True)
            # TODO: Embed edited entries and overwrite entry in db
            #st.button('Submit Edits', type='primary')
        else:
            # Show prettified dataframe
            st.dataframe(df.rename(columns=column_names).sort_values(by='Date', ascending=False)
                        [['Date', 'Name on receipt', 'Price']], # TODO: add back in 'Receipt' after presentation
                        column_config={
                            'Date': st.column_config.DateColumn(format='DD.MM.YYYY'),
                            'Price': st.column_config.NumberColumn(format='%.2f €')},
                            height=600,
                            hide_index=True)


with embeddings:
    # Understanding Embeddings
    st.subheader('Part 2: LLM text embeddings')


    example, tsne = st.tabs(['Embeddings in general', 'Semantic space'])

    with example:
        #formula = st.container(height=400, border=False)
        #_, center, _ = formula.columns([1,2,1])
        #with formula:
        st.markdown('# \n# ')
        st.latex('\mathrm{king} - \mathrm{man} + \mathrm{woman} = \mathrm{queen}')

    with tsne:
        # This function shall plot the embedded products by category 
        # - the user can choose which categories shall be plotted

        # Make a list of all categories and add an option to use all categories
        prod_list = rewe_products.category.unique().tolist()
        keys = [num for num in range(17)] # produce a list of unique keys for each category
        prod_list.insert(0,'ALLE')
        categories = st.multiselect('Multiselect', prod_list, default='ALLE', label_visibility='collapsed') # creates the selection object for the categories
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
        fig.update_layout(title='REWE assortment Mistral embeddings (1024 dimensions reduced with t-SNE)')   
        st.plotly_chart(fig)


    if not presentation:
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
        