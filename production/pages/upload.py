import streamlit as st
import process_ocr as ocr

# streamlit run your_script.py [-- script args]


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

def decoded_data ():
    pass




tab1, tab2 = st.tabs(["Input", "Output"])

with tab1:
    col_input, col_img= st.columns(2)

with col_input:
    st.subheader("Input Receipts")
    #st.image("https://static.streamlit.io/examples/cat.jpg")
    uploaded_files = st.file_uploader("Wählen Sie ein oder mehrere Bilder aus", type=['jpg', 'png', 'bmp', 'pcx', 'tif'], accept_multiple_files=True)

    

with col_img:
    st.subheader("Files to upload")
    #st.image("https://static.streamlit.io/examples/dog.jpg")
    # function
    # Erstellen Sie eine Variable, um das ausgewählte Bild zu speichern
    selected_image = None

    if uploaded_files:
        # Erstellen Sie Spalten für jedes hochgeladene Bild
        columns = st.columns(len(uploaded_files))
        # Erstellen Sie eine Liste der Dateinamen
        file_names = [uploaded_file.name for uploaded_file in uploaded_files]

        # Erstellen Sie eine SelectBox zur Auswahl der Datei
        selected_file_name = st.selectbox("Wählen Sie eine Datei aus", file_names)

        # Finden Sie die ausgewählte Datei
        for uploaded_file in uploaded_files:
            if uploaded_file.name == selected_file_name:
                col_a, col_b, cl_c= st.columns([1, 4 ,1])
                with col_b:
                    image = Image.open(uploaded_file)
                    st.image(image, caption=uploaded_file.name, use_column_width=True)
        

with tab2:
    #st.subheader("You resulting data!")
    #st.image("https://static.streamlit.io/examples/owl.jpg", width=200)
 
    col_data, col_graphs= st.columns(2)

    with col_data:
        st.subheader("decoded products")
    # function
        decoded_data()

    with col_graphs:
        tab1, tab2 = st.tabs(["📈 Chart", "🗃 Data"])
        data = np.random.randn(10, 1)

        tab1.subheader("A tab with a chart")
        tab1.line_chart(data)

        tab2.subheader("A tab with the data")
        tab2.write(data)