import streamlit as st
import pandas as pd

import database as db

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
st.sidebar.image('receipt_logo.png', use_column_width='always')
st.sidebar.page_link('home.py', label='Home', icon='📊')
st.sidebar.page_link('pages/search.py', label='Search', icon='🔎')
st.sidebar.page_link('pages/upload.py', label='Upload', icon='🧾')
st.sidebar.page_link('pages/data.py', label='Data', icon='🗄️')
st.sidebar.page_link('pages/visualization.py', label='Explainer', icon='🤯')
st.sidebar.divider()

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

# Options for dashboard

# Select timeframe
dates = []
try:
    df_timeframe = [df.receipt_date.min().date(), df.receipt_date.max().date()]
    dates = st.sidebar.date_input('Select dates of expenses', value=(df_timeframe),
                                min_value=df_timeframe[0],
                                max_value=df_timeframe[1],
                                format='DD.MM.YYYY')
except:
    pass

# TODO: set date_input state to reset
reset_dates = st.sidebar.button('Reset')

if reset_dates: # Reset button will display full df
    pass 
elif len(dates) == 2: # Dashboard already updates and throws error if only one date is chosen
    # Query df for timeframe for all visualizations on the dashboard
    df = df.query('@dates[0] <= receipt_date <= @dates[-1]') 

if not df.empty:
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
else: 
    st.markdown('<p style="color:red;">Upload image-files on the Upload page first before any receipt data can be shown!</p>', unsafe_allow_html=True)
