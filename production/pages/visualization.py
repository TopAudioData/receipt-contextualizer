import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.express as px
import plotly.graph_objects as go

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
st.sidebar.title('Receipt :receipt::nerd_face::bar_chart: Contextualizer')
st.sidebar.page_link('home.py', label='Home', icon='📊')
st.sidebar.page_link('pages/search.py', label='Search', icon='🔎')
st.sidebar.page_link('pages/upload.py', label='Upload', icon='🧾')
st.sidebar.page_link('pages/data.py', label='Data', icon='🗄️')
st.sidebar.page_link('pages/visualization.py', label='Explainer', icon='🤯')

st.header("How, what, why?!")

# read product data and prepare for visualisation
rewe_products = pd.read_csv('../data/prod_bav_cleaned.csv', index_col=0)
plot_products = rewe_products.copy()
plot_products.drop(['price','image','x_embeds_tsne','y_embeds_tsne'],axis=1,inplace=True)

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

# This function shall plot the embedded products by category 
# - the user can choose which categories shall be plotted
def cluster_plot():

    # Make a list of all categories and add an option to use all categories
    prod_list = rewe_products.category.unique().tolist()
    keys = [num for num in range(17)] # produce a list of unique keys for each category
    prod_list.insert(0,'ALLE')
    categories = st.multiselect('Multiselect', prod_list, key=keys) # creates the selection object for the categories
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
cluster_plot()
