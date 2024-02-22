from math import exp
import streamlit as st
import pandas as pd
import numpy as np
import database as db

import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

st.sidebar.page_link('home.py', label='Home')
st.sidebar.page_link('pages/search.py', label='Search', icon='🔎')
st.sidebar.page_link('pages/upload.py', label='Upload', icon='🧾')
st.sidebar.page_link('pages/visualization.py', label='Visualize', icon='📊')

st.title('Home')

st.write('Check out your receipts in these visualizations')

df = db.data()

st.write(df)

st.header('Expenses by category')
expenses_by_category = df.groupby('category_main').price.sum().reset_index()

expenses_by_category.category_main = expenses_by_category.category_main.astype('category')

st.bar_chart(data=expenses_by_category, x='category_main', y='price')

st.dataframe(expenses_by_category)

st.data_editor(df)