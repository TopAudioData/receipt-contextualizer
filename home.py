'''
Start RECEIPT CONTEXTUALIZER by running
streamlit run home.py 
in Terminal
'''

# Import libraries:
import streamlit as st
import pandas as pd
import datetime as dt
import plotly.express as px

# Import script-files:
import database as db

# Page config
st.set_page_config(
    page_title="Receipt contextualizer • Home",
    page_icon=":nerd_face:",
    layout="centered",
    initial_sidebar_state="expanded"
    )

# Hide streamlit menu and reduce padding on top of the page
hide_streamlit_style = """
<style>
.block-container {padding-top: 1rem;}
#MainMenu {visibility: hidden;}
#root > div:nth-child(1) > div.withScreencast > div > div > header {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

## Sidebar:
# Show the logo
st.sidebar.image('images/receipt_logo.png', use_column_width='always')
# Page navigation
st.sidebar.page_link('home.py', label='Home', icon='📊')
st.sidebar.page_link('pages/search.py', label='Search', icon='🔎')
st.sidebar.page_link('pages/upload.py', label='Upload', icon='🧾')
st.sidebar.page_link('pages/data.py', label='Data', icon='🗄️')
st.sidebar.page_link('pages/visualization.py', label='Explainer', icon='🤯')
st.sidebar.divider()

# Get receipts data from database
df = db.data()
df['receipt_date'] = pd.to_datetime(df['receipt_date'])
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

# Set the color-schema for plots
color_scale = px.colors.qualitative.Alphabet


## Options for dashboard
# Show subcategories
toggle_subcategories = st.sidebar.toggle(':eyes: I need details!')

# Select timeframe for available data
dates = []
try:
    df_timeframe = [df.receipt_date.min().date(), df.receipt_date.max().date()]
except:
    pass
# Create a placeholder for selection of date
placeholder = st.sidebar.empty()

# Reset-Button to reset the selected-date to available date
reset_dates = st.sidebar.button('Reset')

# Widget to select the dates at the location of the placeholder
dates=placeholder.date_input('Select dates of expenses', value=(df_timeframe),
                            min_value=df_timeframe[0],
                            max_value=df_timeframe[1],
                            format='DD.MM.YYYY', key='selected_date')

if reset_dates: # Reset button will display full available dates
    # Reset both the dates and the date_input widget. The placeholder is replaced for resetting
    dates=placeholder.date_input('Select dates of expenses', value=(df_timeframe),
                                min_value=df_timeframe[0],
                                max_value=df_timeframe[1],
                                format='DD.MM.YYYY', key='reset_date')
elif len(dates) == 2: # Dashboard already updates and throws error if only one date is chosen
    # Query df for timeframe for all visualizations on the dashboard
    df = df.query('@dates[0] <= receipt_date <= @dates[-1]') 


# Check if a receipt was already uploaded. If not, prompt the user to do so. Otherwise, show expenses and infos from the uploaded receipts
if df.empty:
    st.markdown('<p style="color:red;">Upload image-files on the Upload page first before any receipt data can be shown!</p>', unsafe_allow_html=True)
else:
    # Overview over spending at a glance
    metric1, metric2, metric3 = st.columns(3, gap='small')

    with metric1:
        total_spending = df.price.sum()
        st.metric(':money_with_wings: Total spending', 
                value=f'{round(total_spending, 2)} €')
    with metric2:
        most_spending_category = df.groupby('category_main').price.sum().sort_values(ascending=False).reset_index().iloc[0].to_list()
        st.metric(':gem: Most expensive category', 
                value=f'{round(most_spending_category[1], 2)} €', 
                delta=most_spending_category[0], 
                delta_color='off')
    with metric3:
        top_count_category = df.loc[df['price']>0].category_sub.value_counts().reset_index().iloc[0].to_list()
        st.metric(':shopping_bags: Most common kind of product',
                value=top_count_category[0],
                delta=f'Bought {top_count_category[1]} times',
                delta_color='off')







    header, radio = st.columns([2,3])
    with header:
        st.header('My expenses per')
    with radio:
        aggregate_state = st.radio('Select period', ['day', 'month'], 
                                horizontal=True, label_visibility='hidden',
                                index=1)
    if aggregate_state == 'day':
        if not toggle_subcategories:
            #
            # Barplot over time one color
            #
            fig = px.bar(df.rename(columns=column_names).sort_values(by='Date'), 
                            x='Date', y='Price',
                            hover_data=['Category', 'Kind', 'Name', 'Name on receipt']
                            )
            #fig.update_traces(hovertemplate='') # TODO: fails to display hover_data
            fig.update_layout(
                    yaxis_title="Sum of receipts in €",
                    xaxis_title='',
                    showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            #
            # Barplot over time with colors by category
            #
            fig = px.bar(df.rename(columns=column_names).sort_values(by='Date'), 
                            x='Date', y='Price',
                            color='Category',
                            color_discrete_sequence=color_scale,
                            hover_data=['Kind', 'Name', 'Name on receipt'])
            fig.update_layout(
                    yaxis_title="Sum of receipts in €",
                    xaxis_title='',
                    showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    elif aggregate_state == 'month':
        if not toggle_subcategories:
            #
            # Histogram of expenses by month
            #
            fig = px.histogram(
                df.rename(columns=column_names), 
                x="Date", 
                y="Price", 
                histfunc="sum")
            fig.update_traces(xbins_size="M1")
            fig.update_xaxes(ticklabelmode="period", dtick="M1", tickformat="%b\n%Y")
            fig.update_layout(bargap=0.1, yaxis_title='Sum of expenses in €', xaxis_title='')
            st.plotly_chart(fig, use_container_width=True)
        else:
            #
            # Histogram of expenses by month with categories
            #
            fig = px.histogram(
                df.rename(columns=column_names), 
                x="Date", 
                y="Price", 
                histfunc="sum",
                color='Category',
                color_discrete_sequence=color_scale,
                hover_data=['Kind', 'Name', 'Name on receipt'])
            fig.update_traces(xbins_size="M1")
            fig.update_xaxes(ticklabelmode="period", dtick="M1", tickformat="%b\n%Y")
            fig.update_layout(bargap=0.1, yaxis_title='Sum of expenses in €', xaxis_title='', showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            



    # Choose with toggle if subcategories are colored in
    if not toggle_subcategories:
        #
        # Show h-bar of categories
        #
        fig = px.bar(df.rename(columns=column_names),
                    x='Price', y='Category', 
                    hover_data=['Name'], # TODO:hoverdata
                    orientation='h',
                    )
        #fig.update_traces(hovertemplate='%{x} €')
        fig.update_layout(
            yaxis = {"categoryorder":"total ascending"},
            xaxis_title="Sum of expenses in €")

        st.plotly_chart(fig, use_container_width=True)
    else:
        #
        # H-bar chart with subcategories
        #

        fig = px.bar(df.rename(columns=column_names), 
                    x='Price', y='Category', 
                    color='Kind', 
                    color_discrete_sequence=color_scale,
                    hover_data=['Kind', 'Name', 'Price'],
                    orientation='h')
        #fig.update_traces(hovertemplate='%{x} €') # TODO: hovertemplate '%{Kind}: {Price}' fails
        #fig.update_traces(color=color_scale)
        fig.update_layout(
            yaxis = {"categoryorder":"total ascending"},
            xaxis_title="Sum of expenses in €",
            showlegend=False)


        st.plotly_chart(fig, use_container_width=True)


    with st.expander('Tables…',):
        # Display data of monthly expenses by category
        # Group by Month, put categories as rows, months as col

        #
        #   Table with sum per main category
        #
        st.write('Sums of product **main categories** per month')
        df_monthly = (df.set_index('receipt_date')
                    .groupby([pd.Grouper(freq='M'), 'category_main'])
                    .price.sum().unstack().fillna(0).T)
        # Prettify with formatting the months as Jan 24
        df_monthly.columns = [x.strftime('%b %Y') for x in df_monthly.columns.to_list()]
        # Delete index name
        df_monthly.index.rename(None, inplace=True)
        # Prettify with formatting all number cols as currency
        df_monthly = df_monthly.style.format(dict.fromkeys(df_monthly.select_dtypes(include='number').columns.tolist(), '{:.2f} €'))

        st.dataframe(df_monthly)

        #
        #   Table with sum per subcategory
        #
        st.write('Sums of product **subcategories** per month')
        df_monthly_sub = (df.set_index('receipt_date')
                    .groupby([pd.Grouper(freq='M'), 'category_sub'])
                    .price.sum().unstack().fillna(0).T)
        # Prettify with formatting the months as Jan 24
        df_monthly_sub.columns = [x.strftime('%b %Y') for x in df_monthly_sub.columns.to_list()]
        # Delete index name
        df_monthly_sub.index.rename(None, inplace=True)
        # Prettify with formatting all number cols as currency
        df_monthly_sub = df_monthly_sub.style.format(dict.fromkeys(
            df_monthly_sub.select_dtypes(include='number').columns.tolist(), 
            '{:.2f} €'))
        
        st.dataframe(df_monthly_sub)


    if False:
        # Show all data and edit data in expander
        with st.expander('Your groceries spendings, all in on place…'):
            full_data = st.toggle('Edit data')
            if full_data:
                # Show an editable df
                st.data_editor(df.rename(columns=column_names))
                # TODO: Embed edited entries and overwrite entry in db
                st.button('Submit Edits', type='primary')
            else:
                # Show prettified dataframe
                df['Date'] = df_dates.receipt_date.dt.strftime('%d.%m.%Y')
                st.dataframe(df[['Date', 'product_name', 'category_sub', 'price']]
                            .sort_values(by='Date')
                            .rename(columns=column_names)
                            .style.format({'Price':'{:.2f} €'}))

