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

### Cached Functions:

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



st.title('Receipt upload')

        



# Create 2 tabs
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
                                          accept_multiple_files=True, )
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
        receipt_value_dict =create_receipt_value_dict(uploaded_files)
    #st.write(receipt_value_dict)

    # Predefine the file selection list to avoid an error
    selected_files_output = []
    button = st.button('Accept changes', key='top', type='primary')
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
    liste_df = []
   


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
        
        #print([value[2] for value in receipt_value_dict.values()])
        # Rember: receipt_value_dict[uploaded_file.name] = [df_sorted, image_boxed, True]
        # Write the dataframes of the receipt into the list of dataframes, if it was included
        for uploaded_file_name in receipt_value_dict: # type: ignore
            # if the receipt was included
            if receipt_value_dict[uploaded_file_name][2]:
                # Extract the dataframe in the dictionary 
                df = receipt_value_dict[uploaded_file_name][0] 
                # Write the dataframe of this receipt into the list of receipts
                liste_df.append(df)  

    # If receipts are available and at least one was selected
    if len(liste_df) > 0:
        # combine all dataframe in the list into a combined dataframe
        combined_df = pd.concat(liste_df, ignore_index=True)      
        #st.dataframe(combined_df, height=(combined_df.shape[0]*37+21))    

        # submit button
        button = st.button('Accept changes', key='bottom', type='primary')

    @st.cache_data
    def write_response_to_df(df=None):
        if df == None:          
            df = None       #TODO: Check if this code is nonsense
        else:
            df = pd.DataFrame(response_list) #TODO: where comes responselist into the function?
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
    if not uploaded_files:
        # if no files were uploaded prompt the user to do that
        st.markdown('<p style="color:red;">Upload image-files on tab "Input" first before contextualized receipt output could be shown!</p>', unsafe_allow_html=True)
    else:
        if response_df is not None:
            st.table(response_df)
        st.button('Submit', type='primary')
        