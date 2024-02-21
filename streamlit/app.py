import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.express as px
import plotly.graph_objects as go


# read product data and prepare for visualisation
rewe_products = pd.read_csv('../data/prod_bav_cleaned.csv')
plot_products = rewe_products.copy()
plot_products.drop(['price','image','x_embeds_tsne','y_embeds_tsne'],axis=1,inplace=True)

# make checkbox for the user to choose, if the data shall be shown
if st.checkbox('Show product data'):
    # print dataframe and show images of the products in the image column
    st.data_editor(rewe_products.drop(['x_embeds_tsne','y_embeds_tsne'],axis=1),
               column_config={'image':st.column_config.ImageColumn('Product Image')},hide_index=True)
    # plot the count of products per category
    st.write('Number of products per category')
    st.bar_chart(data = plot_products.groupby('category').name.count())#, x = plot_products.category.unique(), y = plot_products.groupby('category').name.count())


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
