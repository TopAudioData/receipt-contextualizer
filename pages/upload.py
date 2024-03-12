'''
Streamlit Sub-Page to Home = main page
Handels the image-file upload and preview, calls receipt-boxing and ocr-function
returns a dataframe with the product name, prices and filenames of the receipts to the database
'''


import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw


import read_receipt 
import process_llm as llm
import database as db


# Set page configuration
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





### Cached Functions

# Cache the read_receipt function because it takes a long time to run
@st.cache_data
# This function takes the uploaded image-object and returns recognized text in a df and the boxed-receipt
def create_receipt_value_dict(uploaded_files):
    # Dictionary to store the receipt-text-df and the boxed-image
    receipt_value_dict = {}
    # Process all uploaded files
    for uploaded_file in uploaded_files: 
                # Pass the image-object to the function to OCR
                df_sorted, image_boxed = read_receipt.process_receipt(uploaded_file)
                # Write the receipt-text-df, the boxed-image into the dictionary and the label to take this receipt into account
                receipt_value_dict[uploaded_file.name] = [df_sorted, image_boxed, True]
    # Return the dictionary 
    print('function create_receipt_value_dict was running')           
    return receipt_value_dict

# Store the dataframe resulting the 'include' selection after OCR
@st.cache_data
def write_receipt_value_dict_to_df(_receipt_value_dict): # underscore prohibits streamlit from hashing
    # Structure of dict: receipt_value_dict[uploaded_file.name] = [df_sorted, image_boxed, True]

    liste_df = []
    for uploaded_file_name in _receipt_value_dict: # type: ignore
        # if the receipt was included
        if _receipt_value_dict[uploaded_file_name][2]:
            # Extract the dataframe in the dictionary 
            df = _receipt_value_dict[uploaded_file_name][0] 
            # Write the dataframe of this receipt into the list of receipts
            liste_df.append(df)
    if len(liste_df) > 1:
        # combine all dataframe in the list into a combined dataframe
        combined_df = pd.concat(liste_df, ignore_index=True)
    else:
        # In case there's only one receipt TODO: check if necessary step
        combined_df = liste_df[0]
    return combined_df

# Prompt the llm to augment data, return df with complete information
@st.cache_data
def prompt_llm_for_responses(combined_df):

    categories_rewe = llm.get_rewe_categories()
    product_list = combined_df.product_abbr.to_list()

    response_list = []
    for i, item in enumerate(product_list):
        n = len(product_list)
        st.write(f'Processing {i + 1} of {n}: {item}')
        response_js = llm.process_abbr_item(item, categories_rewe)
        st.write(response_js)
        response_list.append(response_js)

    # Make df from augmented data jsons
    response_df = pd.DataFrame(response_list)
    
    # Join with information in combined_df (date, receipt_ID)
    augmented_df = combined_df.join(response_df.drop('product_abbr', axis=1))

    return augmented_df

# Process the augmented data with mistral to get embeddings
@st.cache_data
def embed_data(df):
    embedded_df = llm.embed_augmented_data(df)
    return embedded_df


### Session state to save buttons' states
if 'stage' not in st.session_state:
    # Stage 0: Initialization
    # Stage 1: Files are uploaded and automatically OCR'd
    # Stage 2: User has selected which receipts to include for augmentation, button "Contextualize" is clicked
    # Stage 3: User clicked button "Submit", writing to database
    st.session_state.stage = 0
def set_state(i):
    st.session_state.stage = i


# UI

st.title('Receipt upload')

# Create tabs
tab_Input, tab_Output, tab_Context = st.tabs(["Input", "Output", "Contextualized"])

with tab_Input:
    # Create 2 columns on tab "Input"
    col_load_files, col_img= st.columns(2)

# On column "Load files":
with col_load_files:
    st.subheader("Load receipt-files")
    # File Upload Widget
    uploaded_files = st.file_uploader("Select one or more images-files for upload",\
                                    type=['jpg', 'png', 'bmp', 'pcx', 'tif'], \
                                        accept_multiple_files=True, 
                                        on_change=set_state, args=[1])
    # As soon as image-files were uploaded, show the filenames in a table
    if uploaded_files:
        st.subheader("The following files will be processed:")
        st.markdown("To deselect a file (if it was uploaded by mistake), use the 'x' at the filename from the file-upload above.")
        # Extract names of the uploaded files
        file_names = [file.name for file in uploaded_files]
        # Create a dataframe of the list of filenames
        df = pd.DataFrame(file_names, columns=['Dateiname'])
        # Let Index of the filenames to show start with 1 instead of 0
        df.index = df.index + 1
        # Show the dataframe of filenames as table in Streamlit
        st.table(df)
    
# On column "image"
with col_img:
    st.subheader("Receipts preview")
    # As soon as image-files were uploaded, show the images of the receipts
    if uploaded_files:
        # Create a Selectbox for the image to be shown
        selected_file_name = st.selectbox("Select an image of a receipt to be shown",\
                                            file_names)
    
        # Find the selected image-file and show the image
        for uploaded_file in uploaded_files:
            if uploaded_file.name == selected_file_name:
                # Set the size of the image relativ to column width
                col_a, col_b, cl_c= st.columns([1, 8 ,1])
                with col_b:
                    # Show the image
                    image = Image.open(uploaded_file)
                    st.image(image, caption=uploaded_file.name, use_column_width=True)
    else: # If there is nothing to show, because no files are uploaded, show this message
        st.markdown('<p style="color:red;">Upload image-files on tab "Input" first before receipt output could be shown!</p>', unsafe_allow_html=True)





with tab_Output:
    if uploaded_files:
    # Perform OCR and create boxed-images of all uploaded receipts, function is cached
        receipt_value_dict = create_receipt_value_dict(uploaded_files)
    #st.write(receipt_value_dict)

    # Predefine the file selection list to avoid an error
    selected_files_output = []

    # Submit button at the top
    button_top = st.button('Contextualize', type='primary', key='top', on_click=set_state, args=[2])
    
    if not uploaded_files:
        # If no files were uploaded prompt the user to do that
        st.markdown('<p style="color:red;">Upload image-files on tab "Input" first before receipt output could be shown!</p>', unsafe_allow_html=True)
    else:  
        # Create a Selectbox for the image to be shown
        #selected_files_output = st.multiselect("Select one ore more receipt to be shown", \
                                     #   ["all"]+file_names)
        # Check if "all" was selected or there was no selection
        if "all" in selected_files_output or not selected_files_output:
            # tTen take alle filenames (without "all")
            selected_files_output = file_names
        else:
            # Remove double entries
            selected_files_output = list(set(selected_files_output))
        #st.text(selected_files_output)

    # Show the recognized products and the preview only if files are selected
    count = 0
    if selected_files_output:
        c = st.container()
        for uploaded_file_name in receipt_value_dict:  # type: ignore
            # TODO: loop for df must be over all = uploaded_files. diplay for-loop should stay at selected_files
            count +=1
            print('for-loop file_ocr was running:' + str(uploaded_file_name) + str(count) )     
            # make 2 columns on tab "Output"
            col_ocr_data, col_ocr_image = c.columns(2)
            # On column "ocr_data" = "table recognized products on the receipt:"
            with col_ocr_data:
                if uploaded_file_name in selected_files_output:
                    st.subheader("recognized products on the receipt:")
                    st.write(uploaded_file_name)             
                    include_on = receipt_value_dict[uploaded_file_name][2]
                    #print(f'include vor toggle{include_on}')
                    include_on = st.toggle('Activate to include', value = include_on, key=uploaded_file_name)
                    #print(f'include nach toggle{include_on}')
                    if uploaded_file_name in selected_files_output:
                        receipt_value_dict[uploaded_file_name][2] = include_on
                    if include_on:
                        st.write('Receipt counted')                   
                    else:
                        st.write('Receipt excluded')
                    st.data_editor(receipt_value_dict[uploaded_file_name][0],
                                        height=(receipt_value_dict[uploaded_file_name][0].shape[0]*37+21),
                                        column_config={
                                        'date': st.column_config.DateColumn('Date', format='DD.MM.YYYY'),
                                        'product_abbr': 'Name on receipt',
                                        'receipt_id': 'ID',
                                        'price': st.column_config.NumberColumn('Price', format='%.2f €')}, 
                                        hide_index=True)      

                    # On column "ocr_image" = "preview of the boxed products on the receipt:"
                    with col_ocr_image:
                        st.subheader("preview of the products on the receipt:")
                        # set the size of the image relativ to column width
                        col_a, col_b, cl_c= st.columns([1, 8 ,1])
                        with col_b:
                            # find the selected image-file-NAMES
                            #for file_ocr in selected_files_output:
                            st.image(receipt_value_dict[uploaded_file_name][1], caption=uploaded_file_name, use_column_width=True)
        

    # submit button at the bottom
    button_bottom = st.button('Contextualize', type='primary', key='bottom', on_click=set_state, args=[2])

    if st.session_state.stage >= 2:
        st.write('Start contextualising :nerd_face:')  
        with st.status('Generating names and categories…'):

            # Combine the dataframes of the included receipts
            combined_df = write_receipt_value_dict_to_df(receipt_value_dict)

            # Use cached function to connect to LLM
            augmented_df = prompt_llm_for_responses(combined_df)
            
            # Use cached function to generate df for database
            database_df = embed_data(augmented_df)
    
            st.write(augmented_df)
            has_llm_response = True

            


with tab_Context:
    st.subheader("Contextualized Receipts")
    if st.session_state.stage >= 2:
        # Show result of data augmentation
        st.dataframe(augmented_df)

        # User action to write augmented data to database
        button_store = st.button('Submit', type='primary', on_click=set_state, args=[3])

        if st.session_state.stage >= 3:
            with st.spinner('Writing to database'):
                
                # Write to database
                db.insert_receipt_data(database_df)
                st.success('Receipts saved. You can return to the app.')

    else:

        # if no files were uploaded prompt the user to do that
        st.markdown('<p style="color:red;">Upload image-files on tab "Input" first before contextualized receipt output could be shown!</p>', unsafe_allow_html=True)