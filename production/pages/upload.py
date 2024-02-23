'''
Streamlit Sub-Page to Home = main page
Handels the image-file upload and preview, calls receipt-boxing and ocr-function
returns a dataframe with the product name, prices and filenames of the receipts to the database
'''


import streamlit as st
import process_ocr as ocr
import make_boxes as mabo
import read_receipt 
import process_llm as llm

from altair import DerivedStream
import streamlit as st
import pandas as pd
import numpy as np
import time
from io import StringIO
from PIL import Image, ImageDraw

# Page config
st.set_page_config(
    page_title="Receipt contextualizer • Home",
    page_icon=":nerd_face:",
    layout="wide",
    initial_sidebar_state="expanded"
    )


# Page navigation
st.sidebar.title('Receipt :receipt::nerd_face::bar_chart: Contextualizer')
st.sidebar.page_link('home.py', label='Home', icon='📊')
st.sidebar.page_link('pages/search.py', label='Search', icon='🔎')
st.sidebar.page_link('pages/upload.py', label='Upload', icon='🧾')
st.sidebar.page_link('pages/data.py', label='Data', icon='🗄️')
st.sidebar.page_link('pages/visualization.py', label='Explainer', icon='🤯')



st.title('Upload')

# read_receipt function is cached, because it takes long
@st.cache_data
#takes the uploaded image-object and returns recognized text in a df and the boxed-receipt
def create_receipt_value_dict(uploaded_files):
    # dictionary to take the receipt-text-df and the boxed-image
    receipt_value_dict = {}
    #process all uploaded files
    for uploaded_file in uploaded_files: 
                # give the image-object to the function to ocr
                df_sorted, image_boxed = read_receipt.process_receipt(uploaded_file)
                # write the receipt-text-df and the boxed-image into the dictionary
                receipt_value_dict[uploaded_file.name] = [df_sorted, image_boxed]
    # return the dictionary            
    return receipt_value_dict            



# make 2 tabs
tab_Input, tab_Output, tab_Context = st.tabs(["Input", "Output", "Contextualized"])


with tab_Input:
    # make 2 columns on tab "Input"
    col_load_files, col_img= st.columns(2)

# On column "Load files":
with col_load_files:
    st.subheader("Load receipt-files")
    #st.text("   ") #to alignt the widget with the next column
    # File Upload Widget
    uploaded_files = st.file_uploader("Select one or more images-files for upload",\
                                       type=['jpg', 'png', 'bmp', 'pcx', 'tif'], \
                                          accept_multiple_files=True, )
    
    if uploaded_files:
        st.subheader("The following files will be processed:")
        st.markdown("To deselect a file (if it was uploaded by mistake), use the 'x' at the filename from the file-upload above.")
        # extract names of the uploaded files
        file_names = [file.name for file in uploaded_files]
        # create a dataframe of the list of filenames
        df = pd.DataFrame(file_names, columns=['Dateiname'])
        # let the show filenames start with 1 instead of 0
        df.index = df.index + 1
        # Show the dataframe of filenames as table in Streamlit
        st.table(df)
    
# On column "image"
with col_img:
    st.subheader("Receipts preview")
    if uploaded_files:
        # create a Selectbox for the image to be shown
        selected_file_name = st.selectbox("Select an image of a receipt to be shown",\
                                              file_names)
    
        # find the selected image-file and show the image
        for uploaded_file in uploaded_files:
            if uploaded_file.name == selected_file_name:
                # set the size of the image relativ to column width
                col_a, col_b, cl_c= st.columns([1, 8 ,1])
                with col_b:
                    # show the image
                    image = Image.open(uploaded_file)
                    st.image(image, caption=uploaded_file.name, use_column_width=True)
    else:
        st.markdown('<p style="color:red;">Upload image-files on tab "Input" first before receipt output could be shown!</p>', unsafe_allow_html=True)




with tab_Output:

    # make ocr and boxed-images of all uploaded receipts, function is cached
    receipt_value_dict =create_receipt_value_dict(uploaded_files)
    #st.write(receipt_value_dict)

    # predefine the file selection list to avoid an error
    selected_files_output = []
    button = st.button('accept changes', key='top')
    if not uploaded_files:
        # if no files were uploaded prompt the user to do that
        st.markdown('<p style="color:red;">Upload image-files on tab "Input" first before receipt output could be shown!</p>', unsafe_allow_html=True)
    else:  
        # create a Selectbox for the image to be shown
        selected_files_output = st.multiselect("Select one ore more receipt to be shown", \
                                        ["all"]+file_names)
        # check if "all" was selected or there was no selection
        if "all" in selected_files_output or not selected_files_output:
            # then take alle filenames (without "all")
            selected_files_output = file_names
        else:
            # remove double entries
            selected_files_output = list(set(selected_files_output))
        st.text(selected_files_output)

   

    # Show the recognized products and the preview only if files are selected
    if selected_files_output:
        liste_df = []
        c = st.container()
        for file_ocr in selected_files_output: 
            # TODO: loop for df must be over all = uploaded_files. diplay for-loop should stay at selected_files
             
            # make 2 columns on tab "Output"
            col_ocr_data, col_ocr_image = c.columns(2)

            # On column "ocr_data" = "tabel recognized products on the receipt:"
            with col_ocr_data:
                st.subheader("recognized products on the receipt:")
                #df_output = pd.DataFrame
    #   for receipt, (product, price, image_boxed) in receipt_value_dict:
            #   if receipt in selected_files_output:
            #          for product, price in zip(product, price):
               # for file_ocr in selected_files_output:           #df_output.append({'receipt': receipt, 'product': })
                st.write(file_ocr)
                include_on = st.toggle('Activate to include', value=True, key=file_ocr)
                if include_on:
                    st.write('Receipt counted')
                else:
                    st.write('Receipt excluded')
                df = st.data_editor(receipt_value_dict[file_ocr][0],
                               height=(receipt_value_dict[file_ocr][0].shape[0]*37+21),
                               column_config={
                               'date': st.column_config.DateColumn('Date', format='DD.MM.YYYY'),
                               'product_abbr': 'Name on receipt',
                               'receipt_id': 'ID',
                               'price': st.column_config.NumberColumn('Price', format='%.2f €')}, 
                               hide_index=True)      
                if include_on == True:
                    liste_df.append(df) 
               

            # On column "ocr_image" = "preview of the products on the receipt:"
            with col_ocr_image:
                st.subheader("preview of the products on the receipt:")
                # set the size of the image relativ to column width
                col_a, col_b, cl_c= st.columns([1, 8 ,1])
                with col_b:
                    # find the selected image-file-NAMES
                    #for file_ocr in selected_files_output:
                    st.image(receipt_value_dict[file_ocr][1], caption=file_ocr, use_column_width=True)

    # combine all dataframe in the list into a combined dataframe
    combined_df = pd.concat(liste_df, ignore_index=True)      
    #st.dataframe(combined_df, height=(combined_df.shape[0]*37+21))    

    # submit button
    button = st.button('accept changes', key='bottom')

    @st.cache_data
    def write_response_to_df(df=None):
        if df == None:
            df = None
        else:
            df = pd.DataFrame(response_list)
        return df
    response_df = write_response_to_df() 

    if button == True:
        st.write('Start contextualising : :nerd_face:')  
        with st.status('generating names and categories'):
            categories_rewe = llm.get_rewe_categories()
            product_list = combined_df.product_abbr.to_list()
            st.write(product_list)
            response_list = []
            for item in product_list:
                st.write(f'processing {item}')
                response_js = llm.process_abbr_item(item, categories_rewe)   
                response_list.append(response_js)
            
                response_df = write_response_to_df(response_list)
            


with tab_Context:
    st.subheader("Contextualized Receipts")
    if response_df is not None:
        st.table(response_df)
    st.button('Submit', type='primary')
        