'''
Streamlit Sub-Page to Home = main page
Handels the image-file upload and preview, calls receipt-boxing and ocr-function
returns a dataframe with the product name, prices and filenames of the receipts to the database
'''


import streamlit as st
import process_ocr as ocr
import make_boxes as mabo



from altair import DerivedStream
import streamlit as st
import pandas as pd
import numpy as np
import time
from io import StringIO
from PIL import Image, ImageDraw

st.title('Upload')


#def on_button_click():
 #   st.write('Der Button wurde gedrückt!')

#button = st.button('Drück mich', on_click=on_button_click)

#def decoded_data ():
 #   pass



# make 2 tabs
tab_Input, tab_Output = st.tabs(["Input", "Output"])

with tab_Input:
    # make 2 columns on tab "Input"
    col_load_files, col_img= st.columns(2)

# On column "Input":
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
    # create a variable to save the selected image
   # selected_image = None

    if uploaded_files:
        # create a Selectbox for the image to be shown
        selected_file_name = st.selectbox("Select an image of a receipt to be shown",\
                                              file_names, key='preview')
    
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
    # predefine the file selection list to avoid an error
    selected_files_ocr = []

    if not uploaded_files:
        # if no files were uploaded prompt the user to do that
        st.markdown('<p style="color:red;">Upload image-files on tab "Input" first before receipt output could be shown!</p>', unsafe_allow_html=True)
    else:  
        # create a Selectbox for the image to be shown
        selected_files_ocr = st.multiselect("Select one ore more receipt to be shown", \
                                        ["all"]+file_names, key='ocr_output')
        # check if "all" was selected or there was no selection
        if "all" in selected_files_ocr or not selected_files_ocr:
            # then take alle filenames (without "all")
            selected_files_ocr = file_names
        else:
            # remove double entries
            selected_files_ocr = list(set(selected_files_ocr))
        st.text(selected_files_ocr)

    # Show the recognized products and the preview only if files are selected
    if selected_files_ocr:
         # make 2 columns on tab "Output"
        col_ocr_data, col_ocr_image = st.columns(2)

        # On column "ocr_data" = "recognized products on the receipt:"
        with col_ocr_data:
            st.subheader("recognized products on the receipt:")
            # find the selected image-file-NAMES
            for file_ocr in selected_files_ocr:
                # find the selected image-FILE
                for uploaded_file in uploaded_files: # look at every file
                    # check if the iterated FILE matchs the selected file-NAME
                    if uploaded_file.name == file_ocr:
                        # open the image 
                        image = Image.open(uploaded_file)
                        # give the image to the function to make ocr and return products
                        #df_receipt = ocr.process_receipt(image)
                        st.image(image, caption=uploaded_file.name, use_column_width=True)
        # function
        #decoded_data()
                            

        # On column "ocr_image" = "preview of the products on the receipt:"
        with col_ocr_image:
            st.subheader("preview of the products on the receipt:")
            # find the selected image-file-NAMES
            for file_ocr in selected_files_ocr:
                    # find the selected image-FILE
                    for uploaded_file in uploaded_files: # look at every file
                        # check if the iterated FILE matchs the selected file-NAME
                        if uploaded_file.name == file_ocr:
                            # set the size of the image relativ to column width
                            col_a, col_b, cl_c= st.columns([1, 8 ,1])
                            with col_b:
                                # open the image
                                image = Image.open(uploaded_file)
                                # give the image to the function to make boxes
                                image_boxed = mabo.render_doc_text(image)
                                # show the image with boxes
                                st.image(image_boxed, caption=uploaded_file.name, use_column_width=True)

        